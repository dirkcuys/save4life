from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django import http

import json
from datetime import datetime

from .models import UssdUser
from .models import Voucher
from .models import Transaction
from .tasks import send_welcome_sms
from .tasks import issue_airtime

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
            send_welcome_sms.delay(ussd_user.msisdn)

        return http.JsonResponse(ussd_user.to_dict())


class VoucherVerifyView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(VoucherVerifyView, self).dispatch(*args, **kwargs)


    def get_user(self):
        json_data = json.loads(self.request.body)
        msisdn = json_data.get('msisdn')
        queryset = UssdUser.objects.filter(msisdn=msisdn)
        if queryset.count() == 1:
            return queryset.get()
        else:
            return None


    def get_voucher(self):
        json_data = json.loads(self.request.body)
        queryset = Voucher.objects.filter(code = json_data.get('voucher_code'))
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


class VoucherRedeemView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(VoucherRedeemView, self).dispatch(*args, **kwargs)


    def get_user(self):
        json_data = json.loads(self.request.body)
        msisdn = json_data.get('msisdn')
        queryset = UssdUser.objects.filter(msisdn=msisdn)
        if queryset.count() == 1:
            return queryset.get()
        else:
            return None


    def get_voucher(self):
        json_data = json.loads(self.request.body)
        queryset = Voucher.objects.filter(code = json_data.get('voucher_code'))
        if queryset.count() == 1:
            return queryset.get()
        return None


    def post(self, request, *args, **kwargs):
        user = self.get_user()
        voucher = self.get_voucher()

        if user is None or voucher is None:
            return http.JsonResponse({"status": "invalid"}) #TODO make errors consistent

        # make sure voucher wasn't already redeemed or revoked!!
        if voucher.redeemed_at or voucher.revoked_at:
            return http.JsonResponse({"status": "invalid"}) #TODO make errors consistent

        json_data = json.loads(self.request.body)
        savings_amount = json_data.get("savings_amount")
        # verify that savings amount is valid
        if savings_amount > voucher.amount or savings_amount < 0:
            return http.JsonResponse({"status": "invalid"}) #TODO make errors consistent

        voucher.redeemed_at = datetime.utcnow()
        voucher.redeemed_by = user
        voucher.save()

        # Credit user balance with savings amount
        Transaction.objects.create(
                user=user,
                action=Transaction.SAVING,
                amount=savings_amount,
                reference_code='savings',
                voucher=voucher
        )

        # Credit airtime with remainder - call external API
        issue_airtime.delay(voucher)

        return http.JsonResponse({"status": "success"})
