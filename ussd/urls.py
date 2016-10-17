from django.conf.urls import url
from ussd import views

urlpatterns = [
    url(r'^user_registration/(?P<msisdn>[\d]+)/$', views.UssdRegistrationView.as_view()),
    url(r'^voucher/verify/$', views.VoucherVerifyView.as_view()),
    url(r'^voucher/redeem/$', views.VoucherRedeemView.as_view()),
    url(r'^quiz/$', views.QuizView.as_view()),
    url(r'^quiz/(?P<quiz_id>[\d]+)/question/(?P<question_index>[\d]+)/$', views.AnswerSubmitView.as_view()),
]
