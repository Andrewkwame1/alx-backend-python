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
                    old_content=old_message.content,
                    edited_by=instance.sender  # User who edited the message
                )
                instance.edited = True
        except Message.DoesNotExist:
            pass

@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """Clean up all user-related data when user is deleted"""
    # Delete all messages sent by the user
    Message.objects.filter(sender=instance).delete()
    
    # Delete all messages received by the user
    Message.objects.filter(receiver=instance).delete()
    
    # Delete all notifications for the user
    Notification.objects.filter(user=instance).delete()
    
    # Delete all message history entries edited by the user
    MessageHistory.objects.filter(edited_by=instance).delete()
    
    logger.info(f"User {instance.username} (ID: {instance.id}) has been deleted. All related messages, notifications, and edit histories have been removed.")