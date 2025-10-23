from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
import logging
from .models import Message, Notification, MessageHistory

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """Create notification when new message is received"""
    if created:
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            notification_type='new_message'
        )

@receiver(pre_save, sender=Message)
def log_message_edits(sender, instance, **kwargs):
    """Log previous content before message is edited"""
    if instance.pk:  # Existing message being updated
        try:
            old_message = Message.objects.get(pk=instance.pk)
            if old_message.content != instance.content:
                MessageHistory.objects.create(
                    message=instance,
                    old_content=old_message.content
                )
                instance.edited = True
        except Message.DoesNotExist:
            pass

@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """Log user deletion - related data will be deleted via CASCADE"""
    logger.info(f"User {instance.username} (ID: {instance.id}) has been deleted. Related data cleanup completed.")