from django.test import TestCase
from django.test import Client
from django.utils import timezone

from ussd.models import Voucher, UssdUser, Transaction

import json
from mock import patch

# Create your tests here.
class TestUssdApi(TestCase):

    def setUp(self):
        pass

    def test_get_user_info(self):
        c = Client()
        resp = c.get('/ussd/user_registration/278312345678/')
        self.assertEquals(resp.json(), {"msisdn": u"278312345678"})


    def test_update_user_info(self):
        c = Client()
        data = {"name": u"Spongebob"}
        resp = c.post('/ussd/user_registration/278312345678/', data=json.dumps(data), content_type='application/json')
        for key in [u'msisdn', u'goal_item', u'goal_amount', u'name', u'balance']:
            self.assertIn(key, resp.json().keys())
        self.assertEquals(resp.json().get('name'), u'Spongebob')
        self.assertEquals(resp.json().get('msisdn'), u'278312345678')
        self.assertEquals(resp.json().get('goal_item'), u'')
        self.assertEquals(resp.json().get('goal_amount'), None)
        self.assertEquals(resp.json().get('recurring_amount'), None)
        self.assertEquals(resp.json().get('balance'), 0)
        self.assertFalse(resp.json().get('pin_set'))


    def test_complete_registration(self):
        c = Client()
        data = {"name": u"Spongebob", "goal_item": u"Airtime", "goal_amount": 50 }

        # test welcome sms is sent first time registration is completed
        with patch('ussd.tasks.send_welcome_sms.delay') as send_welcome_sms:
            resp = c.post('/ussd/user_registration/278312345679/', data=json.dumps(data), content_type='application/json')
            self.assertTrue(send_welcome_sms.called)

        # test welcome sms isn't send when data is updated
        with patch('ussd.tasks.send_welcome_sms.delay') as send_welcome_sms:
            resp = c.post('/ussd/user_registration/278312345679/', data=json.dumps(data), content_type='application/json')
            self.assertFalse(send_welcome_sms.called)

        # test that registration bonus was awarded
        self.assertEquals(resp.json().get('balance'), 5)


    def test_set_pin(self):
        c = Client()
        user = UssdUser.objects.create(msisdn='27831112222', name=u'Spongebob', goal_item=u'Airtime', goal_amount=50)
        resp = c.get('/ussd/user_registration/278312345678/')
        self.assertFalse(resp.json().get('pin_set'))

        data = {"pin": "1234"}
        resp = c.post('/ussd/user_registration/278312345679/', data=json.dumps(data), content_type='application/json')
        self.assertTrue(resp.json().get('pin_set'))


    def test_voucher_verify_without_user(self):
        c = Client()
        data = {"msisdn": "27831112222", "voucher_code": "1234567890123456" }
        resp = c.post('/ussd/voucher/verify/', data=json.dumps(data), content_type='application/json')
        self.assertEquals(resp.json().get('error_code'), 403)


    def test_voucher_verify(self):
        c = Client()
        user = UssdUser.objects.create(msisdn='27831112222', name=u'Spongebob', goal_item=u'Airtime', goal_amount=50)

        # Test non-existent voucher
        data = {"msisdn": "27831112222", "voucher_code": "1234567890123456" }
        resp = c.post('/ussd/voucher/verify/', data=json.dumps(data), content_type='application/json')
        self.assertEquals(resp.json().get('status'), 'invalid')

        # Test valid voucher
        voucher = Voucher.objects.create(code='1234567890123456', amount=100)
        data = {"msisdn": "27831112222", "voucher_code": "1234567890123456" }
        resp = c.post('/ussd/voucher/verify/', data=json.dumps(data), content_type='application/json')
        self.assertEquals(resp.json().get('status'), 'valid')
        self.assertEquals(resp.json().get('amount'), 100)

        voucher.redeemed_at = timezone.now()
        voucher.save()

        # Test redeemed voucher
        data = {"msisdn": "27831112222", "voucher_code": "1234567890123456" }
        resp = c.post('/ussd/voucher/verify/', data=json.dumps(data), content_type='application/json')
        self.assertEquals(resp.json().get('status'), 'used')


    def test_voucher_redeem(self):
        c = Client()

        # create user 
        user = UssdUser.objects.create(msisdn='27831112222', name=u'Spongebob', goal_item=u'Airtime', goal_amount=50)
                
        # create a voucher
        voucher = Voucher.objects.create(code='1234567890123456', amount=100)

        # redeem voucher
        data = {
            "msisdn": "27831112222",
            "voucher_code": "1234567890123456",
            "savings_amount": 10 
        }
        with patch('ussd.transactions.issue_airtime.delay') as issue_airtime:
            resp = c.post('/ussd/voucher/redeem/', data=json.dumps(data), 
                    content_type='application/json')
            self.assertEquals(resp.json().get('status'), 'success')
            self.assertTrue(issue_airtime.called)

        # test that we created 2 Transactions
        self.assertEquals(Transaction.objects.filter(voucher=voucher).count(), 2)
        self.assertEquals(Transaction.objects.filter(voucher=voucher).first().amount, 10)
        self.assertEquals(Transaction.objects.filter(voucher=voucher).last().amount, 90)

        # test that user received savings
        resp = c.get('/ussd/user_registration/27831112222/')
        self.assertEquals(resp.json().get("balance"), 10)

        # test that voucher is now invalid
        data = {"msisdn": "27831112222", "voucher_code": "1234567890123456" }
        resp = c.post('/ussd/voucher/verify/', data=json.dumps(data), content_type='application/json')
        self.assertEquals(resp.json().get('status'), 'used')

        # test that voucher redeemed by is set
        voucher.refresh_from_db()
        self.assertEquals(voucher.redeemed_by.msisdn, '27831112222')


    def test_voucher_save_whole_voucher(self):
        c = Client()
        # create user
        user = UssdUser.objects.create(msisdn='27831112222', name=u'Spongebob', goal_item=u'Airtime', goal_amount=50)
        # create a voucher
        voucher = Voucher.objects.create(code='1234567890123456', amount=100)

        # redeem voucher
        data = {
            "msisdn": "27831112222",
            "voucher_code": "1234567890123456",
            "savings_amount": 100 
        }
        with patch('ussd.transactions.issue_airtime.delay') as issue_airtime:
            resp = c.post('/ussd/voucher/redeem/', data=json.dumps(data), 
                    content_type='application/json')
            self.assertTrue(issue_airtime.called)

        # test that user received savings
        resp = c.get('/ussd/user_registration/27831112222/')
        self.assertEquals(resp.json().get("balance"), 100)


    def test_voucher_save_nothing(self):
        c = Client()
        # create user
        user = UssdUser.objects.create(msisdn='27831112222', name=u'Spongebob', goal_item=u'Airtime', goal_amount=50)
        # create a voucher
        voucher = Voucher.objects.create(code='1234567890123456', amount=100)

        # redeem voucher
        data = {
            "msisdn": "27831112222",
            "voucher_code": "1234567890123456",
            "savings_amount": 0 
        }
        with patch('ussd.transactions.issue_airtime.delay') as issue_airtime:
            resp = c.post('/ussd/voucher/redeem/', data=json.dumps(data), 
                    content_type='application/json')
            self.assertTrue(issue_airtime.called)

        # test that user received savings
        resp = c.get('/ussd/user_registration/27831112222/')
        self.assertEquals(resp.json().get("balance"), 0)


    def test_voucher_redeem_savings_amount_too_much(self):
        c = Client()
        # create user
        user = UssdUser.objects.create(msisdn='27831112222', name=u'Spongebob', goal_item=u'Airtime', goal_amount=50)
        # create a voucher
        voucher = Voucher.objects.create(code='1234567890123456', amount=100)

        # redeem voucher
        data = {
            "msisdn": "27831112222",
            "voucher_code": "1234567890123456",
            "savings_amount": 200 
        }
        with patch('ussd.transactions.issue_airtime.delay') as issue_airtime:
            resp = c.post('/ussd/voucher/redeem/', data=json.dumps(data), 
                    content_type='application/json')
            self.assertFalse(issue_airtime.called)
            self.assertEqual(resp.json().get('status'), 'invalid') 

        # test that user received savings
        resp = c.get('/ussd/user_registration/27831112222/')
        self.assertEquals(resp.json().get("balance"), 0)


    def test_voucher_redeem_with_negative_savings_amount(self):
        c = Client()
        # create user
        user = UssdUser.objects.create(msisdn='27831112222', name=u'Spongebob', goal_item=u'Airtime', goal_amount=50)
        # create a voucher
        voucher = Voucher.objects.create(code='1234567890123456', amount=100)

        # redeem voucher
        data = {
            "msisdn": "27831112222",
            "voucher_code": "1234567890123456",
            "savings_amount": -20 
        }
        with patch('ussd.transactions.issue_airtime.delay') as issue_airtime:
            resp = c.post('/ussd/voucher/redeem/', data=json.dumps(data), 
                    content_type='application/json')
            self.assertFalse(issue_airtime.called)
            self.assertEqual(resp.json().get('status'), 'invalid') 

        # test that user received savings
        resp = c.get('/ussd/user_registration/27831112222/')
        self.assertEquals(resp.json().get('balance'), 0)



