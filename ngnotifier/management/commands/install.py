from subprocess import call
from ngnotifier.management.utils import query_yes_no

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings

from ngnotifier.fixtures import NGFixtures, UserFixtures
from ngnotifier.utils import bcolors
from ngnotifier.tasks import update_news

class Command(BaseCommand):
    help = 'Installs the app: checks requirements, creates DB, '\
           'and adds its fixtures'

    def handle(self, *args, **options):
        print(
            'Welcome to the %s installation procedure...' % settings.SITE_NAME)
        print(
            'Before installation please check twice your configuration in '
            '\'web/ngnotifier/settings.py\' file.')
        print('Your settings are :')
        print('-> MODE = ' + bcolors.WARNING + (
        'DEBUG' if settings.DEBUG else 'PRODUCTION') + bcolors.ENDC)
        print('-> TEMPLATE_DEBUG = ' + bcolors.WARNING + ('ON' if
            settings.TEMPLATE_DEBUG else 'OFF') + bcolors.ENDC)
        print('-> DATABASE = ' + bcolors.WARNING
              + settings.DATABASES['default']['ENGINE'] + bcolors.ENDC)


        if not query_yes_no('Start installation?'):
            exit()

        # **** REQUIREMENTS **** #
        self.stdout.write(bcolors.WARNING +
                          '\n\nInstalling requirements...' +
                          bcolors.ENDC)
        self.stdout.write('------------------------>>')
        call("sud o pip install -r requirements.txt --upgrade", shell=True)
        self.stdout.write('------------------------>> ' +
                          bcolors.OKGREEN + 'Done !\n\n' + bcolors.ENDC)

        # **** STATICS **** #
        self.stdout.write(bcolors.WARNING +
                          'Installing statics...' +
                          bcolors.ENDC)
        self.stdout.write('------------------->>')
        call_command('collectstatic', interactive=False)
        self.stdout.write('------------------->> ' +
                          bcolors.OKGREEN + 'Done !\n\n' + bcolors.ENDC)

        # **** DATABASE **** #
        self.stdout.write(bcolors.WARNING +
                          'Installing database...' +
                          bcolors.ENDC)
        self.stdout.write('-------------------->>')
        call("python manage.py migrate", shell=True)
        self.stdout.write('-------------------->> ' +
                          bcolors.OKGREEN + 'Done !\n\n' + bcolors.ENDC)

        # **** FIXTURES **** #
        self.stdout.write(bcolors.WARNING +
                          'Installing fixtures...' +
                          bcolors.ENDC)
        self.stdout.write('-------------------->>')
        fixtures = NGFixtures()
        fixtures.create_hosts()
        fixtures.create_groups()
        update_news(True, False)
        fixtures = UserFixtures()
        fixtures.create_users()
        self.stdout.write('-------------------->> ' +
                          bcolors.OKGREEN + 'Done !\n\n' + bcolors.ENDC)

        self.stdout.write(bcolors.OKGREEN +
                          'Successfully installed app!' +
                          bcolors.ENDC)