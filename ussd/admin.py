from django.contrib import admin

from ussd import models
from ussd.forms import MessageAdminForm

class UssdUserAdmin(admin.ModelAdmin):
    list_display = ('msisdn', 'name', 'goal_item', 'goal_amount')

class QuestionInline(admin.TabularInline):
    model = models.Question

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


admin.site.register(models.Voucher)
admin.site.register(models.Transaction)
admin.site.register(models.Quiz, QuizAdmin)
admin.site.register(models.Message, MessageAdmin)
admin.site.register(models.UssdUser, UssdUserAdmin)
