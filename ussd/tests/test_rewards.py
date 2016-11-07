from django.test import TestCase
from django.test import Client
from django.utils import timezone

from ussd.models import Voucher, UssdUser, Transaction, Message
from ussd.rewards import calculate_rewards

from datetime import datetime
import json

from mock import patch
from freezegun import freeze_time

# Create your tests here.
class TestUssdApi(TestCase):

    def setUp(self):
        self.user = UssdUser.objects.create(
            msisdn='27831112222',
            name=u'Spongebob',
            goal_item=u'Airtime',
            goal_amount=50
        )
        # create a voucher
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


    def test_week_1_no_streak(self):
        # redeem a voucher
        Transaction.objects.create(
            user=self.user,
            action=Transaction.SAVING,
            amount=10,
            reference_code='saving',
            voucher=self.vouchers[0]
        )
        self.assertEquals(Transaction.objects.count(), 1)
        # make sure no streak is awarded
        calculate_rewards()
        self.assertEquals(Transaction.objects.count(), 1)
        self.assertEquals(self.user.balance(), 10)


    def test_week_2_streak_1(self):
        # redeem a voucher
        with freeze_time(datetime(2015, 12, 28, 10)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[0]
            )
        with freeze_time(datetime(2016, 1, 10, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[1]
            )

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 0)
        # make sure 1 week streak is awarded once and only once
        with freeze_time(datetime(2016, 1, 11, 15)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 1)
        self.assertEquals(self.user.balance(), 25)
        self.assertEquals(Message.objects.count(), 1)

        award_transaction = Transaction.objects.last()
        self.assertEquals(award_transaction.user, self.user)
        self.assertEquals(award_transaction.action, Transaction.REWARD)
        self.assertEquals(award_transaction.amount, 5)
        self.assertEquals(award_transaction.reference_code, u'streak-2')


    def test_6_week_streak(self):
        # week 1 saving
        with freeze_time(datetime(2015, 12, 28, 10)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[0]
            )

        with freeze_time(datetime(2016, 1, 4)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 0)

        # week 2 saving
        with freeze_time(datetime(2016, 1, 10, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[1]
            )

        with freeze_time(datetime(2016, 1, 11)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 1)

        # week 3 saving
        with freeze_time(datetime(2016, 1, 17, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[2]
            )

        with freeze_time(datetime(2016, 1, 18)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 1)

        # week 4 saving
        with freeze_time(datetime(2016, 1, 20, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[3]
            )

        with freeze_time(datetime(2016, 1, 25)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 2)

        # week 5 saving
        with freeze_time(datetime(2016, 1, 28, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[4]
            )

        with freeze_time(datetime(2016, 2, 1)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 2)

        # week 6 saving
        with freeze_time(datetime(2016, 2, 2, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[5]
            )

        with freeze_time(datetime(2016, 2, 8)):
            calculate_rewards()
            calculate_rewards()


        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 3)
        self.assertEquals(self.user.balance(), 82)

        # week 7 saving
        with freeze_time(datetime(2016, 2, 9)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[6]
            )

        with freeze_time(datetime(2016, 2, 15)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 3)
        self.assertEquals(self.user.balance(), 92)

        # week 8 saving
        with freeze_time(datetime(2016, 2, 18, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[7]
            )

        with freeze_time(datetime(2016, 2, 22)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 4)
        self.assertEquals(self.user.balance(), 107)


    def test_1_week_missed_streak(self):
        # week 1
        with freeze_time(datetime(2015, 12, 28, 10)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[0]
            )

        with freeze_time(datetime(2016, 1, 4)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 0)

        # week 2
        with freeze_time(datetime(2016, 1, 10, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[1]
            )

        with freeze_time(datetime(2016, 1, 11)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 1)

        # week 3
        with freeze_time(datetime(2016, 1, 18)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 1)

        # week 4
        with freeze_time(datetime(2016, 1, 20, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[3]
            )

        with freeze_time(datetime(2016, 1, 25)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 1)

        # week 5
        with freeze_time(datetime(2016, 1, 28, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[4]
            )

        with freeze_time(datetime(2016, 2, 1)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 2)

        # week 6
        with freeze_time(datetime(2016, 2, 2, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[5]
            )

        with freeze_time(datetime(2016, 2, 8)):
            calculate_rewards()
            calculate_rewards()


        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 2)
        self.assertEquals(self.user.balance(), 60)

        # week 7
        with freeze_time(datetime(2016, 2, 9)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[6]
            )

        with freeze_time(datetime(2016, 2, 15)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 3)
        self.assertEquals(self.user.balance(), 77)

        # week 8 saving
        with freeze_time(datetime(2016, 2, 18, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[7]
            )

        with freeze_time(datetime(2016, 2, 22)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 3)
        self.assertEquals(self.user.balance(), 87)

        # week 9
        with freeze_time(datetime(2016, 2, 23, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[7]
            )

        with freeze_time(datetime(2016, 2, 29)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 4)
        self.assertEquals(self.user.balance(), 107)


    def test_with_withdrawal(self):
        # week 1 saving
        with freeze_time(datetime(2015, 12, 28, 10)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[0]
            )

        with freeze_time(datetime(2016, 1, 4)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 0)

        # week 2 saving
        with freeze_time(datetime(2016, 1, 10, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[1]
            )

        with freeze_time(datetime(2016, 1, 11)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 1)

        # week 3 saving
        with freeze_time(datetime(2016, 1, 17, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[2]
            )

        with freeze_time(datetime(2016, 1, 18)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 1)

        # week 4 saving
        with freeze_time(datetime(2016, 1, 20, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[3]
            )
            Transaction.objects.create(
                user=self.user,
                action=Transaction.WITHDRAWAL,
                amount=-5,
                reference_code=''
            )

        with freeze_time(datetime(2016, 1, 25)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 1)
        self.assertEquals(self.user.balance(), 40)

        # week 5 saving
        with freeze_time(datetime(2016, 1, 28, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[4]
            )

        with freeze_time(datetime(2016, 2, 1)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 1)

        # week 6 saving
        with freeze_time(datetime(2016, 2, 2, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[5]
            )

        with freeze_time(datetime(2016, 2, 8)):
            calculate_rewards()
            calculate_rewards()


        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 2)
        self.assertEquals(self.user.balance(), 65)

        # week 7 saving
        with freeze_time(datetime(2016, 2, 9)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[6]
            )

        with freeze_time(datetime(2016, 2, 15)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 2)
        self.assertEquals(self.user.balance(), 75)

        # week 8 saving
        with freeze_time(datetime(2016, 2, 18, 15)):
            Transaction.objects.create(
                user=self.user,
                action=Transaction.SAVING,
                amount=10,
                reference_code='saving',
                voucher=self.vouchers[7]
            )

        with freeze_time(datetime(2016, 2, 22)):
            calculate_rewards()
            calculate_rewards()

        self.assertEquals(Transaction.objects.filter(action=Transaction.REWARD).count(), 3)
        self.assertEquals(self.user.balance(), 92)
        self.assertEquals(Message.objects.count(), 3)


