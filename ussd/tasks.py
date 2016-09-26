from django.conf import settings
import logging

logger = logging.getLogger(__name__)

import requests
import json
from celery.decorators import task

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
