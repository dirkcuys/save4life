from __future__ import unicode_literals

from django.db import models
from django.db.models import Sum
from django.db.models import F
from django.db.models import Count

from datetime import datetime, timedelta


class UssdUser(models.Model):
    msisdn = models.CharField(max_length=12, primary_key=True)  # TODO validate msisdn
    network = models.CharField(max_length=32)  # TODO restrict to enum
    name = models.CharField(max_length=128)
    goal_item = models.CharField(max_length=128)
    goal_amount = models.IntegerField(null=True, blank=True)
    recurring_amount = models.IntegerField(null=True, blank=True)
    pin = models.CharField(max_length=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __repr__(self):
        return u"<UssdUser {0}>".format(self.msisdn)

    def __unicode__(self):
        return self.msisdn

    def to_dict(self):
        # Don't include PIN
        return {
            'msisdn': self.msisdn,
            'name': self.name,
            'goal_item': self.goal_item,
            'goal_amount': self.goal_amount,
            'recurring_amount': self.recurring_amount,
            'balance': self.balance(),
            'pin_set': True if self.pin else False,
            'streak': self.current_streak()
        }

    def registration_complete(self):
        """ return True if registration is complete """
        return all([
            self.name != '',
            self.goal_item != '',
            self.goal_amount > 0
        ])

    def balance(self):
        return self.transaction_set\
            .exclude(action=Transaction.AIRTIME)\
            .aggregate(Sum('amount'))\
            .get('amount__sum', 0)\
            or 0


    def streak(self):
        """ number of weeks consecutively saved"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=today.weekday()+7)
        savings = self.transaction_set.filter(
            action=Transaction.SAVING,
            amount__gt=0
        ).values('created_at').order_by('-created_at')
        weeks = 0  # Number of consecutive weeks saved
        while True:
            start = week_start - timedelta(days=weeks*7)
            end = start + timedelta(days=7)
            # make sure the user saved during the week
            if not savings.filter(created_at__gt=start, created_at__lte=end).exists():
                break
            # check for withdrawals during the week
            withdrawals = self.transaction_set.filter(created_at__gt=start).\
                filter(created_at__lte=end).\
                filter(action=Transaction.WITHDRAWAL)
            if withdrawals.exists():
                break
            weeks += 1
        return weeks


    def current_streak(self):
        """ counts this week if user saved this week """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=today.weekday())
        savings = self.transaction_set.filter(
            action=Transaction.SAVING,
            amount__gt=0,
            created_at__gt=week_start
        )
        withdrawals = self.transaction_set.filter(
            action=Transaction.WITHDRAWAL,
            created_at__gt=week_start
        )
        if withdrawals.exists():
            return 0
        elif savings.exists():
            return 1 + self.streak()
        else:
            return self.streak()



class Voucher(models.Model):
    code = models.CharField(max_length=16, unique=True)
    amount = models.IntegerField()
    redeemed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    distributor = models.CharField(max_length=128)
    redeemed_by = models.ForeignKey(UssdUser, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'Voucher <R{0}>'.format(self.amount)


def generate_voucher(amount, distributor):
    import string
    import random
    def gen_code():
        start = random.choice(['1','2','3','4','5','6','7','8','9'])
        return "".join([start] + [random.choice(string.digits) for i in range(15)])
    code = gen_code()
    while Voucher.objects.filter(code=code).count() > 0:
        code = gen_code()
    return Voucher.objects.create(code=code, amount=amount, distributor=distributor)


class Transaction(models.Model):
    SAVING = 'saving'
    WITHDRAWAL = 'withdrawal'
    AIRTIME = 'airtime'
    REWARD = 'rewards'
    REGISTRATION_BONUS = 'registration bonus'
    QUIZ_PRIZE = 'quiz_prize'
    ACTION_TYPES = [
        (SAVING, SAVING),
        (WITHDRAWAL, WITHDRAWAL),
        (AIRTIME, AIRTIME),
        (REWARD, REWARD),
        (REGISTRATION_BONUS, REGISTRATION_BONUS),
        (QUIZ_PRIZE, QUIZ_PRIZE)
    ]

    user = models.ForeignKey(UssdUser)
    action = models.CharField(max_length=32, choices=ACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    amount = models.IntegerField()
    reference_code = models.CharField(max_length=32)
    voucher = models.ForeignKey(Voucher, null=True, blank=True)

    def __unicode__(self):
        return u'Transaction <{0}: R{1}>'.format(self.action, self.amount)


class Quiz(models.Model):
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    publish_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    def to_dict(self):
        data = {
            'quiz_id': self.pk,
            'questions': [q.to_dict() for q in self.question_set.all().order_by('id')]
        }
        return data

    def mark_quiz(self, user):
        complete = Answer.objects.filter(user=user, question__quiz=self).count()
        correct = Answer.objects.filter(user=user, question__quiz=self, user_response=F('question__solution')).count()
        return (correct, complete)

    def total_responses(self):
        completed_qs = Answer.objects\
            .filter(question__quiz=self)\
            .values('user')\
            .annotate(completed_questions=Count('pk'))\
            .filter(completed_questions=self.question_set.count())
        return completed_qs.count()


    class Meta:
        verbose_name_plural = "quizzes"


class Question(models.Model):
    quiz = models.ForeignKey(Quiz)
    question = models.CharField(max_length=128)
    options = models.CharField(max_length=128)
    reinforce_text = models.CharField(max_length=128)
    solution = models.IntegerField()

    def to_dict(self):
        data = {
            'question': self.question,
            'options': self.options.split(',')
        }
        return data

    def answer_text(self):
        return self.options.split(',')[self.solution]


class Answer(models.Model):
    question = models.ForeignKey(Question)
    user = models.ForeignKey(UssdUser)
    created_at = models.DateTimeField(auto_now_add=True)
    user_response = models.IntegerField()

    def response_text(self):
        return self.question.options.split(',')[self.user_response]

    # TODO set user and question as unique together


class Message(models.Model):
    to = models.CharField(max_length=1024)  # Store comma seperated list of msisdns
    body = models.CharField(max_length=160)
    send_at = models.DateTimeField()
    sent_at = models.DateTimeField(blank=True, null=True)
