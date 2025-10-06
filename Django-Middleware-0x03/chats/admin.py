from django.contrib import admin
from .models import Conversation, Message

# Register models used in the tests
admin.site.register(Conversation)
admin.site.register(Message)
