from django.contrib import admin

from ussd import models

class QuestionInline(admin.TabularInline):
    model = models.Question

class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]

admin.site.register(models.Voucher)
admin.site.register(models.UssdUser)
admin.site.register(models.Transaction)
admin.site.register(models.Quiz, QuizAdmin)
