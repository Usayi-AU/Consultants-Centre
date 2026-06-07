import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'operations_dashboard.settings')
import django
django.setup()
from django.test import Client
client = Client(raise_request_exception=True)
try:
    response = client.get('/unlock/')
    print('STATUS', response.status_code)
    print(response.content.decode('utf-8', errors='replace'))
except Exception:
    import traceback
    import sys
    traceback.print_exc(file=sys.stdout)
