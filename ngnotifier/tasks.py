from ngnotifier.fixtures import hosts
from ngnotifier.models import NGHost, NGGroup, Log

from ngnotifier.notifs import send_notif
from ngnotifier.models import kinship_updater

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