from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django import http

import json

from .models import UssdUser
from .tasks import send_welcome_sms

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
        """ Update user with name, goal_item and/or goal_amount """
        ussd_user = self.get_object()

        # get or create user 
        if ussd_user is None:
            ussd_user = UssdUser(msisdn=self.kwargs.get('msisdn'))
        was_complete = ussd_user.name and ussd_user.goal_item and ussd_user.goal_amount
        
        # update attributes
        json_data = json.loads(request.body)
        for key in ['name', 'goal_item', 'goal_amount']:
            if json_data.get(key, None):
                ussd_user.__setattr__(key, json_data.get(key))
        ussd_user.save()

        # if registration was just completed, send welcome sms
        is_complete = ussd_user.name and ussd_user.goal_item and ussd_user.goal_amount
        if not was_complete and is_complete:
            send_welcome_sms.delay(uss_user.msisdn)

        return http.JsonResponse(ussd_user.to_dict())

