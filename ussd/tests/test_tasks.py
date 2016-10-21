from django.test import TestCase
from django.utils import timezone

from ussd.models import Message
from ussd.tasks import send_messages, send_junebug_sms

from mock import patch
from freezegun import freeze_time

from datetime import datetime

# Create your tests here.
class TestTasks(TestCase):

    def setUp(self):
        pass

    @patch('ussd.tasks.send_junebug_sms')
    def test_send_messages(self, send_junebug_sms):
        Message.objects.create(to='27731231234', body='Test', send_at=datetime(2016, 6, 1, 12, 0))
        with freeze_time('2016-06-01 11:59') as moment:
            send_messages()
            self.assertFalse(send_junebug_sms.called)

        with freeze_time('2016-06-01 12:00') as moment:
            send_messages()
            self.assertTrue(send_junebug_sms.called)


    @patch('ussd.tasks.send_junebug_sms')
    def test_dont_resend_messages(self, send_junebug_sms):
        Message.objects.create(to='27731231234', body='Test', send_at=datetime(2016, 6, 1, 12, 0), sent_at=datetime(2016, 6, 1, 12, 1))
        with freeze_time('2016-06-01 12:02') as moment:
            send_messages()
            self.assertFalse(send_junebug_sms.called)


    @patch('ussd.tasks.requests')
    def test_send_junebug_sms(self, requests):
        requests.post.return_value.status_code = 200
        send_junebug_sms('27731231234', 'This is a test message')


    @patch('ussd.tasks.requests')
    def test_send_junebug_sms_fail(self, requests):
        with self.assertRaises(Exception):
            requests.post.return_value.status_code = 404
            send_junebug_sms('27731231234', 'This is a test message')
