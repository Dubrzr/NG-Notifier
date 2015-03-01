from _sha256 import sha224
from uuid import uuid4
from django.core.exceptions import ObjectDoesNotExist
from django.forms import EmailField, CharField, BooleanField, PasswordInput
from django import forms
from captcha.fields import CaptchaField
from ngnotifier.models import User

class CaptchaForm(forms.Form):
    email = EmailField()
    captcha = CaptchaField()

    def save(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')

        token = sha224(uuid4().hex.encode('utf-8')).hexdigest()
        try:
            # If the user already exists, we just update its token
            user = User.objects.get(
                email=email
            )
            user.token = token
            user.save()
            return user, token
        except ObjectDoesNotExist:
            new_user = User()
            new_user.token = token
            new_user.email = email
            new_user.save()
            return new_user, token

class SettingsForm(forms.Form):
    password = CharField(required=False, max_length=100)
    enable_emails = BooleanField(required=False)
    enable_pushbullets = BooleanField(required=False)
    pushbullet_api_key = CharField(required=False, max_length=64)

    def save(self, user):
        cleaned_data = super().clean()
        enable_emails = cleaned_data.get('enable_emails')
        enable_pushbullets = cleaned_data.get('enable_pushbullets')
        p_api_key = cleaned_data.get('pushbullet_api_key')
        password = cleaned_data.get('password')

        if not len(p_api_key):
            enable_pushbullets = False

        user.send_emails = enable_emails
        user.send_pushbullets = enable_pushbullets
        user.pushbullet_api_key = p_api_key
        if password != '' and password != None:
            user.set_password(password)
        user.save()


