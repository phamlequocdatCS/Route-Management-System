from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from ..forms import LoginForm, PasswordResetForm, RegistrationForm
from ..models import PERMISSIONS, Account, LoggerSystem


@login_required(login_url="home")
def logout_view(request):
    new_log = LoggerSystem.create_logout_log(request.user)
    new_log.save()
    print(new_log)
    logout(request)
    return redirect("home")


def login_view(request):
    form = LoginForm(request.POST or None)
    user = None
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        print(username)
        print(password)
        user = authenticate(request, username=username, password=password)
        print(f"Authenticated User: {user}")

        if user is None:
            print("Authentication failed. Checking if user exists in the database...")
            try:
                user_from_db = Account.objects.get(username=username)
                print(f"User found in database: {user_from_db}")
                
                print(f"Checking password: {user_from_db.check_password(password)}")
            except Account.DoesNotExist:
                print("User does not exist in the database.")

    if user is not None:
        print(user)
        login(request, user)
        new_log = LoggerSystem.create_login_log(user)
        print(new_log)
        new_log.save()
        return redirect("home")

    return render(request, "login.html", {"form": form})


def register_view(request):
    form = RegistrationForm(request.POST or None)

    if form.is_valid():
        form.save()
        username = form.cleaned_data.get("username")
        messages.info(request, f"{username}")
        return redirect("register_success")

    return render(request, "register.html", {"form": form})


def register_success_view(request):
    username = ""
    for message in messages.get_messages(request):
        if message.level == messages.INFO:
            username = message.message
            break
    return render(request, "register_success.html", {"username": username})


@login_required(login_url="home")
def account_create_view(request):
    if not request.user.has_perm(PERMISSIONS.CAN_CREATE_ACCOUNT):
        return HttpResponseForbidden()
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        token = default_token_generator.make_token(user)
        to_email = form.cleaned_data.get("email")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        email = create_activate_acc_email(request, user, to_email, uid, token)
        print(email.send())
        return HttpResponse(
            f'Email is sent to {to_email}. <a href="/routeManager/home">Return to home</a>'
        )
    return render(request, "register.html", {"form": form})


def password_reset_view(request):
    form = PasswordResetForm(request.POST or None)
    if form.is_valid():
        to_email = form.cleaned_data.get("email")
        ssn = form.cleaned_data.get("ssn")
        try:
            user = Account.objects.get(email=to_email, ssn=ssn)
        except Account.DoesNotExist:
            form.add_error(None, "No account found with the provided email and SSN.")
        else:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            email = create_pass_reset_email(request, user, to_email, uid, token)
            email.send()
            return HttpResponse(
                f'Email is sent to {user.email}. <a href="/routeManager/home">Return to home</a>'
            )
    else:
        form = PasswordResetForm()
    return render(request, "password_reset.html", {"form": form})


def create_activate_acc_email(request, user, to_email, uid, token):
    mail_subject = "Activate your account"
    message = render_to_string(
        "acc_active_email.html",
        {
            "user": user,
            "domain": request.META["HTTP_HOST"],
            "uid": uid,
            "token": token,
            "password_reset_link": request.build_absolute_uri(
                reverse(
                    "password_reset_confirm", kwargs={"uidb64": uid, "token": token}
                )
            ),
        },
    )
    email = EmailMessage(mail_subject, message, to=[to_email])
    return email


def create_pass_reset_email(request, user, to_email, uid, token):
    mail_subject = "Reset your password"
    message = render_to_string(
        "password_reset_email.html",
        {
            "user": user,
            "domain": request.META["HTTP_HOST"],
            "uid": uid,
            "token": token,
            "password_reset_link": request.build_absolute_uri(
                reverse(
                    "password_reset_confirm", kwargs={"uidb64": uid, "token": token}
                )
            ),
        },
    )
    email = EmailMessage(mail_subject, message, to=[to_email])
    return email
