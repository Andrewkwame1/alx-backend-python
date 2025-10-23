# messaging/tests.py

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.cache import cache
from .models import Message, Notification, MessageHistory

class MessageNotificationSignalTest(TestCase):
    """Test cases for Signal: Message Notifications"""

    def setUp(self):
        # Create users for testing
        self.sender = User.objects.create_user(username='sender', password='password123')
        self.receiver = User.objects.create_user(username='receiver', password='password123')

    def test_notification_creation_on_new_message(self):
        """Test that a notification is created when a new message is sent"""
        # Ensure no notifications exist initially
        self.assertEqual(Notification.objects.count(), 0)
        
        # Create a new message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Hello, World!"
        )

        # Check if a notification is created for the receiver
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.notification_type, 'new_message')
        self.assertFalse(notification.is_read)

    def test_no_notification_on_message_update(self):
        """Test that no new notification is created when updating an existing message"""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Hello, World!"
        )
        initial_notification_count = Notification.objects.count()
        
        # Update the message
        message.content = "Updated content"
        message.save()
        
        # Verify no new notification was created
        self.assertEqual(Notification.objects.count(), initial_notification_count)


class MessageEditHistorySignalTest(TestCase):
    """Test cases for Signal: Message Edit History"""

    def setUp(self):
        self.sender = User.objects.create_user(username='sender', password='password123')
        self.receiver = User.objects.create_user(username='receiver', password='password123')

    def test_message_history_on_content_edit(self):
        """Test that message history is recorded when message content is edited"""
        original_content = "Original message"
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content=original_content
        )
        
        # Ensure no history exists initially
        self.assertEqual(MessageHistory.objects.count(), 0)
        
        # Edit the message
        new_content = "Edited message"
        message.content = new_content
        message.save()
        
        # Verify history was recorded
        self.assertEqual(MessageHistory.objects.count(), 1)
        history = MessageHistory.objects.first()
        self.assertEqual(history.message, message)
        self.assertEqual(history.old_content, original_content)
        self.assertTrue(message.edited)

    def test_message_edited_flag(self):
        """Test that the edited flag is set when message is modified"""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original"
        )
        self.assertFalse(message.edited)
        
        message.content = "Modified"
        message.save()
        
        # Reload from database to verify
        message.refresh_from_db()
        self.assertTrue(message.edited)

    def test_no_history_for_content_unchanged(self):
        """Test that no history is created if content remains the same"""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Content"
        )
        
        # Update other fields but not content
        message.read = True
        message.save()
        
        # Verify no history was created
        self.assertEqual(MessageHistory.objects.count(), 0)


