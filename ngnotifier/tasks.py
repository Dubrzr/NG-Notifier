from ngnotifier.fixtures import hosts
from ngnotifier.models import NGHost, NGGroup

from ngnotifier.notifs import send_notif
from ngnotifier.models import kinship_updater

def update_news(verbose=False, notif=True):
    m = 0
    p = 0
    for host in NGHost.objects.all():
        # if verbose:
            # print('Checking {} host:'.format(host.host), flush=False)
        groups = NGGroup.objects.filter(host=host)
        tmp_co = host.get_co()
        m_tmp = 0
        p_tmp = 0
        new_news_list_all = []
        for group in groups:
            new_news_list = group.update_news(tmp_co, verbose=verbose)
            new_news_list_all += new_news_list
            if notif:
                m_tmp_grp, p_tmp_grp = send_notif(new_news_list, group)
                m_tmp += m_tmp_grp
                p_tmp += p_tmp_grp
                if m_tmp + p_tmp > 0:
                    host.nb_notifs_sent += m_tmp + p_tmp
                    host.save()
                m += m_tmp
                p += p_tmp

        kinship_updater(new_news_list_all)
        for nn in new_news_list_all:
            nn.add_answer_count()
    if verbose and notif:
        print('\t\tSent {} emails!'.format(m))
        print('\t\tSent {} pushs!'.format(p))


def update_groups(verbose=False):
    for host in NGHost.objects.all():
        host.update_groups(groups=hosts[host.host]['groups'], verbose=verbose)