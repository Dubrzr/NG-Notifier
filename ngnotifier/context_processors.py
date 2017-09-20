from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist

from ngnotifier import settings


# NEVER PUT SITE PRIVATE PARAMETERS !!
from ngnotifier.models import User, Log
from push_notifications.models import APNSDevice, GCMDevice


def size_fmt(num, suffix=''):
   for unit in ['','K','M','G','T','P','E','Z']:
       if abs(num) < 1000.0:
           return "%3.1f%s%s" % (num, unit, suffix)
       num /= 1000.0
   return "%.1f%s%s" % (num, 'Y', suffix)

def site_infos(request):
    current_site = get_current_site(request)
    protocol = 'https'  # if request.is_secure() else 'http'
    domain = current_site.domain
    count_email = Log.objects.filter(type='N', description__startswith='E').count()
    count_android = Log.objects.filter(type='N', description__startswith='A').count()
    count_ios = Log.objects.filter(type='N', description__startswith='i').count()
    count = count_email + count_android + count_ios

    try:
        last_un_update = Log.objects.filter(type='UN').latest('date').date
    except ObjectDoesNotExist:
        last_un_update = None

    return {
        'site_url': settings.SITE_URL,
        'site_url_prefix': settings.SITE_URL_PREFIX,
        'site_name': settings.SITE_NAME,
        'protocol': protocol,
        'domain': domain,
        'nb_users': User.objects.filter(is_active=True, anonymous=False).count(),
        'nb_android': GCMDevice.objects.filter(active=1).count(),
        'nb_ios': APNSDevice.objects.filter(active=1).count(),
        'nb_notifs_sent_email_str': size_fmt(count_email),
        'nb_notifs_sent_android_str': size_fmt(count_android),
        'nb_notifs_sent_ios_str': size_fmt(count_ios),
        'nb_notifs_sent_str': size_fmt(count),
        'nb_notifs_sent_email': count_email,
        'nb_notifs_sent_android': count_android,
        'nb_notifs_sent_ios': count_ios,
        'nb_notifs_sent': count,
        'last_un_update': last_un_update
    }
