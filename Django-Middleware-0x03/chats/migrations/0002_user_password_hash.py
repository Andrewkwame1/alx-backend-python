"""No-op migration to keep a linear migration history for tests.

This intentionally has no operations. The original project included a
custom User model migration here which is not present in the simplified
test copy; keeping this file as a no-op avoids merge conflicts while
allowing later migrations (like the permissions migration) to run.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chats", "0001_initial"),
    ]

    operations = []
