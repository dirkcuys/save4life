from django.conf import settings

from zeep import Client
import time
import logging

logger = logging.getLogger(__name__)


class InsufficientBalance(Exception):
    pass

class AirtimeApiError(Exception):
    pass

def pinless_recharge(transaction):
    amount = transaction.amount
    msisdn = transaction.user.msisdn
    api_ref = 'transaction-{0}'.format(transaction.pk)  # Reference for external API

    logger.info(u'pinless_recharge({0}, {1})'.format(msisdn, amount))
    client = Client(settings.AIRTIME_WSDL_URL)
    
    # authenticate client
    auth_resp = client.service.authenticate_cashier(
        terminalnumber=settings.AIRTIME_TERMINAL_NUMBER,
        msisdn=settings.AIRTIME_MSISDN,
        pin=settings.AIRTIME_PIN
    )

    # get auth token
    # TODO accessing properties can throw an exception ...
    token = auth_resp.token
    balance_available = auth_resp.authenticate_cashierResult.Vendor.Balance.Available

    # check balance - make sure we have enough money to pay voucher
    if balance_available < amount:
        raise InsufficientBalance('Account balance too low for airtime recharge')

    recharge_resp = client.service.vend_airtime_pinless(
        authtoken=token,
        reference=api_ref,
        sourcemsisdn=settings.AIRTIME_MSISDN,
        msisdn=msisdn,
        denomination=amount
    )

    if recharge_resp.vend_airtime_pinlessResult != True:
        logger.info(u'pinless_recharge({0}, {1}) failed')
        raise AirtimeApiError(u'Could not issue airtime: '.format(recharge_resp.error))
    
    # reference used by transaction 
    ref = "{0}-{1}-{2}".format(msisdn, amount, int(time.time()))
    transaction.reference_code = ref
    transaction.save()

    logger.info(u'pinless_recharge({0}, {1}) success. ref# {2}'.format(msisdn, amount, ref))
