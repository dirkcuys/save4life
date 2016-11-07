from django import forms
from django.contrib import admin

from .models import Quiz
from .models import Question
from .models import UssdUser

def _to_choices(self):
    return [('*','*')] + [(u.msisdn,u.msisdn) for u in UssdUser.objects.all()]


class MessageAdminForm(forms.ModelForm):

    to = forms.ChoiceField(choices=_to_choices)

    def __init__(self, *args, **kwargs):
        super(MessageAdminForm, self).__init__(*args, **kwargs)
        self.fields['body'].widget = admin.widgets.AdminTextareaWidget()


class VoucherGenerateForm(forms.Form):
    
    vouchers_10 = forms.IntegerField(label='R10 vouchers', min_value=0, initial=0)
    vouchers_20 = forms.IntegerField(label='R20 vouchers', min_value=0, initial=0)
    vouchers_50 = forms.IntegerField(label='R50 vouchers', min_value=0, initial=0)
    distributor = forms.CharField(max_length=128)


class SplitOptionsWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (
            forms.TextInput(attrs=attrs),
            forms.TextInput(attrs=attrs),
            forms.TextInput(attrs=attrs),
            forms.TextInput(attrs=attrs),
        )
        super(SplitOptionsWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return value.split(',')
        return [None, None, None, None]


class OptionsField(forms.MultiValueField):
    widget = SplitOptionsWidget
    def __init__(self, *args, **kwargs):
        fields = (
            forms.CharField(max_length=32, label='Option 1'),
            forms.CharField(max_length=32, label='Option 1'),
            forms.CharField(max_length=32, label='Option 1'),
            forms.CharField(max_length=32, label='Option 1'),
        )
        super(OptionsField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        return ','.join(data_list)


class QuestionAdminForm(forms.ModelForm):

    options = OptionsField()
    solution = forms.ChoiceField(choices=[(i, 'Option {}'.format(i+1)) for i in range(4)])

    class Meta:
        model = Question
        fields = '__all__'


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
