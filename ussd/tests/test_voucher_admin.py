from django.test import TestCase
from django.test import Client
from django.utils import timezone
from django.utils.timezone import utc
from django.contrib.auth.models import User

from ussd.models import UssdUser
from ussd.models import Voucher
from ussd.models import generate_voucher

from mock import patch
from freezegun import freeze_time

from datetime import datetime

# Create your tests here.
class TestVoucherAdmin(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user('admin', 'admin@test.com', 'password')
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()


    def test_add_vouchers(self):
        c = Client()
        c.login(username='admin', password='password')
        data = {
            'vouchers_10': 4,
            'vouchers_20': 7,
            'vouchers_50': 9,
            'distributor': 'test distributor'
        }
        resp = c.post('/admin/ussd/voucher/generate_vouchers/', data=data)
        self.assertEquals(Voucher.objects.all().count(), 20)
        self.assertEquals(Voucher.objects.filter(amount=10).count(), 4)
        self.assertEquals(Voucher.objects.filter(amount=20).count(), 7)
        self.assertEquals(Voucher.objects.filter(amount=50).count(), 9)


    def test_revoke_vouchers(self):
        v1 = generate_voucher(20, 'test dist')
        v2 = generate_voucher(50, 'test dist')
        v3 = generate_voucher(20, 'test dist')
        v4 = generate_voucher(50, 'test dist')
        v5 = generate_voucher(60, 'test dist')
        c = Client()
        c.login(username='admin', password='password')
        data = {
            'action': 'revoke_vouchers',
            'select_across': '0',
            'index': 0,
            '_selected_action': [str(v1.pk), str(v2.pk)]
        }
        self.assertEquals(Voucher.objects.filter(revoked_at__isnull=False).count(), 0)
        resp = c.post('/admin/ussd/voucher/', data=data)
        v1.refresh_from_db()
        v2.refresh_from_db()
        v3.refresh_from_db()
        v4.refresh_from_db()
        v5.refresh_from_db()
        self.assertEquals(Voucher.objects.filter(revoked_at__isnull=False).count(), 2)
        self.assertNotEquals(v1.revoked_at, None)
        self.assertNotEquals(v2.revoked_at, None)
        self.assertEquals(v3.revoked_at, None)
        self.assertEquals(v4.revoked_at, None)
        self.assertEquals(v5.revoked_at, None)

