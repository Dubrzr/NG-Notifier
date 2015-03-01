from django.contrib.sites.models import get_current_site

from ngnotifier import settings


# NEVER PUT SITE PRIVATE PARAMETERS !!
from ngnotifier.models import User, NGHost


def site_infos(request):

    current_site = get_current_site(request)
    protocol = 'https'# if request.is_secure() else 'http'
    domain = current_site.domain

    count = 0
    for host in NGHost.objects.all():
        count += host.nb_notifs_sent

    return {
        'site_url' : settings.SITE_URL,
	'site_url_prefix': settings.SITE_URL_PREFIX,
        'site_name': settings.SITE_NAME,
        'protocol': protocol,
        'domain': domain,
        'nb_users': len(User.objects.filter(is_active=True)),
        'nb_notifs_sent': count
    }