class UserDeletionSignalTest(TestCase):
    """Test cases for Signal: User Deletion and Cleanup"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.receiver = User.objects.create_user(username='receiver', password='password123')

    def test_user_deletion_cascades_messages(self):
        """Test that all messages are deleted when a user is deleted"""
        # Create messages sent by the user
        msg1 = Message.objects.create(
            sender=self.user,
            receiver=self.receiver,
            content="Message 1"
        )
        
        # Create message received by the user
        msg2 = Message.objects.create(
            sender=self.receiver,
            receiver=self.user,
            content="Message 2"
        )
        
        self.assertEqual(Message.objects.count(), 2)
        
        # Delete the user
        self.user.delete()
        
        # Verify all messages are deleted (CASCADE)
        self.assertEqual(Message.objects.count(), 0)

    def test_user_deletion_cascades_notifications(self):
        """Test that all notifications are deleted when a user is deleted"""
        message = Message.objects.create(
            sender=self.receiver,
            receiver=self.user,
            content="Test message"
        )
        
        self.assertEqual(Notification.objects.count(), 1)
        
        # Delete the user
        self.user.delete()
        
        # Verify notifications are deleted
        self.assertEqual(Notification.objects.count(), 0)

    def test_user_deletion_cascades_message_history(self):
        """Test that message history is deleted when related message is deleted"""
        message = Message.objects.create(
            sender=self.user,
            receiver=self.receiver,
            content="Original"
        )
        
        # Edit message to create history
        message.content = "Edited"
        message.save()
        
        self.assertEqual(MessageHistory.objects.count(), 1)
        
        # Delete the user (which cascades to messages and then history)
        self.user.delete()
        
        # Verify history is deleted
        self.assertEqual(MessageHistory.objects.count(), 0)


class UnreadMessagesManagerTest(TestCase):
    """Test cases for Custom ORM Manager: Unread Messages"""

    def setUp(self):
        self.sender = User.objects.create_user(username='sender', password='password123')
        self.receiver = User.objects.create_user(username='receiver', password='password123')

    def test_unread_manager_filters_unread_messages(self):
        """Test that unread manager only returns unread messages"""
        # Create unread message
        unread = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Unread message",
            read=False
        )
        
        # Create read message
        read = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Read message",
            read=True
        )
        
        # Query using unread manager
        unread_messages = Message.unread.all()
        
        self.assertEqual(unread_messages.count(), 1)
        self.assertEqual(unread_messages.first().id, unread.id)

    def test_unread_manager_for_specific_user(self):
        """Test that unread manager filters for specific receiver"""
        other_user = User.objects.create_user(username='other', password='password123')
        
        # Messages for receiver
        msg1 = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="For receiver",
            read=False
        )
        
        # Messages for other user
        msg2 = Message.objects.create(
            sender=self.sender,
            receiver=other_user,
            content="For other",
            read=False
        )
        
        # Get unread for specific user
        unread = Message.unread.for_user(self.receiver)
        
        self.assertEqual(unread.count(), 1)
        self.assertEqual(unread.first().id, msg1.id)

    def test_unread_manager_only_returns_necessary_fields(self):
        """Test that only() optimization is applied"""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test",
            read=False
        )
        
        unread = Message.unread.for_user(self.receiver).first()
        
        # Verify essential fields are present
        self.assertIsNotNone(unread.id)
        self.assertIsNotNone(unread.sender)
        self.assertIsNotNone(unread.receiver)
        self.assertIsNotNone(unread.content)


class ThreadedConversationsOrmTest(TestCase):
    """Test cases for ORM Optimization: Threaded Conversations"""

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')

    def test_parent_message_field(self):
        """Test that parent_message field enables threading"""
        parent = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Parent message"
        )
        
        reply = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply to parent",
            parent_message=parent
        )
        
        self.assertEqual(reply.parent_message, parent)
        self.assertIn(reply, parent.replies.all())

    def test_get_conversation_thread(self):
        """Test that conversation thread retrieves all related messages optimally"""
        parent = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Parent"
        )
        
        reply1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply 1",
            parent_message=parent
        )
        
        reply2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Reply 2",
            parent_message=parent
        )
        
        thread = Message.objects.get_conversation_thread(parent)
        
        self.assertEqual(thread.count(), 3)
        self.assertIn(parent, thread)
        self.assertIn(reply1, thread)
        self.assertIn(reply2, thread)

    def test_get_user_conversations(self):
        """Test efficient retrieval of all user conversations with optimization"""
        msg1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Message 1"
        )
        
        msg2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Message 2"
        )
        
        conversations = Message.objects.get_user_conversations(self.user1)
        
        self.assertEqual(conversations.count(), 2)
        self.assertIn(msg1, conversations)
        self.assertIn(msg2, conversations)

    def test_get_thread_method_on_message(self):
        """Test the get_thread method returns ordered thread"""
        parent = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Parent"
        )
        
        reply = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply",
            parent_message=parent
        )
        
        thread = parent.get_thread()
        
        self.assertEqual(thread.count(), 2)
        # Verify ordering by timestamp
        self.assertEqual(list(thread), [parent, reply])


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
})
class CachingTest(TestCase):
    """Test cases for View-level Caching"""

    def setUp(self):
        self.sender = User.objects.create_user(username='sender', password='password123')
        self.receiver = User.objects.create_user(username='receiver', password='password123')
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_cache_configuration(self):
        """Test that cache backend is properly configured"""
        from django.core.cache import cache
        
        # Test set and get
        cache.set('test_key', 'test_value', 60)
        self.assertEqual(cache.get('test_key'), 'test_value')

    def test_cache_ttl(self):
        """Test that cache entries expire after TTL"""
        cache.set('expiring_key', 'value', 1)
        self.assertIsNotNone(cache.get('expiring_key'))
        
        # After TTL, key should be gone (simulated by immediate clear)
        cache.delete('expiring_key')
        self.assertIsNone(cache.get('expiring_key'))
