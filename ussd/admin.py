from django.contrib import admin
from django.conf.urls import url

from ussd import models
from ussd.forms import MessageAdminForm
from ussd.views import generate_vouchers

class UssdUserAdmin(admin.ModelAdmin):
    list_display = ('msisdn', 'name', 'goal_item', 'goal_amount', 'balance', 'streak')

class QuestionInline(admin.TabularInline):
    model = models.Question
    max_num = 4
    min_num = 4
    can_delete = False


class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('publish_at', 'ends_at')


class MessageAdmin(admin.ModelAdmin):
    form = MessageAdminForm
    exclude = ('sent_at',)
    list_display = ('to', 'body', 'send_at', 'sent_at')

    # TODO this doesn't disable the link from the list
    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.sent_at is not None:
            return False
        return super(MessageAdmin, self).has_change_permission(request, obj=obj)


class VoucherAdmin(admin.ModelAdmin):
    list_display = [
        'amount',
        'distributor', 
        'created_at',
        'redeemed_at',
        'revoked_at',
        'redeemed_by'
    ]
    change_list_template = 'voucher_change_list.html'

    def has_add_permission(self, request, obj=None):
        return False


    def get_urls(self):
        urls = super(VoucherAdmin, self).get_urls()
        my_urls = [
            url(r'^generate_vouchers/$',
                self.admin_site.admin_view(generate_vouchers),
                name="generate_vouchers"
            )
        ]
        return my_urls + urls


class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'user', 'action', 'reference_code', 'voucher', 'amount'
    ]
    list_display_links = None

    def get_actions(self, request):
        actions = super(TransactionAdmin, self).get_actions(request)
        # Disable delete
        del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(models.Voucher, VoucherAdmin)
admin.site.register(models.Transaction, TransactionAdmin)
admin.site.register(models.Quiz, QuizAdmin)
admin.site.register(models.Message, MessageAdmin)
admin.site.register(models.UssdUser, UssdUserAdmin)
