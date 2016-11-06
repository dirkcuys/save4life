from django.contrib import admin
from django.conf.urls import url
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.utils.html import format_html

from ussd import models
from ussd.forms import MessageAdminForm
from ussd.views import generate_vouchers
from ussd.views import QuizResultsView

from datetime import datetime
import csv

class UssdUserAdmin(admin.ModelAdmin):
    list_display = ('msisdn', 'name', 'goal_item', 'goal_amount', 'balance', 'streak')

class QuestionInline(admin.TabularInline):
    model = models.Question
    max_num = 4
    min_num = 4
    can_delete = False


class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('publish_at', 'ends_at', 'results')

    def results(self, obj):
        results_url = reverse('admin:quiz_results', args=(obj.pk,))
        return format_html('<a href="{0}">View results</a>', results_url)

    def get_urls(self):
        urls = super(QuizAdmin, self).get_urls()
        my_urls = [
            url(r'^(?P<quiz_id>[\d]+)/results/$',
                self.admin_site.admin_view(QuizResultsView.as_view()),
                name="quiz_results"
            )
        ]
        return my_urls + urls



class MessageAdmin(admin.ModelAdmin):
    form = MessageAdminForm
    exclude = ('sent_at',)
    list_display = ('to', 'body', 'send_at', 'sent_at')

    # TODO this doesn't disable the link from the list
    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.sent_at is not None:
            return False
        return super(MessageAdmin, self).has_change_permission(request, obj=obj)


def revoke_vouchers(modeladmin, request, queryset):
    queryset.update(revoked_at=datetime.utcnow())
revoke_vouchers.short_description = "Revoke selected vouchers to prevent them from being used"


def export_voucher_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="vouchers.csv"'

    writer = csv.writer(response)
    writer.writerow(['code', 'amount', 'redeemed_at', 'revoked_at', 'distributor', 'redeemed_by', 'created_at', 'updated_at'])
    writer.writerows([
        [ 
            voucher.code,
            voucher.amount,
            voucher.redeemed_at,
            voucher.revoked_at,
            voucher.distributor,
            voucher.redeemed_by,
            voucher.created_at,
            voucher.updated_at
        ] for voucher in queryset 
    ])
    return response
export_voucher_as_csv.short_description = "Export selected vouchers as CSV"


def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="vouchers.csv"'

    values = queryset.values()
    writer = csv.DictWriter(response, fieldnames=values[0].keys())
    writer.writeheader()
    writer.writerows(values)
    return response
export_as_csv.short_description = "Export selected objects as CSV"


class VoucherAdmin(admin.ModelAdmin):
    list_display = [
        'amount',
        'distributor', 
        'created_at',
        'redeemed_at',
        'revoked_at',
        'redeemed_by'
    ]
    list_display_links = None
    list_filter = ['distributor', 'amount']
    change_list_template = 'voucher_change_list.html'
    actions = [revoke_vouchers, export_as_csv]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super(VoucherAdmin, self).get_actions(request)
        # Disable delete
        del actions['delete_selected']
        return actions

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
