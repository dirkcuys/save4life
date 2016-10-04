from django.contrib import admin

from ussd.models import Voucher
from ussd.models import UssdUser
from ussd.models import Transaction

admin.site.register(Voucher)
admin.site.register(UssdUser)
admin.site.register(Transaction)
