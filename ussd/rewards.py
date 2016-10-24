from .models import Transaction, UssdUser

from datetime import datetime, timedelta


def calculate_rewards():
    """ Calculate rewards streaks for users who saved consecutive streaks.
    This method should be run once a week
    Rewards will be calculated for streaks ending the previous week.
    """
    # TODO move streak_award somewhere else and finalize amounts
    streak_award = [5, 7, 10]

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=today.weekday()+7)

    # get all users who saved in the previous week
    users = Transaction.objects.filter(
        action=Transaction.SAVING,
        created_at__gt=week_start,
        created_at__lte=week_start + timedelta(weeks=1),
        amount__gt=0
    ).values('user_id')

    for user in UssdUser.objects.filter(pk__in=users):
        savings = user.transaction_set.filter(
            action=Transaction.SAVING,
            amount__gt=0
        ).values('created_at').order_by('-created_at')
        weeks = 0  # Number of consecutive weeks saved
        while True:
            start = week_start - timedelta(days=weeks*7)
            end = start + timedelta(days=7)
            # make sure the user saved during the week
            if not savings.filter(created_at__gt=start, created_at__lte=end).exists():
                break
            # check for withdrawals during the week
            withdrawals = user.transaction_set.filter(created_at__gt=start).\
                filter(created_at__lte=end).\
                filter(action=Transaction.WITHDRAWAL)
            if withdrawals.exists():
                break
            weeks += 1
        rewards = user.transaction_set.filter(
            action=Transaction.REWARD,
            created_at__gt=week_start-timedelta(weeks=weeks-1)
        )
        conditions = [
            weeks > 0,
            weeks % 2 == 0,
            rewards.count() < weeks/2
        ]
        if all(conditions):
            streak = weeks/2 % 3
            # TODO move transaction code somewhere central
            Transaction.objects.create(
                user=user,
                action=Transaction.REWARD,
                amount=streak_award[streak-1],
                reference_code='streak {0} reward'.format(streak)
            )
