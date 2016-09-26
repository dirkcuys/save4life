from django.test import TestCase
from django.test import Client

import json
from mock import patch

# Create your tests here.
class TestUssdApi(TestCase):
    def test_get_user_info(self):
        c = Client()
        resp = c.get('/ussd/user_registration/278312345678/')
        self.assertEquals(resp.json(), {"msisdn": u"278312345678"})


    def test_update_user_info(self):
        c = Client()
        data = {"name": u"Spongebob"}
        resp = c.post('/ussd/user_registration/278312345678/', data=json.dumps(data), content_type='application/json')
        for key in [u'msisdn', u'goal_item', u'goal_amount', u'name', u'balance']:
            self.assertIn(key, resp.json().keys())
        self.assertEquals(resp.json().get('name'), u'Spongebob')
        self.assertEquals(resp.json().get('msisdn'), u'278312345678')
        self.assertEquals(resp.json().get('goal_item'), u'')
        self.assertEquals(resp.json().get('goal_amount'), u'')
        self.assertEquals(resp.json().get('balance'), 0)


    def test_complete_registration(self):
        c = Client()
        data = {"name": u"Spongebob", "goal_item": u"Airtime", "goal_amount": 50 }

        # test welcome sms is sent first time registration is completed
        with patch('ussd.tasks.send_welcome_sms.delay') as send_welcome_sms:
            resp = c.post('/ussd/user_registration/278312345678/', data=json.dumps(data), content_type='application/json')
            self.assertTrue(send_welcome_sms.called)

        # test welcome sms isn't send when data is updated
        with patch('ussd.tasks.send_welcome_sms.delay') as send_welcome_sms:
            resp = c.post('/ussd/user_registration/278312345678/', data=json.dumps(data), content_type='application/json')
            self.assertTrue(send_welcome_sms.called)

