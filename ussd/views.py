from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django import http

import json

from .models import UssdUser

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
            'ussd_user_isnone': ussd_user is None
        }
        return http.JsonResponse(data)


    def post(self, request, *args, **kwargs):
        """ Update user with name, goal_item and/or goal_amount """
        ussd_user = self.get_object()
        if ussd_user is None:
            ussd_user = UssdUser(msisdn=self.kwargs.get('msisdn'))
        json_data = json.loads(request.body)
        for key in ['name', 'goal_item', 'goal_amount']:
            if json_data.get(key, None):
                ussd_user.__setattr__(key, json_data.get(key))
        ussd_user.save()
        return http.JsonResponse(ussd_user.to_dict())

