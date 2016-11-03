from django.test import TestCase
from django.test import Client
from django.utils import timezone

from ussd.models import Voucher, UssdUser, Transaction
from ussd.airtime_api import pinless_recharge
from ussd.airtime_api import InsufficientBalance
from ussd.airtime_api import AirtimeApiError
from ussd.tasks import issue_airtime


import json
from mock import patch, MagicMock

# Create your tests here.
class TestAirtimeApi(TestCase):

    def setUp(self):
        self.user = UssdUser.objects.create(msisdn='27831112222', name=u'Spongebob', goal_item=u'Airtime', goal_amount=50)


    def test_issue_airtime(self):
        c = Client()
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
        self.assertEquals(Transaction.objects.filter(voucher=voucher).count(), 2)
        airtime_transaction = Transaction.objects.filter(voucher=voucher).last()
        self.assertEquals(airtime_transaction.action, Transaction.AIRTIME)


    def test_pinless_recharge_fail(self):
        client_mock = MagicMock()
        client_mock.service.authenticate_cashier.return_value.token = '123'
        client_mock.service.authenticate_cashier.return_value.authenticate_cashierResult.Vendor.Balance.Available = 80
        client_mock.service.vend_airtime_pinless.return_value.vend_airtime_pinlessResult = False
        transaction = Transaction.objects.create(
            user=self.user,
            action=Transaction.AIRTIME,
            amount=80,
            reference_code=''
        )
        with patch('ussd.airtime_api.Client') as Client:
            Client.return_value = client_mock
            self.assertRaises(AirtimeApiError, pinless_recharge, *[transaction])

        transaction.refresh_from_db()
        self.assertEquals(transaction.reference_code, '')


    def test_pinless_recharge_insufficient_balance(self):
        client_mock = MagicMock()
        client_mock.service.authenticate_cashier.return_value.token = '123'
        client_mock.service.authenticate_cashier.return_value.authenticate_cashierResult.Vendor.Balance.Available = 79
        client_mock.service.vend_airtime_pinless.return_value.vend_airtime_pinlessResult = True
        transaction = Transaction.objects.create(
            user=self.user,
            action=Transaction.AIRTIME,
            amount=80,
            reference_code=''
        )
        with patch('ussd.airtime_api.Client') as Client:
            Client.return_value = client_mock
            self.assertRaises(InsufficientBalance, pinless_recharge, *[transaction])
   
        transaction.refresh_from_db()
        self.assertEquals(transaction.reference_code, '')

    
    def test_pinless_recharge(self):
        authResponse = MagicMock()
        client_mock = MagicMock()
        client_mock.service.authenticate_cashier.return_value.token = '123'
        client_mock.service.authenticate_cashier.return_value.authenticate_cashierResult.Vendor.Balance.Available = 80
        client_mock.service.vend_airtime_pinless.return_value.vend_airtime_pinlessResult = True
        transaction = Transaction.objects.create(
            user=self.user,
            action=Transaction.AIRTIME,
            amount=80,
            reference_code=''
        )
        with patch('ussd.airtime_api.Client') as Client:
            Client.return_value = client_mock
            pinless_recharge(transaction)

        transaction.refresh_from_db()
        self.assertNotEquals(transaction.reference_code, '')

