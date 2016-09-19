from django.conf.urls import url
from ussd import views

urlpatterns = [
    url(r'^user_registration/(?P<msisdn>[\d]+)/$', views.UssdRegistrationView.as_view()),
]
