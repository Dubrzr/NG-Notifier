from django.contrib.sites.shortcuts import get_current_site

from ngnotifier import settings


# NEVER PUT SITE PRIVATE PARAMETERS !!
from ngnotifier.models import User, NGHost, Log


def site_infos(request):
    current_site = get_current_site(request)
    protocol = 'https'  # if request.is_secure() else 'http'
    domain = current_site.domain
    count = Log.objects.filter(type='N').count()

    return {
        'site_url': settings.SITE_URL,
        'site_url_prefix': settings.SITE_URL_PREFIX,
        'site_name': settings.SITE_NAME,
        'protocol': protocol,
        'domain': domain,
        'nb_users': len(User.objects.filter(is_active=True, anonymous=False)),
        'nb_notifs_sent': count
    }
