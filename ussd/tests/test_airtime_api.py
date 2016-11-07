from django.test import TestCase
from django.test import Client

from ussd.models import Voucher, UssdUser, Transaction, Message
from ussd.tasks import issue_airtime
from ussd.airtime_api import pinless_recharge
from ussd.airtime_api import InsufficientBalance
from ussd.airtime_api import AirtimeApiError


import json
from mock import patch, MagicMock

# Create your tests here.
class TestAirtimeApi(TestCase):

    def setUp(self):
        self.user = UssdUser.objects.create(msisdn='27831112222', name=u'Spongebob', goal_item=u'Airtime', goal_amount=50)


    def test_issue_airtime(self):
        transaction = Transaction.objects.create(
            user=self.user,
            action=Transaction.SAVING,
            amount=20,
            reference_code='savings'
        )
        transaction = Transaction.objects.create(
            user=self.user,
            action=Transaction.AIRTIME,
            amount=80,
            reference_code=''
        )
        self.assertEquals(Message.objects.all().count(), 0)
        with patch('ussd.tasks.pinless_recharge') as pinless_recharge:
            issue_airtime(transaction)
            self.assertTrue(pinless_recharge.called)
        self.assertEquals(Message.objects.all().count(), 1)
        self.assertEquals(Message.objects.first().body, 'Hi Spongebob. We have credited your mobile with R80 airtime. Your savings balance is R20.')


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

