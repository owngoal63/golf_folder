# accounts/views.py
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView, PasswordResetView
from django.conf import settings

from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordResetForm, ContactForm

from django.shortcuts import render, redirect
from django.core.mail import send_mail, BadHeaderError

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    success_url = reverse_lazy("home")
    template_name = "registration/login.html"

class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    success_url = "../password_reset/done/"
    template_name = "registration/password_reset_form.html"

def SendMailView(request, recipient):
    # url format /accounts/sendmail/gordonalindsay@gmail.com/
    res = send_mail(
        subject = 'Test Email',
        message = 'Here is the message.',
        from_email = 'notrelevant@gmail.com',
        recipient_list = [recipient],
        fail_silently=False,
    )  
    return render(request,"email/email_sent.html", {'email_address': recipient})

def ContactView(request):
    if request.method == "GET":
        # Pass the user details to form if signed on, don't if not (AnonymousUser)
        form = ContactForm(initial={'from_email': request.user}) if not str(request.user) == 'AnonymousUser' else ContactForm() 
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            from_email = form.cleaned_data["from_email"]
            message = form.cleaned_data['message']
            try:
                send_mail(subject, message, from_email, [settings.CONTACT_EMAIL_ADDRESS])
            except BadHeaderError:
                print("Contact Form Email Error: Invalid header found.")
                return
            return redirect("contactsuccess")
    return render(request, "contact/contact_form.html", {"form": form})

def ContactSuccessView(request):
    return render(request, "contact/contact_success.html")



