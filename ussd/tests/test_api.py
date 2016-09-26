from django.test import TestCase
from django.test import Client

# Create your tests here.
class TestUssdApi(TestCase):
    def test_get_user_info(self):
        c = Client()
        resp = c.get('/ussd/user_registration/278312345678/')
        self.assertEquals(resp.json(), {"msisdn": u"278312345678"})
