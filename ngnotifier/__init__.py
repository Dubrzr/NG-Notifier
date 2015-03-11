import os

os.environ["DJANGO_SETTINGS_MODULE"] = "ngnotifier.settings"


# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .tasks import app as celery_app
