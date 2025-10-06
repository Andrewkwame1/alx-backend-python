import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messaging_app.settings')

try:
    django.setup()
    from django.urls import get_resolver
    r = get_resolver()
    print('Root url patterns count:', len(r.url_patterns))
    for p in r.url_patterns:
        print(type(p), getattr(p, 'pattern', p))
except Exception as e:
    print('Error during import:', repr(e))
    raise
