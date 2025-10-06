import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','messaging_app.messaging_app.settings')
import django
django.setup()
from django.test import Client
client = Client()
response = client.get('/chats/')
print('status=', response.status_code)
print('content=', response.content)
print('headers=', list(response.items()))
