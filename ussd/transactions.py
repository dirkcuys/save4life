from .models import Transaction
from .tasks import issue_airtime

from datetime import datetime

class TransactionError(Exception):
    pass

def award_joining_bonus(user):
    transaction = Transaction.objects.create(
        user=user,
        action=Transaction.REGISTRATION_BONUS,
        amount=5,  # TODO store joining bonus somewhere
        reference_code='joining-bonus'
    )
    return transaction


def award_streak(user, weeks, amount):
    return Transaction.objects.create(
        user=user,
        action=Transaction.REWARD,
        amount=amount,
        reference_code='streak-{0}'.format(weeks)
    )


def award_quiz_prize(user, quiz):
    return Transaction.objects.create(
        user=user,
        action=Transaction.QUIZ_PRIZE,
        amount=user.balance(),  # TODO should this be limited to an upper amount?
        reference_code='quiz-{0}'.format(quiz.pk)
    )


def redeem_voucher(voucher, user, savings_amount):
    # make sure voucher wasn't already redeemed or revoked!!
    if voucher.redeemed_at or voucher.revoked_at:
        raise TransactionError("Voucher not valid")

    if savings_amount > voucher.amount or savings_amount < 0:
        raise TransactionError('Invalid savings amount')

    voucher.redeemed_at = datetime.utcnow()
    voucher.redeemed_by = user
    voucher.save()

    # Credit user balance with savings amount
    Transaction.objects.create(
        user=user,
        action=Transaction.SAVING,
        amount=savings_amount,
        reference_code='savings',
        voucher=voucher
    )

    # TODO - change this to create transaction that will be processes later
    # Credit airtime with remainder
    airtime_amount = voucher.amount - savings_amount
    airtime_transaction = Transaction.objects.create(
        user=user,
        action=Transaction.AIRTIME,
        amount=airtime_amount,
        reference_code ='',  # TODO
        voucher=voucher
    )
    issue_airtime.delay(airtime_transaction)


def withdraw_savings(user, amount):
    if not amount or amount < 5 or amount > user.balance():
        raise TransactionError('incorrect amount')

    # Stop user from withdrawing an amount that would result in 
    # positive balance less than 5
    resulting_balance = user.balance() - amount
    if 0 < resulting_balance < 5:
        raise TransactionError('resulting balance less than minimum payable amount')

    transaction = Transaction.objects.create(
        user=user,
        action=Transaction.WITHDRAWAL,
        amount=-amount,
        reference_code=''  # TODO
    )
    # TODO should we fire off async airtime operation or should we run 
    # a task that matches WITHDRAWAL transactions agains AIRTIME transactions?

    airtime_transaction = Transaction.objects.create(
        user=user,
        action=Transaction.AIRTIME,
        amount=amount,
        reference_code='' #TODO
    )
    issue_airtime.delay(airtime_transaction)
