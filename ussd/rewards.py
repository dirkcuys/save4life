from .models import Transaction, UssdUser
from .transactions import award_streak

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
        weeks = user.streak()
        rewards = user.transaction_set.filter(
            action=Transaction.REWARD,
            created_at__gt=week_start-timedelta(weeks=weeks-1)
        )
        conditions = [
            weeks > 0,
            weeks % 2 == 0,
            rewards.count() < weeks//2
        ]
        if all(conditions):
            streak = weeks//2 % 3
            # TODO move transaction code somewhere central
            award_streak(user, streak, streak_award[streak-1])
