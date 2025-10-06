from django.db import migrations


def create_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    # Use existing content type for chats app models (if available)
    ct, _ = ContentType.objects.get_or_create(app_label='chats', model='message')

    Permission.objects.get_or_create(codename='delete_message', name='Can delete message', content_type=ct)
    Permission.objects.get_or_create(codename='moderate_conversation', name='Can moderate conversation', content_type=ct)


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0002_user_password_hash'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_permissions, lambda apps, schema_editor: None),
    ]
