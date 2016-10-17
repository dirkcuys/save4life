from __future__ import unicode_literals

from django.db import models
from django.db.models import Sum
from django.db.models import Q, F

# Create your models here.

class UssdUser(models.Model):
    msisdn = models.CharField(max_length=12, primary_key=True) #TODO validate msisdn
    network = models.CharField(max_length=32) #TODO restrict to enum
    name = models.CharField(max_length=128)
    goal_item = models.CharField(max_length=128)
    goal_amount = models.IntegerField(null=True, blank=True)
    recurring_amount = models.IntegerField(null=True, blank=True)
    pin = models.CharField(max_length=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        # Don't include PIN 
        return {
            'msisdn': self.msisdn,
            'name': self.name,
            'goal_item': self.goal_item,
            'goal_amount': self.goal_amount,
            'recurring_amount': self.recurring_amount,
            'balance': self.balance(),
            'pin_set': True if self.pin else False
        }

    def registration_complete(self):
        return all([
            self.name <> '',
            self.goal_item <> '',
            self.goal_amount > 0
        ])

    def balance(self):
        return self.transaction_set\
                .filter(Q(action=Transaction.SAVING) | Q(action=Transaction.WITHDRAWAL))\
                .aggregate(Sum('amount'))\
                .get('amount__sum', 0) or 0

    def __unicode__(self):
        return u"UssdUser <{0}>".format(self.name)


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
    import string, random
    code = "".join([random.choice(string.digits) for i in range(16)])
    while Voucher.objects.filter(code=code).count() > 0:
        code = "".join([random.choice(string.digits) for i in range(16)])
    return Voucher.objects.create(code=code, amount=amount, distributor=distributor)



class Transaction(models.Model):
    SAVING = 'saving'
    WITHDRAWAL = 'withdrawal'
    AIRTIME = 'airtime'
    ACTION_TYPES = [
        (SAVING, SAVING),
        (WITHDRAWAL, WITHDRAWAL),
        (AIRTIME, AIRTIME),
    ]

    user = models.ForeignKey(UssdUser)
    action = models.CharField(max_length=12, choices=ACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    amount = models.IntegerField()
    reference_code = models.CharField(max_length=32)
    voucher = models.ForeignKey(Voucher, null=True, blank=True)


    def __unicode__(self):
        return u'Transaction <{0}: R{1}>'.format(self.action, self.amount)


class Quiz(models.Model):
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

    #TODO set user and question as unique together
