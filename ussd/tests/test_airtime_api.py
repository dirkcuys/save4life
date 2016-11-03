from django.test import TestCase
from django.test import Client
from django.utils import timezone

from ussd.models import Voucher, UssdUser, Transaction
from ussd.airtime_api import pinless_recharge
from ussd.airtime_api import InsufficientBalance
from ussd.tasks import issue_airtime

import json
from mock import patch, Mock, sentinel, PropertyMock, MagicMock

# Create your tests here.
class TestAirtimeApi(TestCase):

    def setUp(self):
        pass


    def test_issue_airtime(self):
        c = Client()
        # create user
        user = UssdUser.objects.create(msisdn='27831112222', name=u'Spongebob', goal_item=u'Airtime', goal_amount=50)
        # create a voucher
        voucher = Voucher.objects.create(code='1234567890123456', amount=100)

        # redeem voucher
        data = {
            "msisdn": "27831112222",
            "voucher_code": "1234567890123456",
            "savings_amount": 20 
        }
        with patch('ussd.transactions.issue_airtime.delay') as issue_airtime_delay:
            resp = c.post('/ussd/voucher/redeem/', data=json.dumps(data), 
                    content_type='application/json')
            self.assertTrue(issue_airtime_delay.called)
            self.assertEqual(resp.json().get('status'), 'success') 

        voucher.refresh_from_db()
        self.assertEquals(Transaction.objects.filter(voucher=voucher).count(), 1)

        # make sure we don't create a transaction if pinless_recharge fails 
        with patch('ussd.tasks.pinless_recharge') as pinless_recharge:
            pinless_recharge.side_effect = Exception('error')
            issue_airtime(voucher)
            self.assertTrue(pinless_recharge.called)
            # TODO insert test condition once we do something about failed recharges

        self.assertEquals(Transaction.objects.filter(voucher=voucher).count(), 1)

        #TODO test that we do something when the balance is too low 
        with patch('ussd.tasks.pinless_recharge') as pinless_recharge:
            pinless_recharge.side_effect = InsufficientBalance()
            issue_airtime(voucher)
            self.assertTrue(pinless_recharge.called)
            # TODO what should be tested when the balance was too low?

        self.assertEquals(Transaction.objects.filter(voucher=voucher).count(), 1)


        # call issue_airtime and test
        with patch('ussd.tasks.pinless_recharge') as pinless_recharge:
            pinless_recharge.return_value = True
            issue_airtime(voucher)
            self.assertTrue(pinless_recharge.called)
            
        self.assertEquals(Transaction.objects.filter(voucher=voucher).count(), 2)

        # test that user received savings
        resp = c.get('/ussd/user_registration/27831112222/')
        self.assertEquals(resp.json().get("balance"), 20)


    def test_pinless_recharge(self):
        authResponse = MagicMock()
        client_mock = MagicMock()
        client_mock.service.authenticate_cashier.return_value.token = '123'
        client_mock.service.authenticate_cashier.return_value.authenticate_cashierResult.Vendor.Balance.Available = 80
        client_mock.service.vend_airtime_pinless.return_value.vend_airtime_pinlessResult = True
        with patch('ussd.airtime_api.Client') as Client:
            Client.return_value = client_mock
            pinless_recharge('27831231234', 80)


    def test_pinless_recharge_low_balance(self):
        authResponse = MagicMock()
        client_mock = MagicMock()
        client_mock.service.authenticate_cashier.return_value.token = '123'
        client_mock.service.authenticate_cashier.return_value.authenticate_cashierResult.Vendor.Balance.Available = 79
        client_mock.service.vend_airtime_pinless.return_value.vend_airtime_pinlessResult = True
        with patch('ussd.airtime_api.Client') as Client:
            Client.return_value = client_mock
            self.assertRaises(InsufficientBalance, pinless_recharge, *['27831231234', 80])


