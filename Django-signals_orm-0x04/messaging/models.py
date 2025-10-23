from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class MessageManager(models.Manager):
    def get_conversation_thread(self, message):
        """Get entire conversation thread for a message"""
        return self.filter(
            models.Q(id=message.id) |
            models.Q(parent_message=message) |
            models.Q(parent_message__parent_message=message)
        ).select_related('sender', 'receiver', 'parent_message').prefetch_related('replies')
    
    def get_user_conversations(self, user):
        """Get all conversations for a user"""
        return self.filter(
            models.Q(sender=user) | models.Q(receiver=user)
        ).select_related('sender', 'receiver').prefetch_related('replies').order_by('-timestamp')


class UnreadMessagesManager(models.Manager):
    def get_queryset(self):
        """Return only unread messages"""
        return super().get_queryset().filter(read=False)
    
    def for_user(self, user):
        """Get unread messages for a specific user"""
        return self.get_queryset().filter(
            receiver=user
        ).select_related('sender', 'receiver').only(
            'id', 'sender__username', 'receiver__username', 'content', 'timestamp', 'read'
        )


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    objects = MessageManager()
    unread = UnreadMessagesManager()
    
    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"
    
    def get_thread(self):
        """Get all replies in this thread"""
        return Message.objects.filter(
            models.Q(id=self.id) |
            models.Q(parent_message=self)
        ).select_related('sender', 'receiver').order_by('timestamp')


class MessageHistory(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='history')
    old_content = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"History for Message {self.message.id}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=50, default='new_message')
    
    def __str__(self):
        return f"Notification for {self.user} - {self.notification_type}"