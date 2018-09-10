import os

import pandas as pd

from ngnotifier.fixtures import hosts
from ngnotifier.models import NGHost, NGGroup, Log, NGNews

from ngnotifier.notifs import send_notif
from ngnotifier.models import kinship_updater
from ngnotifier.settings import STATIC_ROOT


def update_news(verbose=False, notif=True):
    notif_count_before = Log.objects.filter(type='N').count()
    for host in NGHost.objects.all():
        if verbose:
            print('Checking host {}:'.format(host.host), flush=False)
        groups = NGGroup.objects.filter(host=host)
        tmp_co = host.get_co()
        new_news_list_all = []
        for group in groups:
            new_news_list = group.update_news(tmp_co, verbose=verbose)
            new_news_list_all += new_news_list
            if notif:
                send_notif(new_news_list, group)

        print("    Found {} news".format(len(new_news_list_all)))

        print("\    Updating kinship links...")
        kinship_updater()
        for nn in new_news_list_all:
            nn.add_answer_count()
    if verbose and notif:
        notif_count_after = Log.objects.filter(type='N').count()
        print('    Sent {} notifications!'.format(notif_count_after-notif_count_before))
    Log.objects.create(type='UN')


def update_hosts(verbose=False):
    for host in NGHost.objects.all():
        host.update_groups(groups=hosts[host.host]['groups'], verbose=verbose)
    Log.objects.create(type='UG')


def update_stats(verbose=False):
    for host in NGHost.objects.all():
        groups = NGGroup.objects.filter(host=host)
        newss = pd.DataFrame.from_records(NGNews.objects.filter(groups__in=groups).values('date', 'father', 'has_children'))
        newss['date'] = newss.date.dt.floor('D')
        newss['father'] = newss.father.map(lambda x: 1 if x != '' else 0)
        newss['has_children'] = newss.has_children.map(lambda x: 1 if x else 0)
        count_by_day = newss.drop("has_children", axis=1).groupby('date').count()
        count_by_day_root = newss.drop("has_children", axis=1)[newss.father == 0].groupby('date').count()
        count_by_day_children = newss.drop("has_children", axis=1)[newss.father == 1].groupby('date').count()
        tmp = newss[newss.father == 0]
        count_root_answered = tmp.drop("father", axis=1)[tmp.has_children == 1].groupby('date').count()
        count_root_never_answered = tmp.drop("father", axis=1)[tmp.has_children == 0].groupby('date').count()

        min_date = newss.date.min().floor('D')
        max_date = newss.date.max().ceil('D')
        t = pd.date_range(min_date, max_date, freq='D').to_frame()

        res = t.merge(count_by_day, left_on=0, right_on='date', how='left')\
            .merge(count_by_day_root,  left_on=0, right_on='date', how='left')\
            .merge(count_by_day_children, left_on=0, right_on='date', how='left')\
            .merge(count_root_answered, left_on=0, right_on='date', how='left')\
            .merge(count_root_never_answered, left_on=0, right_on='date', how='left')\
            .fillna(0)
        res.columns = ['date', 'total', 'root', 'children', 'answered', 'never_answered']
        res.to_csv(os.path.join(STATIC_ROOT, 'stats_news_{}.csv'.format(host.host)))

        Log.objects.create(type='US')