from django.test import TestCase
from django.test import Client
from django.utils import timezone
from django.contrib.auth.models import User

from ussd.models import Transaction
from ussd.models import Quiz
from ussd.models import Question
from ussd.models import Answer
from ussd.models import UssdUser
from ussd.models import Message
from ussd.transactions import award_joining_bonus

from mock import patch
from freezegun import freeze_time

from datetime import datetime

# Create your tests here.
class TestQuizPrize(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user('admin', 'admin@test.com', 'password')
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()

        self.user = UssdUser.objects.create(
            msisdn='27831112222',
            name=u'Spongebob',
            goal_item=u'Airtime',
            goal_amount=50
        )

        # create a quiz
        self.quiz = Quiz.objects.create(
            publish_at=datetime(2016,10,31),
            ends_at=datetime(2016,11,6)
        )

        self.questions = [
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

        Answer.objects.create(question=self.questions[0], user=self.user, user_response=0)
        Answer.objects.create(question=self.questions[1], user=self.user, user_response=0)
        Answer.objects.create(question=self.questions[2], user=self.user, user_response=0)
        Answer.objects.create(question=self.questions[3], user=self.user, user_response=0)
        award_joining_bonus(self.user)


    def test_award_quiz_prize(self):
        c = Client()
        c.login(username='admin', password='password')
        data = {
            'sms_text': 'Congratulations on winning the quiz this week'
        }
        balance = self.user.balance()
        resp = c.post('/admin/ussd/quiz/1/award/{}/'.format(self.user.msisdn), data=data)
        self.assertRedirects(resp, '/admin/ussd/quiz/1/results/')
        self.assertEquals(Transaction.objects.filter(user=self.user, action=Transaction.QUIZ_PRIZE).count(), 1)
        self.assertEquals(Transaction.objects.filter(user=self.user, action=Transaction.QUIZ_PRIZE).first().amount, balance)
        self.assertEquals(Message.objects.all().count(), 1)
        self.assertEquals(Message.objects.first().body, data['sms_text'])

