# NG-Notifier
A News Reader as a webapp', bundled with celery for frequent checks of news, and a notifier system using mails &amp; pushbullet.

THe current version is running [here](https://42portal.com/ng-notifier/).

## How to?

### Initialization

We will use the virtualenv way, assuming python is aliased to python3.

* First, create a virtual environment with `virtualenv --no-site-packages ng-notifier`.
* Second, enter the VE using `cd ng-notifier; source bin/activate`.
* Third, clone the repository with `git clone https://github.com/Dubrzr/NG-Notifier.git web`.

The directory structure should now look like this:

```
path/ng-notifier/
  bin/
  include/
  lib/
  web/
    README.md
    requirements.txt
    static/
    ...
```

You will now have to install requirements for this project. Proceed with the
following command: `cd web; pip install -r requirements.txt` (it may take a while).

### Configuration

Now you have to set up your own settings in ngnotifier/settings.py file, just rename the example.settings.py file provided.

Things you must/may modify:

* SECRET_KEY (Generate a new one, google guys)
* DEBUG (Set to True or False)
* TEMPLATE_DEBUG (Set to True or False)
* ALLOWED_HOSTS
* DATABASES (You may use something else than sqlite3)
* TIME_ZONE
* STATIC_URL (website.comSTATIC_URL)
* SEND_FROM_POSTER (Pay attention to this parameter, you must have your own
  mail server else your provider may refuse your emails)
* FROM_ADDR (Will be used if SEND_FROM_POSTER is False)
* mail_conf (Fill in all parameters)
* SECONDS_DELTA (Seconds between 2 news checks)
* hosts (Set up all hosts you want)
* users (A variable to regiter default accounts - usefull for dev)

### Installation

You are now able to install the application.

Just type `python manage.py install` and it will do everything for you :)

You now have a ready to run application.

### Running the app

* To run the server just type `python manage.py runserver`.
* To execute tasks automatically, type `python manage.py celery -A ngnotifier
  worker --beat --concurrency=1`

## About

This project is maintained, and any pull request will be reviewed! Even for
grammar mistakes, and PEP-8.
