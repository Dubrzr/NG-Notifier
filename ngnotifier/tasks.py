from ngnotifier.fixtures import hosts
from ngnotifier.models import NGHost, NGGroup

from ngnotifier.notifs import send_notif
from ngnotifier.models import kinship_updater

def update_news(verbose=False, notif=True):
    for host in NGHost.objects.all():
        # if verbose:
        #     print('Checking host {}:'.format(host.host), flush=False)
        groups = NGGroup.objects.filter(host=host)
        tmp_co = host.get_co()
        new_news_list_all = []
        for group in groups:
            new_news_list = group.update_news(tmp_co, verbose=verbose)
            new_news_list_all += new_news_list
            if notif:
                send_notif(new_news_list, group)

        kinship_updater(new_news_list_all)
        for nn in new_news_list_all:
            nn.add_answer_count()
    if verbose and notif:
        print('\t\tSent {} notifications!'.format(0))


def update_hosts(verbose=False):
    for host in NGHost.objects.all():
        host.update_groups(groups=hosts[host.host]['groups'], verbose=verbose)