from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import time
import os

User = get_user_model()


class RequestLoggingMiddlewareTest(TestCase):
    """Test cases for Task 1: Request Logging Middleware"""
    
    def setUp(self):
        self.client = Client()
        # Clean up log file before each test
        if os.path.exists('requests.log'):
            os.remove('requests.log')
    
    def test_request_logging_anonymous_user(self):
        """Test that anonymous user requests are logged"""
        response = self.client.get('/chats/')
        
        # Check that log file exists
        self.assertTrue(os.path.exists('requests.log'))
        
        # Read log file
        with open('requests.log', 'r') as f:
            log_content = f.read()
        
        # Verify log contains required information
        self.assertIn('User: Anonymous', log_content)
        self.assertIn('Path: /chats/', log_content)
    
    def test_request_logging_authenticated_user(self):
        """Test that authenticated user requests are logged"""
        # Create and login user
        user = User.objects.create_user(username='testuser', password='test123')
        self.client.login(username='testuser', password='test123')
        
        # Make request
        response = self.client.get('/chats/')
        
        # Read log file
        with open('requests.log', 'r') as f:
            log_content = f.read()
        
        # Verify user is logged
        self.assertIn('User: testuser', log_content)
        self.assertIn('Path: /chats/', log_content)
    
    def test_multiple_requests_logged(self):
        """Test that multiple requests are all logged"""
        # Make multiple requests
        self.client.get('/chats/')
        self.client.get('/chats/test/')
        
        # Read log file
        with open('requests.log', 'r') as f:
            log_lines = f.readlines()
        
        # Should have at least 2 log entries
        self.assertGreaterEqual(len(log_lines), 2)


class RestrictAccessByTimeMiddlewareTest(TestCase):
    """Test cases for Task 2: Time-Based Access Control"""
    
    def setUp(self):
        self.client = Client()
    
    def test_access_during_allowed_hours(self):
        """Test access is allowed during 9 AM - 6 PM"""
        # Mock current time to be within allowed hours (12 PM)
        with self.mock_time(hour=12):
            response = self.client.get('/chats/')
            self.assertNotEqual(response.status_code, 403)
    
    def test_access_before_allowed_hours(self):
        """Test access is denied before 9 AM"""
        with self.mock_time(hour=8):
            response = self.client.get('/chats/')
            self.assertEqual(response.status_code, 403)
            self.assertIn(b'restricted', response.content.lower())
    
    def test_access_after_allowed_hours(self):
        """Test access is denied after 6 PM"""
        with self.mock_time(hour=19):
            response = self.client.get('/chats/')
            self.assertEqual(response.status_code, 403)
            self.assertIn(b'restricted', response.content.lower())
    
    def test_non_chat_paths_not_restricted(self):
        """Test that non-chat paths are not time-restricted"""
        with self.mock_time(hour=20):
            response = self.client.get('/admin/')
            # Should redirect to login, not return 403 for time
            self.assertNotEqual(response.status_code, 403)
    
    def mock_time(self, hour):
        """Context manager to mock current hour"""
        from unittest.mock import patch
        mock_datetime = datetime.now().replace(hour=hour, minute=0, second=0)
        return patch('chats.middleware.timezone.now', return_value=mock_datetime)


