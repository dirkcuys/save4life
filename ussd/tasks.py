from django.conf import settings

from .airtime_api import pinless_recharge
from .models import Transaction

import requests
import json
from celery.decorators import task

import logging

logger = logging.getLogger(__name__)


@task(name="send_welcome_sms")
def send_welcome_sms(msisdn):
    url = settings.JUNEBUG_SMS_URL
    data = {
        "to": msisdn,
        "content": "Congratulations on registering for your Save4Life airtime wallet. Don't forget to dail back in to save and earn rewards. *120*XXXX# 20c/20sec T&Cs apply."
    }
    resp = requests.post(url, data=json.dumps(data))
    if resp.status_code != 200:
        logger.error('Could not send welcome SMS to {}'.format(msisdn))


@task(name="issue_airtime")
def issue_airtime(voucher):
    queryset = Transaction.objects.filter(voucher=voucher)
    if queryset.count() != 1:
        raise Exception('There should be 1 and only 1 transaction associated with the voucher')
        # TODO does this mean we should create a 0 savings transaction when the user choose to save nothing?

    savings_transaction = queryset.get()
    if savings_transaction.action != Transaction.SAVING:
        raise Exception('Transaction associated with the voucher is not a savings transaction')

    airtime_amount = voucher.amount - savings_transaction.amount

    try:
        ref = pinless_recharge(voucher.redeemed_by.msisdn, airtime_amount)
        Transaction.objects.create(
            user=voucher.redeemed_by,
            action=Transaction.AIRTIME,
            amount=airtime_amount,
            reference_code = ref,
            voucher = voucher
        )
    except Exception as e:
        logger.error('Could not issue R{0} airtime to {1}'.format(airtime_amount, voucher.redeemed_by.msisdn))
        # TODO should we retry this?
