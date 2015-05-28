from django.core.exceptions import ObjectDoesNotExist

from ngnotifier.models import NGHost, NGGroup, User, kinship_updater
from ngnotifier.utils import print_msg, print_done, print_exists, print_fail
from ngnotifier.settings import hosts, users


class NGFixtures():
    @staticmethod
    def create_hosts():
        for host in hosts:
            print_msg('host', hosts[host]['host'])
            try:
                NGHost.objects.get(host=hosts[host]['host'])
                print_exists()
            except ObjectDoesNotExist:
                try:
                    current_host = NGHost()
                    current_host.host = hosts[host]['host']
                    current_host.port = hosts[host]['port']
                    current_host.ssl = hosts[host]['ssl']
                    current_host.user = hosts[host]['user']
                    current_host.password = hosts[host]['pass']
                    current_host.timeout = hosts[host]['timeout']
                    current_host.save()
                    print_done()
                except Exception as e:
                    print_fail(e)


    @staticmethod
    def create_groups():
        for host in NGHost.objects.all():
            host.update_groups(hosts[host.host]['groups'], verbose=True)


    @staticmethod
    def clean_all():
        for group in NGGroup.objects.all():
            group.delete()
        for host in NGHost.objects.all():
            host.delete()


class UserFixtures():
    @staticmethod
    def create_users():
        for user in users:
            try:
                User.objects.get(
                    email=users[user]['mail']
                )
            except ObjectDoesNotExist:
                new_user = User()
                new_user.email = users[user]['mail']
                new_user.set_password(users[user]['password'])
                new_user.is_active = True
                new_user.is_admin = users[user]['admin']
                new_user.pushbullet_api_key = users[user]['pushbullet_api_key']
                new_user.send_emails = users[user]['notifs']['mail']
                new_user.send_pushbullets = users[user]['notifs']['pushbullet']
                new_user.save()

                for host in users[user]['subscriptions']:
                    ng_host = NGHost.objects.get(
                        host=hosts[host]['host']
                    )
                    for group in hosts[host]['groups']:
                        ng_group = NGGroup.objects.get(
                            host=ng_host,
                            name=group
                        )
                        new_user.add_ng_group(ng_group)