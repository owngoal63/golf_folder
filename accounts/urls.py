# accounts/urls.py
from django.urls import path
# from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from .views import SignUpView, CustomLoginView, CustomPasswordResetView, SendMailView, ContactView, ContactSuccessView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("password_reset/", CustomPasswordResetView.as_view(), name="passwordreset"),
    path('sendmail/<str:recipient>/', SendMailView, name='sendmail'),
    path("contact/", ContactView, name="contact"),
    path("contactsuccess/", ContactSuccessView, name="contactsuccess"),
]

urlpatterns += staticfiles_urlpatterns()