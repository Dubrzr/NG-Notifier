from __future__ import absolute_import
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'ngnotifier.settings'
from datetime import timedelta
from celery import Celery
from django.conf import settings
from ngnotifier.fixtures import hosts
from ngnotifier.models import NGHost, NGGroup

# set the default Django settings module for the 'celery' program.
from ngnotifier.notifs import send_notif
from ngnotifier.settings import SECONDS_DELTA

app = Celery('ngnotifier')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
# app.config_from_object(CeleryConfig)

app.conf.update(
    # Broker settings.
    BROKER_URL = 'sqla+sqlite:///db.sqlite3',

    CELERY_RESULT_BACKEND = 'db+sqlite:///results.db',

    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_RESULT_SERIALIZER='json',
    CELERY_TIMEZONE='Europe/Paris',
    CELERY_ENABLE_UTC=True,

    CELERYBEAT_SCHEDULE = {
        'every-minute': {
            'task': 'ngnotifier.tasks.update_news',
            'schedule': timedelta(seconds=SECONDS_DELTA),
            },
        'every-day': {
            'task': 'ngnotifier.tasks.update_groups',
            'schedule': timedelta(seconds=86400),
            },
        }
)

@app.task
def update_news():
    m = 0
    p = 0
    for ng_host in NGHost.objects.all():
        print('Checking {} host:'.format(ng_host.host), flush=False)
        ng_groups = NGGroup.objects.filter(host=ng_host)
        co = ng_host.get_co()
        m_tmp = 0
        p_tmp = 0
        for ng_group in ng_groups:
            new_news_list = ng_group.update_news(co, verbose=False)
            m_tmp_grp, p_tmp_grp = send_notif(new_news_list, ng_group)
            m_tmp += m_tmp_grp
            p_tmp += p_tmp_grp
        if m_tmp + p_tmp > 0:
            ng_host.nb_notifs_sent += m_tmp + p_tmp
            ng_host.save()
        m += m_tmp
        p += p_tmp
    print('\t\tSent {} emails!'.format(m))
    print('\t\tSent {} pushs!'.format(p))

# Add 24h task to update groups/host
@app.task
def update_groups():
    for ng_host in NGHost.objects.all():
       ng_host.update_groups(groups=hosts[ng_host.host]['groups'],
                             check_news=False, verbose=False)