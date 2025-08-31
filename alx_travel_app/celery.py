import os
from celery import Celery

# set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app_0x03.settings')

app = Celery('alx_travel_app_0x03')

# read settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# discover tasks.py in apps
app.autodiscover_tasks()
