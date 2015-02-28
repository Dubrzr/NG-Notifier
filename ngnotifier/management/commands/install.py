from subprocess import call
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings
import sys
from ngnotifier.fixtures import NGFixtures, UserFixtures
from ngnotifier.utils import bcolors


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")


class Command(BaseCommand):
    help = 'Installs the app: checks requirements, creates DB, '\
           'and adds its fixtures'

    def handle(self, *args, **options):
        print('Welcome to the %s installation procedure...' % settings.SITE_NAME)
        print('Before installation please check twice your configuration in \'web/ngnotifier/settings.py\' file.')
        print('Your settings are :')
        print('-> MODE = ' + bcolors.WARNING + ('DEBUG' if settings.DEBUG else 'PRODUCTION') + bcolors.ENDC)
        print('-> DATABASE = ' + bcolors.WARNING + 'SQLITE3' + bcolors.ENDC)
        print('-> TEMPLATE_DEBUG = ' + bcolors.WARNING + str(settings.TEMPLATE_DEBUG) + bcolors.ENDC)

        if not query_yes_no('Confirm ?'):
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
        self.stdout.write( '-------------------->>')
        call("python manage.py migrate", shell=True)
        self.stdout.write('-------------------->> ' +
                          bcolors.OKGREEN + 'Done !\n\n' + bcolors.ENDC)

        # **** FIXTURES **** #
        self.stdout.write(bcolors.WARNING +
                          'Installing fixtures...' +
                          bcolors.ENDC)
        self.stdout.write('-------------------->>')
        fixtures = NGFixtures()
        fixtures.create_hosts_and_groups()
        fixtures = UserFixtures()
        fixtures.create_users()
        self.stdout.write('-------------------->> ' +
                          bcolors.OKGREEN + 'Done !\n\n' + bcolors.ENDC)

        self.stdout.write(bcolors.OKGREEN +
                          'Successfully installed app!' +
                          bcolors.ENDC)