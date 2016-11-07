from django.contrib import admin
from django.contrib import messages
from django.conf.urls import url
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils import timezone

from ussd import models
from ussd.forms import MessageAdminForm
from ussd.forms import QuizAdminForm
from ussd.forms import QuestionAdminForm
from ussd.views import generate_vouchers
from ussd.views import QuizResultsView
from ussd.views import QuizAwardView

import csv


def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="vouchers.csv"'

    values = queryset.values()
    writer = csv.DictWriter(response, fieldnames=values[0].keys())
    writer.writeheader()
    writer.writerows(values)
    return response
export_as_csv.short_description = "Export selected objects as CSV"


class UssdUserAdmin(admin.ModelAdmin):
    list_display = (
        'msisdn', 'name', 'goal_item', 'goal_amount', 'balance', 
        'total_2_week_streaks', 'total_4_week_streaks', 'total_6_week_streaks',
        'total_quiz_awards'
    )

    def total_2_week_streaks(self, obj):
        return obj.transaction_set.all()\
            .filter(action=models.Transaction.REWARD)\
            .filter(reference_code='streak-2')\
            .count()

    def total_4_week_streaks(self, obj):
        return obj.transaction_set.all()\
            .filter(action=models.Transaction.REWARD)\
            .filter(reference_code='streak-4')\
            .count()

    def total_6_week_streaks(self, obj):
        return obj.transaction_set.all()\
            .filter(action=models.Transaction.REWARD)\
            .filter(reference_code='streak-6')\
            .count()

    def total_quiz_awards(self, obj):
        return obj.transaction_set.all()\
            .filter(action=models.Transaction.QUIZ_PRIZE)\
            .count()


class QuestionInline(admin.StackedInline):
    model = models.Question
    form = QuestionAdminForm
    max_num = 4
    min_num = 4
    can_delete = False


class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('name', 'description', 'publish_at', 'ends_at', 'total_responses','results', 'is_live')
    actions = [export_as_csv]
    form = QuizAdminForm

    def results(self, obj):
        results_url = reverse('admin:quiz_results', args=(obj.pk,))
        return format_html('<a href="{0}">View results</a>', results_url)

    def is_live(self, obj):
        return obj.publish_at <= timezone.now() < obj.ends_at

    def save_model(self, request, obj, form, change):
        super(QuizAdmin, self).save_model(request, obj, form, change)
        if change == False:
            obj.reminder = models.Message.objects.create(
                to='*',
                body=form.cleaned_data['reminder_text'],
                send_at=obj.publish_at
            )
            obj.save()
        else:
            # check to see if we've already sent the reminder
            if obj.reminder.sent_at is None:
                obj.reminder.body = form.cleaned_data['reminder_text']
                obj.send_at = obj.publish_at
                obj.reminder.save()
            elif obj.reminder.body != form.cleaned_data['reminder_text']:
                # warn user that quiz reminder has been sent already
                self.message_user(request, 'The reminder SMS has already been sent', level=messages.WARNING)

    def get_urls(self):
        urls = super(QuizAdmin, self).get_urls()
        my_urls = [
            url(r'^(?P<quiz_id>[\d]+)/results/$',
                self.admin_site.admin_view(QuizResultsView.as_view()),
                name="quiz_results"
            ),
            url(r'^(?P<quiz_id>[\d]+)/award/(?P<msisdn>[\d]+)/$',
                self.admin_site.admin_view(QuizAwardView.as_view()),
                name="quiz_award"
            )
        ]
        return my_urls + urls


class MessageAdmin(admin.ModelAdmin):
    form = MessageAdminForm
    exclude = ('sent_at',)
    list_display = ('to', 'body', 'send_at', 'sent_at')
    actions = [export_as_csv]

    # TODO this doesn't disable the link from the list
    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.sent_at is not None:
            return False
        return super(MessageAdmin, self).has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.sent_at is not None:
            return False
        return super(MessageAdmin, self).has_delete_permission(request, obj=obj)


def revoke_vouchers(modeladmin, request, queryset):
    queryset.update(revoked_at=timezone.now())
revoke_vouchers.short_description = "Revoke selected vouchers to prevent them from being used"


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
    actions = [export_as_csv]

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