class OffensiveLanguageMiddlewareTest(TestCase):
    """Test cases for Task 3: Rate Limiting (Offensive Language Middleware)"""
    
    def setUp(self):
        self.client = Client()
        # Reset rate limit counters
        from django.core.cache import cache
        cache.clear()
    
    def test_rate_limit_allows_within_limit(self):
        """Test that requests within rate limit are allowed"""
        # Send 5 POST requests (within limit)
        for i in range(5):
            response = self.client.post('/chats/messages/send/', {
                'message': f'Test message {i}',
                'conversation_id': 1
            }, content_type='application/json')
            self.assertNotEqual(response.status_code, 403, 
                              f"Request {i+1} should not be blocked")
    
    def test_rate_limit_blocks_exceeded_requests(self):
        """Test that 6th request within a minute is blocked"""
        # Send 5 requests quickly
        for i in range(5):
            self.client.post('/chats/messages/send/', {
                'message': f'Test message {i}',
                'conversation_id': 1
            }, content_type='application/json')
        
        # 6th request should be blocked
        response = self.client.post('/chats/messages/send/', {
            'message': 'This should be blocked',
            'conversation_id': 1
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Rate limit exceeded', response.content)
    
    def test_rate_limit_resets_after_time(self):
        """Test that rate limit resets after the time window"""
        # Send 5 requests
        for i in range(5):
            self.client.post('/chats/messages/send/', {
                'message': f'Test message {i}',
                'conversation_id': 1
            }, content_type='application/json')
        
        # Wait for rate limit window to expire
        # Note: In real testing, you might want to mock time
        time.sleep(61)  # Wait 61 seconds
        
        # Should be able to send again
        response = self.client.post('/chats/messages/send/', {
            'message': 'After timeout',
            'conversation_id': 1
        }, content_type='application/json')
        
        self.assertNotEqual(response.status_code, 403)
    
    def test_rate_limit_only_applies_to_post(self):
        """Test that rate limit only applies to POST requests"""
        # Send many GET requests (should not be limited)
        for i in range(10):
            response = self.client.get('/chats/')
            self.assertNotEqual(response.status_code, 403)
    
    def test_rate_limit_tracks_different_ips_separately(self):
        """Test that different IPs are tracked separately"""
        # First IP sends 5 requests
        for i in range(5):
            self.client.post('/chats/messages/send/', {
                'message': f'Test {i}',
                'conversation_id': 1
            }, content_type='application/json')
        
        # Simulate different IP by creating new client
        # (In real scenario, you'd set REMOTE_ADDR)
        new_client = Client()
        response = new_client.post('/chats/messages/send/', {
            'message': 'From different IP',
            'conversation_id': 1
        }, content_type='application/json', 
        HTTP_X_FORWARDED_FOR='192.168.1.100')
        
        # Should not be blocked (different IP)
        self.assertNotEqual(response.status_code, 403)


class RolePermissionMiddlewareTest(TestCase):
    """Test cases for Task 4: Role-Based Permissions"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        self.moderator_user = User.objects.create_user(
            username='moderator',
            password='mod123'
        )
        # Set moderator permissions
        from django.contrib.auth.models import Permission
        self.moderator_user.user_permissions.add(
            Permission.objects.get(codename='delete_message'),
            Permission.objects.get(codename='moderate_conversation')
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            password='user123'
        )
    
    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users cannot delete"""
        response = self.client.delete('/chats/messages/1/delete/')
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Authentication required', response.content)
    
    def test_regular_user_denied(self):
        """Test that regular users cannot delete"""
        self.client.login(username='regular', password='user123')
        response = self.client.delete('/chats/messages/1/delete/')
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Only admins and moderators', response.content)
    
    def test_admin_user_allowed(self):
        """Test that admin users can delete"""
        # Create a test message
        from chats.models import Message, Conversation
        conversation = Conversation.objects.create(user1=self.admin_user, user2=self.regular_user)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.regular_user,
            content='Test message'
        )
        
        self.client.login(username='admin', password='admin123')
        response = self.client.delete(f'/chats/messages/{message.id}/delete/')
        self.assertEqual(response.status_code, 200)  # or whatever success code you expect
        self.assertFalse(Message.objects.filter(id=message.id).exists())
    
    def test_moderator_user_allowed(self):
        """Test that moderator users can delete"""
        self.client.login(username='moderator', password='mod123')
        response = self.client.delete('/chats/messages/1/delete/')
        # Should not be 403
        self.assertNotEqual(response.status_code, 403)
    
    def test_regular_paths_not_restricted(self):
        """Test that regular paths are not restricted"""
        self.client.login(username='regular', password='user123')
        response = self.client.get('/chats/')
        self.assertEqual(response.status_code, 200)
    
    def test_moderation_endpoint_restricted(self):
        """Test that moderation endpoints are restricted"""
        self.client.login(username='regular', password='user123')
        response = self.client.post('/chats/conversations/1/moderate/', {
            'action': 'warn'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 403)


class MiddlewareIntegrationTest(TestCase):
    """Integration tests for all middleware working together"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        # Clean log file
        if os.path.exists('requests.log'):
            os.remove('requests.log')
    
    def test_all_middleware_execute_in_order(self):
        """Test that all middleware execute properly"""
        # Make a request that goes through all middleware
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/chats/')
        
        # Check request was logged (Task 1)
        self.assertTrue(os.path.exists('requests.log'))
        
        # Response should be successful if within time
        # (Can't easily test time restriction here without mocking)
        self.assertIn(response.status_code, [200, 403])
    
    def test_middleware_short_circuits_correctly(self):
        """Test that middleware can block requests early"""
        # Send requests to trigger rate limit
        for i in range(6):
            response = self.client.post('/chats/messages/send/', {
                'message': f'Test {i}',
                'conversation_id': 1
            }, content_type='application/json')
        
        # Last request should be blocked by rate limiting
        self.assertEqual(response.status_code, 403)
        
        # But it should still be logged
        with open('requests.log', 'r') as f:
            log_content = f.read()
        self.assertIn('/chats/messages/send/', log_content)
    
    def test_admin_bypasses_no_restrictions(self):
        """Test that being admin doesn't bypass time/rate restrictions"""
        self.client.login(username='admin', password='admin123')
        
        # Rate limiting should still apply
        for i in range(6):
            response = self.client.post('/chats/messages/send/', {
                'message': f'Test {i}',
                'conversation_id': 1
            }, content_type='application/json')
        
        # Admin should still be rate limited
        self.assertEqual(response.status_code, 403)


# Run tests with: python manage.py test chats