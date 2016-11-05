from django.db.models import Sum
from django.db.models import Count
from django.db.models import Q

from .models import Voucher
from .models import Transaction
from .models import Answer
from .models import Quiz
from .models import UssdUser

def generate_report_data(start, end):
    data = {}
    # Total amount of airtime redeemed this week
    data['total_airtime'] = Voucher.objects\
        .filter(redeemed_at__gt=start, redeemed_at__lte=end)\
        .aggregate(Sum('amount'))\
        .get('amount__sum') or 0

    period_transactions = Transaction.objects\
        .filter(created_at__gt=start, created_at__lte=end)

    # Total amount of airtime saved this week
    data['total_savings_amount'] = period_transactions\
        .filter(action=Transaction.SAVING)\
        .aggregate(Sum('amount'))\
        .get('amount__sum') or 0

    # Average savings this week
    savings_count = period_transactions\
        .filter(action=Transaction.SAVING)\
        .count()
    if savings_count > 0:
        data['average_savings'] = data['total_savings_amount']/savings_count
    else:
        data['average_savings'] = 0

    # Total 2 week streaks this week
    data['streak_2'] = period_transactions\
        .filter(action=Transaction.REWARD)\
        .filter(reference_code='streak-2')\
        .count()

    # Total 4 week streaks this week
    data['streak_4'] = period_transactions\
        .filter(action=Transaction.REWARD)\
        .filter(reference_code='streak-4')\
        .count()

    # Total 6 week streaks this week
    data['streak_6'] = period_transactions\
        .filter(action=Transaction.REWARD)\
        .filter(reference_code='streak-6')\
        .count()

    # Total quizzes completed this week
    completed_qs = Answer.objects\
        .filter(created_at__gt=start, created_at__lte=end)\
        .values('user', 'question__quiz')\
        .annotate(completed_questions=Count('pk'))\
        .filter(completed_questions=4)
    data['quizzes_completed'] = completed_qs.count()

    # Average quiz score this week
    total_score = 0
    for user_quiz in completed_qs:
        quiz = Quiz.objects.get(pk=user_quiz.get('question__quiz'))
        user = UssdUser.objects.get(msisdn=user_quiz.get('user'))
        total_score += quiz.mark_quiz(user)[1]
    if data['quizzes_completed'] > 0:
        data['average_quiz_score'] = total_score/data['quizzes_completed']
    else:
        data['average_quiz_score'] = 0
    
    return data

