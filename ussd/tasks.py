from django.conf import settings
from celery.decorators import task

from .airtime_api import pinless_recharge
from .models import Transaction, Message

import requests
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def send_junebug_sms(msisdn, content):
    url = settings.JUNEBUG_SMS_URL
    data = {
        "to": msisdn,
        "content": content
    }
    resp = requests.post(url, data=json.dumps(data))
    if resp.status_code != 200:
        raise Exception('Could not send SMS to {}'.format(msisdn))


@task(name="send_welcome_sms")
def send_welcome_sms(msisdn):
    msg = "Congratulations on registering for your Save4Life airtime wallet. Don't forget to dail back in to save and earn rewards. *120*XXXX# 20c/20sec T&Cs apply."
    try:
        send_junebug_sms(msisdn, msg)
    except Exception as e:
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


@task(name="withdraw_airtime")
def issue_airtime_withdrawal(transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id)
    if transaction.action != Transaction.WITHDRAWAL:
        raise Exception('Transaction passed to withdraw_airtime should be a WITHDRAWAL')
    if transaction.reference_code and Transaction.objects.filter(reference_code=transaction.reference_code):
        raise Exception('Airtime already issued for this withdrawal transaction')
    # TODO - we should make sure this transaction doesn't already have a airtime equivalent
    try:
        ref = pinless_recharge(transaction.user.msisdn, abs(transaction.amount))
        Transaction.objects.create(
            user=voucher.redeemed_by,
            action=Transaction.AIRTIME,
            amount=airtime_amount,
            reference_code = ref,
            voucher = voucher
        )
        transaction.reference_code = ref
        transaction.save()
    except Exception as e:
        logger.error('Could not issue R{0} airtime to {1}'.format(transaction.amount, transaction.user.msisdn))
        # TODO should we retry this?


@task(name="withdraw_airtime_backlog")
def withdraw_airtime_backlog():
    return
    # TODO - this could potentially issue airtime multiple times if
    # more than 1 task executes at the same time!

    # find withdrawals with unmatched airtime issue transactions
    unprocessed = Transaction.objects\
        .filter(action=Transaction.WITHDRAWAL)\
        .exclude(
            reference_code__in=Transaction.objects
            .filter(action=Transaction.AIRTIME).values('reference_code')
        )
    # issue airtime
    while unprocessed.count() > 0:
        withdrawal = unprocessed.first()
        ref = pinless_recharge(withdrawal.user.msisdn, abs(withdrawal.amount))
        Transaction.objects.create(
            user=voucher.redeemed_by,
            action=Transaction.AIRTIME,
            amount=airtime_amount,
            reference_code = ref,
            voucher = voucher
        )
        withdrawal.reference = ref
        withdrawal.save()


@task(name='send_messages')
def send_messages():
    messages = Message.objects.filter(send_at__lte=datetime.now(), sent_at__isnull=True)
    for msg in messages:
        try:
            send_junebug_sms(msg.to, msg.body)
            msg.sent_at = datetime.now()
            msg.save()
        except Exception as e:
            logger.error('could not send message!')

