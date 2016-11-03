from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import SingleObjectMixin
from django.utils.decorators import method_decorator
from django import http
from django.utils import timezone

import json
from datetime import datetime

from .models import UssdUser
from .models import Voucher
from .models import Quiz, Answer
from .tasks import send_welcome_sms
from .transactions import TransactionError
from .transactions import award_joining_bonus
from .transactions import redeem_voucher
from .transactions import withdraw_savings


class UssdUserMixin(object):

    def get_user(self):
        msisdn = ''
        if self.request.method == 'GET':
            msisdn = self.request.GET.get('msisdn')
        else:
            json_data = json.loads(self.request.body)
            msisdn = json_data.get('msisdn')
        queryset = UssdUser.objects.filter(msisdn=msisdn)
        if queryset.count() == 1:
            return queryset.get()
        else:
            #TODO should we raise a 404?
            return None


# Create your views here.
class UssdRegistrationView(View):

    def get_object(self):
        msisdn = self.kwargs.get('msisdn')
        queryset = UssdUser.objects.filter(msisdn=msisdn)
        if queryset.count() == 1:
            return queryset.get()
        else:
            return None

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(UssdRegistrationView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        ussd_user = self.get_object()
        data = {
            'msisdn': self.kwargs.get('msisdn'),
        }
        if ussd_user:
            data.update(ussd_user.to_dict())
        return http.JsonResponse(data)

    def post(self, request, *args, **kwargs):
        """ Update user with name, goal_item, goal_amount and/or recurring_amount """
        ussd_user = self.get_object()

        # get or create user
        if ussd_user is None:
            ussd_user = UssdUser(msisdn=self.kwargs.get('msisdn'))
        was_complete = ussd_user.registration_complete()

        # update attributes
        json_data = json.loads(request.body)
        for key in ['name', 'goal_item', 'goal_amount', 'recurring_amount', 'pin']:
            if json_data.get(key, None):
                ussd_user.__setattr__(key, json_data.get(key))
        ussd_user.save()

        # if registration was just completed, send welcome sms
        is_complete = ussd_user.registration_complete()
        if not was_complete and is_complete:
            award_joining_bonus(ussd_user)
            send_welcome_sms.delay(ussd_user.msisdn)

        return http.JsonResponse(ussd_user.to_dict())


class VoucherVerifyView(View, UssdUserMixin):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(VoucherVerifyView, self).dispatch(*args, **kwargs)

    def get_voucher(self):
        json_data = json.loads(self.request.body)
        queryset = Voucher.objects.filter(code=json_data.get('voucher_code'))
        if queryset.count() == 1:
            return queryset.get()
        return None

    def post(self, request, *args, **kwargs):
        user = self.get_user()
        if user is None:
            #TODO shouldn't happen under normal circumstances - log error!
            return http.JsonResponse({'error_code': 403, 'msg': 'user not registered'})
       
        voucher = self.get_voucher()
        if voucher is None:
            return http.JsonResponse({"status": "invalid"})

        voucher_data = {}
        if voucher.redeemed_at:
            voucher_data["status"] = "used"
        elif voucher.revoked_at:
            voucher_data["status"] = "invalid"
        else:
            voucher_data["status"] = "valid"
            voucher_data["amount"] = voucher.amount
        return http.JsonResponse(voucher_data)


class VoucherRedeemView(View, UssdUserMixin):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(VoucherRedeemView, self).dispatch(*args, **kwargs)

    def get_voucher(self):
        json_data = json.loads(self.request.body)
        queryset = Voucher.objects.filter(code=json_data.get('voucher_code'))
        if queryset.count() == 1:
            return queryset.get()
        return None

    def post(self, request, *args, **kwargs):
        user = self.get_user()
        voucher = self.get_voucher()
        if user is None or voucher is None:
            return http.JsonResponse({"status": "invalid"})  # TODO make errors consistent
        json_data = json.loads(self.request.body)
        savings_amount = json_data.get("savings_amount")

        try:
            redeem_voucher(voucher, user, savings_amount)
        except TransactionError as e:
            return http.JsonResponse({"status": "invalid"})  # TODO make errors consistent
        return http.JsonResponse({"status": "success"})


class QuizView(View, UssdUserMixin):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(QuizView, self).dispatch(*args, **kwargs)

    def get_active_quiz(self):
        # Find a quiz with an end date in the future
        queryset = Quiz.objects\
            .filter(ends_at__gt=timezone.now())\
            .filter(publish_at__lte=timezone.now())\
            .order_by('ends_at')
        # TODO Does this need to use utcnow()?
        return queryset.first()

    def get(self, request, *args, **kwargs):
        ussd_user = self.get_user()
        if ussd_user is None:
            return http.JsonResponse({'status': 'error', 'reason': 'no user'})  # TODO
        # Get active quiz
        quiz = self.get_active_quiz()
        data = {}
        if quiz:
            data.update(quiz.to_dict())
            # get user answers for this quiz to add user_progress field
            answers = Answer.objects.filter(user=ussd_user, question__quiz=quiz)
            results = quiz.mark_quiz(ussd_user)
            data.update({'user_progress': results[1]})
            data.update({'user_score': results[0]})

        return http.JsonResponse(data)


class AnswerSubmitView(View, SingleObjectMixin, UssdUserMixin):

    pk_url_kwarg = 'quiz_id'
    model = Quiz

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(AnswerSubmitView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        ussd_user = self.get_user()
        if ussd_user is None:
            return http.JsonResponse({'status': 'error', 'reason': 'no user'})  # TODO
        quiz = self.get_object()
        question_index = int(self.kwargs.get('question_index'))  # TODO
        question_query_set = quiz.question_set.all().order_by('id')
        question = list(question_query_set)[question_index]
        # check if answer for this question already exists
        if question.answer_set.filter(user=ussd_user).exists():
            return http.JsonResponse({'status': 'error'})  # TODO
        # save answer
        user_response = json.loads(request.body).get('answer')
        Answer.objects.create(question=question, user=ussd_user, user_response=user_response)
        data = {
            'correct': user_response == question.solution,
            'answer_text': question.answer_text(),
            'reinforce_text': question.reinforce_text
        }
        return http.JsonResponse(data)


class PinVerifyView(View, UssdUserMixin):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(PinVerifyView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.get_user()
        if user is None:
            return http.JsonResponse({'error_code': 403, 'msg': 'user not registered'})
        json_data = json.loads(self.request.body)
        data = {}
        if user.pin and user.pin == json_data.get('pin'):
            data["status"] = "valid"
        else:
            data["status"] = "invalid"
        return http.JsonResponse(data)


class WithdrawView(View, UssdUserMixin):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(WithdrawView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.get_user()
        if user is None:
            return http.JsonResponse({'error_code': 403, 'msg': 'user not registered'})
        resp_data = {}
        
        json_data = json.loads(self.request.body)
        pin = json_data.get('pin')
        if pin is None or user.pin != pin:
            resp_data["status"] = 'error'  # TODO handle error
            return http.JsonResponse(resp_data)
        
        amount = abs(json_data.get('amount'))
        try:
            withdraw_savings(user, amount)
        except TransactionError as e:
            resp_data['status'] = 'error'  # TODO handle error
            return http.JsonResponse(resp_data)

        resp_data['status'] = 'success'
        return http.JsonResponse(resp_data)
