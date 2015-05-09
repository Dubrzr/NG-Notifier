from _sha256 import sha224
from uuid import uuid4

from django.core.exceptions import ObjectDoesNotExist
from django.forms import EmailField, CharField, BooleanField
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


        # NGGroup.objects.get(id=groups)
        #
        # build_article()

        #
        # 200 news.ig-iit.com InterNetNews NNRP server INN 2.4.3 ready (posting ok).
        # 221 0 <slrnmfv4nb.36b.popowi_m@dump2017.epitech.net> head
        # Path: news.ig-iit.com!made by rockyluke!not-for-mail
        #     From: Mikael Popowicz <popowi_m@epita.fr>
        # Newsgroups: epita.cours.sql
        # Subject: [DBZ][TRIGGER] Foreign key
        # Date: Wed, 11 Mar 2015 00:57:15 +0000 (UTC)
        # Organization: IONIS Institute of Technology
        # Lines: 17
        # Message-ID: <slrnmfv4nb.36b.popowi_m@dump2017.epitech.net>
        # Reply-To: popowi_m@epita.fr
        # NNTP-Posting-Host: sge91-4-88-160-88-81.fbx.proxad.net
        # Mime-Version: 1.0
        # Content-Type: text/plain; charset=UTF-8
        # Content-Transfer-Encoding: 8bit
        # X-Trace: news.ig-iit.com 1426035435 8323 88.160.88.81 (11 Mar 2015 00:57:15 GMT)
        # X-Complaints-To: https://intranet.ig-iit.com
        # NNTP-Posting-Date: Wed, 11 Mar 2015 00:57:15 +0000 (UTC)
        # User-Agent: slrn/1.0.1 (Linux)
        # Xref: news.ig-iit.com epita.cours.sql:669
        # .
        #
