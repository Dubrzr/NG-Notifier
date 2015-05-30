import time
import os
from ngnotifier.management.utils import query_yes_no

from django.core.management.base import BaseCommand
from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler

from ngnotifier.settings import SECONDS_DELTA_NEWS, SECONDS_DELTA_GROUP
from ngnotifier.tasks import update_news, update_groups
from ngnotifier.utils import bcolors

class Command(BaseCommand):
    help = 'Installs the app: checks requirements, creates DB, '\
           'and adds its fixtures'

    def handle(self, *args, **options):
        print(
            'Welcome to the %s tasks launcher...' % settings.SITE_NAME)
        print('Your settings are :')
        print('-> Time between two "new group" checks = ' + bcolors.WARNING
              + str(SECONDS_DELTA_GROUP) + ' seconds.' + bcolors.ENDC)
        print('-> Time between two "new news" checks = ' + bcolors.WARNING
              + str(SECONDS_DELTA_NEWS) + ' seconds.' + bcolors.ENDC)



        # **** REQUIREMENTS **** #
        self.stdout.write(bcolors.WARNING +
                          '\n\nLaunching tasks...' +
                          bcolors.ENDC)
        self.stdout.write('------------------------>>')
        scheduler = BackgroundScheduler()
        scheduler.add_job(update_news, 'interval', seconds=SECONDS_DELTA_NEWS)
        scheduler.add_job(update_groups, 'interval', seconds=SECONDS_DELTA_GROUP)
        scheduler.start()
        self.stdout.write('------------------------>> ' +
                          bcolors.OKGREEN + 'Done !\n\n' + bcolors.ENDC)
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
        try:
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
