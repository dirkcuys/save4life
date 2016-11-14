from django.test import TestCase
from django.test import Client
from django.utils import timezone
from django.utils.timezone import utc
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

from datetime import datetime, date, time

# Create your tests here.
class TestQuizAdmin(TestCase):

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
            publish_at=datetime(2016,10,31).replace(tzinfo=utc),
            ends_at=datetime(2016,11,6).replace(tzinfo=utc)
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


    def test_view_quiz_results(self):
        c = Client()
        c.login(username='admin', password='password')
        resp = c.get('/admin/ussd/quiz/1/results/')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(len(resp.context['user_results']), 1)
    
    def test_create_quiz(self):
        c = Client()
        c.login(username='admin', password='password')
        data = {
            'name': 'test_quiz',
            'description': 'blah',
            'publish_at_0': date(2016,1,1),
            'publish_at_1': time(12,0),
            'ends_at_0': date(2016,1,8),
            'ends_at_1': time(12,0),
            'reminder_text': 'This is a reminder. 1',
            "question_set-TOTAL_FORMS": 4,
            "question_set-INITIAL_FORMS": 0,
            "question_set-MIN_NUM_FORMS": 4,
            "question_set-MAX_NUM_FORMS": 4,
            'question_set-0-question': 'Q1',
            'question_set-0-options_0': 'O1',
            'question_set-0-options_1': 'O2',
            'question_set-0-options_2': 'O3',
            'question_set-0-options_3': 'O4',
            'question_set-0-reinforce_text': 'Reinforce',
            'question_set-0-solution': 0,
            'question_set-1-question': 'Q1',
            'question_set-1-options_0': 'O1',
            'question_set-1-options_1': 'O2',
            'question_set-1-options_2': 'O3',
            'question_set-1-options_3': 'O4',
            'question_set-1-reinforce_text': 'Reinforce',
            'question_set-1-solution': 0,
            'question_set-2-question': 'Q1',
            'question_set-2-options_0': 'O1',
            'question_set-2-options_1': 'O2',
            'question_set-2-options_2': 'O3',
            'question_set-2-options_3': 'O4',
            'question_set-2-reinforce_text': 'Reinforce',
            'question_set-2-solution': 0,
            'question_set-3-question': 'Q1',
            'question_set-3-options_0': 'O1',
            'question_set-3-options_1': 'O2',
            'question_set-3-options_2': 'O3',
            'question_set-3-options_3': 'O4',
            'question_set-3-reinforce_text': 'Reinforce',
            'question_set-3-solution': 0
        }
        resp = c.post('/admin/ussd/quiz/add/', data=data)
        self.assertRedirects(resp, '/admin/ussd/quiz/')
        self.assertEquals(Quiz.objects.all().count(), 2)
        self.assertEquals(Question.objects.all().count(), 8)
        self.assertEquals(Message.objects.all().count(), 1)
        self.assertEquals(Message.objects.first().body, 'This is a reminder. 1')


    def test_update_quiz(self):
        c = Client()
        c.login(username='admin', password='password')
        data = {
            'name': 'test_quiz',
            'description': 'blah',
            'publish_at_0': date(2016,1,1),
            'publish_at_1': time(12,0),
            'ends_at_0': date(2016,1,8),
            'ends_at_1': time(12,0),
            'reminder_text': 'This is a reminder. 1',
            "question_set-TOTAL_FORMS": 4,
            "question_set-INITIAL_FORMS": 0,
            "question_set-MIN_NUM_FORMS": 4,
            "question_set-MAX_NUM_FORMS": 4,
            'question_set-0-question': 'Q1',
            'question_set-0-options_0': 'O1',
            'question_set-0-options_1': 'O2',
            'question_set-0-options_2': 'O3',
            'question_set-0-options_3': 'O4',
            'question_set-0-reinforce_text': 'Reinforce',
            'question_set-0-solution': 0,
            'question_set-1-question': 'Q1',
            'question_set-1-options_0': 'O1',
            'question_set-1-options_1': 'O2',
            'question_set-1-options_2': 'O3',
            'question_set-1-options_3': 'O4',
            'question_set-1-reinforce_text': 'Reinforce',
            'question_set-1-solution': 0,
            'question_set-2-question': 'Q1',
            'question_set-2-options_0': 'O1',
            'question_set-2-options_1': 'O2',
            'question_set-2-options_2': 'O3',
            'question_set-2-options_3': 'O4',
            'question_set-2-reinforce_text': 'Reinforce',
            'question_set-2-solution': 0,
            'question_set-3-question': 'Q1',
            'question_set-3-options_0': 'O1',
            'question_set-3-options_1': 'O2',
            'question_set-3-options_2': 'O3',
            'question_set-3-options_3': 'O4',
            'question_set-3-reinforce_text': 'Reinforce',
            'question_set-3-solution': 0
        }
        resp = c.post('/admin/ussd/quiz/add/', data=data)
        quiz = Quiz.objects.last()
        reminder = Message.objects.first()
        self.assertRedirects(resp, '/admin/ussd/quiz/')
        self.assertEquals(Quiz.objects.all().count(), 2)
        self.assertEquals(quiz.reminder, reminder)
        self.assertEquals(reminder.body, 'This is a reminder. 1')
    
        data['reminder_text'] = 'this is the new reminder'
        resp = c.post('/admin/ussd/quiz/{0}/change/'.format(quiz.pk), data=data)
        quiz = Quiz.objects.last()
        reminder = Message.objects.first()
        self.assertRedirects(resp, '/admin/ussd/quiz/')
        self.assertEquals(Quiz.objects.all().count(), 2)
        self.assertEquals(quiz.reminder, reminder)
        self.assertEquals(reminder.body, 'this is the new reminder')

        reminder.sent_at = datetime(2016,1,1,12,5).replace(tzinfo=utc)
        reminder.save()
        data['reminder_text'] = 'this is a reminder too late'
        resp = c.post('/admin/ussd/quiz/{0}/change/'.format(quiz.pk), data=data, follow=True)
        quiz = Quiz.objects.last()
        reminder = Message.objects.first()
        self.assertRedirects(resp, '/admin/ussd/quiz/')
        self.assertEquals(Quiz.objects.all().count(), 2)
        self.assertEquals(quiz.reminder, reminder)
        self.assertEquals(reminder.body, 'this is the new reminder')
        self.assertEquals(str(list(resp.context['messages'])[0]), 'The reminder SMS has already been sent')
