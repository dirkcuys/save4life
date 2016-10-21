from django import forms
from django.contrib import admin

class MessageAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(MessageAdminForm, self).__init__(*args, **kwargs)
        self.fields['body'].widget = admin.widgets.AdminTextareaWidget()

    # TODO validate that all addresses in to field are registered users
