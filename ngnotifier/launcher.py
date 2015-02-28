import nntplib
from ngnotifier.models import NGHost


def get_overviews(co, group_name):
    try:
        # Getting infos & data from the given group
        _, _, first, last, _ = co.group(group_name)
        # Sending a OVER command to get last_nb posts
        _, overviews = co.over((first, last))
    except Exception as err:
        print("Can't get news from {} group.".format(group_name))
        print("Error: {}".format(err))
        return None
    return overviews

def update():
    for ng_host in NGHost.objects.all():
        print('before')
        print(ng_host.get_all_groups())

        ng_host.update_groups()
        print('after')
        print(ng_host.get_all_groups())

