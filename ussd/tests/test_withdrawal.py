from django.test import TestCase
from django.test import Client
from django.utils import timezone

from ussd.models import UssdUser, Transaction

import json
from mock import patch

# Create your tests here.
class TestWithdrawalApi(TestCase):

    def setUp(self):
        self.user = UssdUser.objects.create(
            msisdn='27831112222',
            name=u'Spongebob',
            goal_item=u'Airtime',
            goal_amount=50,
            pin='1234'
        )

        Transaction.objects.create(
            user=self.user,
            action=Transaction.REGISTRATION_BONUS,
            amount=5,
            reference_code='joining bonus'
        )

        Transaction.objects.create(
            user=self.user,
            action=Transaction.SAVING,
            amount=10,
            reference_code='saving'
        )


    def test_pin(self):
        c = Client()
        data = {
            "msisdn": "27831112222",
            "pin": "1234",
        }
        resp = c.post('/ussd/pin/verify/', data=json.dumps(data), content_type='application/json')
        self.assertEquals(resp.json().get('status'), u'valid')

        data['pin'] = '0000'
        resp = c.post('/ussd/pin/verify/', data=json.dumps(data), content_type='application/json')
        self.assertEquals(resp.json().get('status'), u'invalid')

        del data['pin']
        resp = c.post('/ussd/pin/verify/', data=json.dumps(data), content_type='application/json')
        self.assertEquals(resp.json().get('status'), u'invalid')

 
    def test_partial_withdrawal_max(self):
        c = Client()
        data = {
            "msisdn": "27831112222",
            "pin": "1234",
            "amount": 10
        }

        with patch('ussd.transactions.issue_airtime_withdrawal.delay') as withdraw_airtime:
            resp = c.post('/ussd/withdraw/', data=json.dumps(data), content_type='application/json')
            self.assertTrue(withdraw_airtime.called)
        self.assertEquals(resp.json().get('status'), u'success')
        self.assertEquals(self.user.balance(), 5)


    def test_partial_withdrawal_min(self):
        c = Client()
        data = {
            "msisdn": "27831112222",
            "pin": "1234",
            "amount": 5
        }
        with patch('ussd.transactions.issue_airtime_withdrawal.delay') as withdraw_airtime:
            resp = c.post('/ussd/withdraw/', data=json.dumps(data), content_type='application/json')
            self.assertTrue(withdraw_airtime.called)
        self.assertEquals(resp.json().get('status'), u'success')
        self.assertEquals(self.user.balance(), 10)


    def test_small_withdrawal_fail(self):
        c = Client()
        data = {
            "msisdn": "27831112222",
            "pin": "1234",
            "amount": 4
        }
        with patch('ussd.transactions.issue_airtime_withdrawal.delay') as withdraw_airtime:
            resp = c.post('/ussd/withdraw/', data=json.dumps(data), content_type='application/json')
            self.assertFalse(withdraw_airtime.called)
        self.assertEquals(resp.json().get('status'), u'error')
        self.assertEquals(self.user.balance(), 15)


    def test_partial_withdrawal_fail(self):
        c = Client()
        data = {
            "msisdn": "27831112222",
            "pin": "1234",
            "amount": 11
        }
        with patch('ussd.transactions.issue_airtime_withdrawal.delay') as withdraw_airtime:
            resp = c.post('/ussd/withdraw/', data=json.dumps(data), content_type='application/json')
            self.assertFalse(withdraw_airtime.called)
        self.assertEquals(resp.json().get('status'), u'error')
        self.assertEquals(self.user.balance(), 15)


    def test_total_withdrawal(self):
        c = Client()
        data = {
            "msisdn": "27831112222",
            "pin": "1234",
            "amount": 15
        }
        with patch('ussd.transactions.issue_airtime_withdrawal.delay') as withdraw_airtime:
            resp = c.post('/ussd/withdraw/', data=json.dumps(data), content_type='application/json')
            self.assertTrue(withdraw_airtime.called)
        self.assertEquals(resp.json().get('status'), u'success')
        self.assertEquals(self.user.balance(), 0)

