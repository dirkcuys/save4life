from django import forms
from django.contrib import admin

from .models import Quiz
from .models import UssdUser

class MessageAdminForm(forms.ModelForm):

    to = forms.ChoiceField(choices=[('*','*')] + [(u.msisdn,u.msisdn) for u in UssdUser.objects.all()])

    def __init__(self, *args, **kwargs):
        super(MessageAdminForm, self).__init__(*args, **kwargs)
        self.fields['body'].widget = admin.widgets.AdminTextareaWidget()

    # TODO validate that all addresses in to field are registered users


class VoucherGenerateForm(forms.Form):
    
    vouchers_10 = forms.IntegerField(label='R10 vouchers', min_value=0, initial=0)
    vouchers_20 = forms.IntegerField(label='R20 vouchers', min_value=0, initial=0)
    vouchers_50 = forms.IntegerField(label='R50 vouchers', min_value=0, initial=0)
    distributor = forms.CharField(max_length=128)


class QuizAdminForm(forms.ModelForm):
    reminder_text = forms.CharField(max_length=160, widget=admin.widgets.AdminTextareaWidget())
    class Meta:
        model = Quiz
        exclude = ['reminder']
    
    def __init__(self, *args, **kwargs):
        super(QuizAdminForm, self).__init__(*args, **kwargs)  
        instance = kwargs.get('instance')
        if not instance is None:
            self.fields['reminder_text'].initial = instance.reminder.body


class QuizAwardForm(forms.Form):
    sms_text = forms.CharField(label='Text for prize SMS', max_length=160, widget=forms.Textarea)
