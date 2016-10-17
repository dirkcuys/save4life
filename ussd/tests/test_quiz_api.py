from django.test import TestCase
from django.test import Client
from django.utils import timezone

from ussd.models import Voucher, UssdUser
from ussd.models import Quiz, Question, Answer

import json
from mock import patch
from datetime import timedelta


class TestUssdQuizApi(TestCase):

    def setUp(self):
        self.user = UssdUser.objects.create(
            msisdn='27831112222',
            name=u'Spongebob',
            goal_item=u'Airtime',
            goal_amount=50
        )
        self.quiz = Quiz.objects.create(ends_at=timezone.now() + timedelta(days=2))
        self.questions = [
            Question.objects.create(
                    quiz=self.quiz, question='Q1', options='1,2,3', solution='0',
                    reinforce_text='Q1 correct'),
            Question.objects.create(
                    quiz=self.quiz, question='Q2', options='1,2,3', solution='1',
                    reinforce_text='Q2 correct'),
            Question.objects.create(
                    quiz=self.quiz, question='Q3', options='1,2,3', solution='2',
                    reinforce_text='blah'),
            Question.objects.create(
                    quiz=self.quiz, question='Q4', options='1,2,3', solution='0',
                    reinforce_text='blah')
        ]


    def test_get_active_quiz(self):
        c = Client()
        resp = c.get('/ussd/quiz/?msisdn=27831112222')
        self.assertEquals(resp.json().get('quiz_id'), self.quiz.id)
        self.assertEquals(resp.json().get('user_progress'), 0)
        self.assertEquals(resp.json().get('questions')[0], self.questions[0].to_dict())
        self.assertEquals(resp.json().get('questions')[0].get('question'), 'Q1')
        self.assertEquals(resp.json().get('questions')[1], self.questions[1].to_dict())
        self.assertEquals(resp.json().get('questions')[2], self.questions[2].to_dict())
        self.assertEquals(resp.json().get('questions')[3], self.questions[3].to_dict())
        self.assertEquals(resp.json().get('questions')[3].get('question'), 'Q4')


    def test_sumbit_correct_answer(self):
        c = Client()
        data = {
            'msisdn': '27831112222',
            'answer': 0
        }
        expected_response = {
            u'reinforce_text': u'Q1 correct',
            u'correct': True,
            u'answer_text': '1'
        }
        resp = c.post('/ussd/quiz/1/question/0/', data=json.dumps(data),
                content_type='application/json')
        self.assertEquals(resp.json(), expected_response)


    def test_submit_wrong_answer(self):
        c = Client()
        data = {
            'msisdn': '27831112222',
            'answer': 0
        }
        expected_response = {
            u'reinforce_text': u'Q2 correct',
            u'correct': False,
            u'answer_text': '2'
        }
        resp = c.post('/ussd/quiz/1/question/1/', data=json.dumps(data),
                content_type='application/json')
        self.assertEquals(resp.json(), expected_response)
