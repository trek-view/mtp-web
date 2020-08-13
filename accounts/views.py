
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from datetime import datetime
from mailerlite import MailerLiteApi
import secrets

from lib.functions import send_mail_with_html

from .models import CustomUser
from .forms import UserSignUpForm, UserProfileForm

def signup(request):
    if request.method == "POST":
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            authenticate(email=email, password=password)
            if user != None:
                user.verify_email_key = secrets.token_urlsafe(50)
                user.save()

                # confirm email 
                try:
                    # send email to creator
                    subject = 'Please confirm your email'
                    html_message = render_to_string(
                        'emails/account/signup_email_confirm.html', 
                        { 'subject': subject, 'url': '/accounts/email-verify/' + user.verify_email_key}, 
                        request
                    )
                    send_mail_with_html(subject, html_message, email)
                except:
                    print('email sending error!')


                # add maillist
                if user.is_maillist:
                    mailerAPI = MailerLiteApi(settings.MAILERLIST_API_KEY)
                    data = [{
                        'email': user.email,
                        'name': user.username
                    }]
                    try:
                        print(mailerAPI.groups.add_subscribers(group_id=settings.MAILERLIST_GROUP_ID, subscribers_data=data))
                    except:
                        pass
                messages.success(request, 'Please check inbox to confirm your email address.')
                return redirect('login')
    else:
        form = UserSignUpForm()
    return render(request, 'signup.html', {'form': form})

def email_verify(request, key):
    user = CustomUser.objects.get(verify_email_key=key)
    if user:
        user.is_active = True
        user.save()

        # confirm email successfully
        try:
            # send email to creator
            subject = 'Your account is confirmed successfully'
            html_message = render_to_string(
                'emails/account/signup_email_confirmed.html', 
                { 'subject': subject}, 
                request
            )
            send_mail_with_html(subject, html_message, user.email)
        except:
            print('email sending error!')
        messages.success(request, 'Your account is confirmed. You can now login.')
    else:
        message.error(request, 'Error, invalid token!')
    return redirect('login')
    # return render(request, 'registration/confirm_template.html', {'success': False})

@login_required
def profile_edit(request):
    user = request.user
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.updated_at = datetime.now()
            user.save()
            messages.success(request, 'Your email is updated successfully.')
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'account/index.html', {'form': form})

def change_password_success(request):
    messages.success(request, 'Your password is updated successfully.')
    return redirect('change_password')