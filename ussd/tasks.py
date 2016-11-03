from django.conf import settings
from django.template.loader import render_to_string

from celery.decorators import task

from .airtime_api import pinless_recharge
from .airtime_api import InsufficientBalance
from .airtime_api import AirtimeApiError
from .models import Transaction, Message

import requests
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def send_junebug_sms(msisdn, content):
    # TODO - move this function
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
    # TODO use messages to send welcome SMS
    msg = "Congratulations on registering for your Save4Life airtime wallet. Don't forget to dail back in to save and earn rewards. *120*XXXX# 20c/20sec T&Cs apply."
    try:
        send_junebug_sms(msisdn, msg)
    except Exception as e:
        logger.error('Could not send welcome SMS to {}'.format(msisdn))


@task(name="issue_airtime")
def issue_airtime(transaction):
    try:
        pinless_recharge(transaction)
        context = {
            'transaction': transaction
        }
        message_text = render_to_string('ussd/airtime_issued.txt', context).strip('\n')
        Message.objects.create(
            to=transaction.user.msisdn,
            body=message_text,
            send_at=datetime.utcnow()
        )
    except InsufficientBalance as e:
        logger.error('Account balance not sufficient to issue airtime!')
        # TODO send a msg to administrator to manually inspect and retry?
    except AirtimeApiError as e:
        logger.error('Could not process airtime transaction. R{0} airtime to {1}'.format(transaction.amount, transaction.user.msisdn))
        # TODO send a msg to administrator to manually inspect and retry?


@task(name='send_messages')
def send_messages():
    messages = Message.objects.filter(
        send_at__lte=datetime.utcnow(),
        sent_at__isnull=True
    )
    for msg in messages:
        try:
            send_junebug_sms(msg.to, msg.body)
            msg.sent_at = datetime.utcnow()
            msg.save()
        except Exception as e:
            logger.error('could not send message!')
