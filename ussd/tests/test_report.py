from django.test import TestCase
from django.utils import timezone

from ussd.models import Voucher
from ussd.models import Transaction
from ussd.models import Quiz
from ussd.models import Question
from ussd.models import Answer
from ussd.models import UssdUser
from ussd.tasks import send_weekly_report

from mock import patch
from freezegun import freeze_time

from datetime import datetime

# Create your tests here.
class TestReport(TestCase):

    def setUp(self):
        self.user = UssdUser.objects.create(
            msisdn='27831112222',
            name=u'Spongebob',
            goal_item=u'Airtime',
            goal_amount=50
        )

        # create vouchers
        self.vouchers = [
            Voucher.objects.create(code='0000000000000001', amount=100),
            Voucher.objects.create(code='0000000000000002', amount=100),
            Voucher.objects.create(code='0000000000000003', amount=100),
            Voucher.objects.create(code='0000000000000004', amount=100),
            Voucher.objects.create(code='0000000000000005', amount=100),
            Voucher.objects.create(code='0000000000000006', amount=100),
            Voucher.objects.create(code='0000000000000007', amount=100),
            Voucher.objects.create(code='0000000000000008', amount=100),
            Voucher.objects.create(code='0000000000000009', amount=100)
        ]

        # create a quiz
        self.quiz = Quiz.objects.create(
            publish_at=datetime(2016,10,31),
            ends_at=datetime(2016,11,6)
        )

        self.question = [
            Question.objects.create(
                quiz=self.quiz,
                question='q1',
                options='a,b,c,d',
                reinforce_text='yeah, that was right',
                solution=0
            ),
            Question.objects.create(
                quiz=self.quiz,
                question='q2',
                options='a,b,c,d',
                reinforce_text='yeah, that was right',
                solution=0
            ),
            Question.objects.create(
                quiz=self.quiz,
                question='q3',
                options='a,b,c,d',
                reinforce_text='yeah, that was right',
                solution=0
            ),
            Question.objects.create(
                quiz=self.quiz,
                question='q4',
                options='a,b,c,d',
                reinforce_text='yeah, that was right',
                solution=0
            )
        ]


    def test_report_data(self):
        # TODO
        # Redeem some vouchers
        # Answer the quiz
        send_weekly_report()

