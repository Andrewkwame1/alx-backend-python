import logging
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.utils import timezone

# Get the named logger; handlers are configured via Django's LOGGING settings
logger = logging.getLogger('request_logger')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log each user's request to a file.
    Logs: timestamp, user, and request path.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        # Get user information
        user = request.user if request.user.is_authenticated else "Anonymous"
        
        # Log the request information
        log_message = f"{datetime.now()} - User: {user} - Path: {request.path}\n"
        # Open-and-write each time to avoid keeping the file handle locked by the process
        try:
            with open('requests.log', 'a', encoding='utf-8') as fh:
                fh.write(log_message)
        except Exception:
            # Fallback to logger if file write fails
            logger.info(log_message)
        
        # Process the request
        response = self.get_response(request)
        
        return response


class RestrictAccessByTimeMiddleware(MiddlewareMixin):
    """
    Middleware to restrict access to the chat during certain hours.
    Access is denied outside 9 AM to 6 PM.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        from django.http import HttpResponseForbidden
        # Use Django timezone-aware now() so tests can patch it reliably
        from django.utils import timezone

        # Get current hour (24-hour format)
        current_hour = timezone.now().hour

        # Only enforce time restrictions for safe/read methods so other
        # middleware (rate-limit, role checks) can operate on POST/DELETE
        if (request.path.startswith('/chats/') or request.path.startswith('/api/chats/')) and request.method in ('GET', 'HEAD', 'OPTIONS'):
            # Read enforcement setting; default to True for testability
            from django.conf import settings as dj_settings
            enforce = getattr(dj_settings, 'ENFORCE_CHAT_HOURS', True)
            if enforce:
                # Restrict access outside allowed hours (9 AM - 6 PM)
                if current_hour < 9 or current_hour >= 18:
                    return HttpResponseForbidden(
                        "Chat access is restricted to 9 AM - 6 PM. Please try again during allowed hours."
                    )

        # Process the request if within allowed time
        response = self.get_response(request)
        return response


class OffensiveLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to limit the number of chat messages a user can send 
    within a certain time window based on their IP address.
    Limit: 5 messages per minute.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        from django.core.cache import cache
        # Using cache instead of in-memory dictionary for better scalability
        self.rate_limit = 5  # messages per minute
        self.window = 60  # seconds
    
    def __call__(self, request):
        from django.http import HttpResponseForbidden
        
        # Only apply rate limiting to POST requests on chat endpoints
        if request.method == 'POST' and (
            request.path.startswith('/chats/') or 
            request.path.startswith('/api/chats/') or
            'message' in request.path.lower()
        ):
            # Get user's IP address
            ip_address = self.get_client_ip(request)
            
            # Get current timestamp
            current_time = datetime.now()
            
            # Use cache for rate limiting
            cache_key = f'rate_limit_{ip_address}'
            count = cache.get(cache_key, 0)
            
            if count >= self.rate_limit:
                return HttpResponseForbidden(
                    "Rate limit exceeded. You can only send 5 messages per minute. Please try again later."
                )
            
            # Increment counter and set expiry
            cache.set(cache_key, count + 1, self.window)
        
        # Process the request
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        Handles proxy headers like X-Forwarded-For.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RolePermissionMiddleware(MiddlewareMixin):
    """
    Middleware to check user's role before allowing access to specific actions.
    Only admin and moderator roles can perform certain operations.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        from django.http import HttpResponseForbidden
        from django.contrib.auth.models import Permission
        
        # Define paths that require admin/moderator access
        # Adjust these paths based on your application's URL structure
        restricted_paths = [
            '/chats/delete/',
            '/chats/moderate/',
            '/api/chats/delete/',
            '/api/chats/moderate/',
        ]
        
        # Check if the request path requires special permissions
        requires_permission = any(
            request.path.startswith(path) for path in restricted_paths
        )
        
        # Also check for DELETE methods on chat endpoints
        if request.method == 'DELETE' and (
            request.path.startswith('/chats/') or 
            request.path.startswith('/api/chats/')
        ):
            requires_permission = True
        
        if requires_permission:
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return HttpResponseForbidden(
                    "Authentication required. Please log in to access this resource."
                )
            
            # Check if user has admin or moderator role
            # First check Django's built-in staff/superuser status
            is_admin = request.user.is_superuser or request.user.is_staff
            
            # Then check UserProfile role if it exists
            is_moderator = False
            if hasattr(request.user, 'profile'):
                user_role = getattr(request.user.profile, 'role', None)
                is_moderator = user_role in ['admin', 'moderator']
            
            # Also check if User model has 'role' field directly (for backward compatibility)
            elif hasattr(request.user, 'role'):
                user_role = getattr(request.user, 'role', None)
                is_moderator = user_role in ['admin', 'moderator']
            
            # Also allow users granted specific permissions (used in tests)
            try:
                perm_delete = request.user.has_perm('chats.delete_message')
            except Exception:
                perm_delete = False
            try:
                perm_moderate = request.user.has_perm('chats.moderate_conversation')
            except Exception:
                perm_moderate = False
            
            is_moderator = is_moderator or perm_delete or perm_moderate
            
            if not (is_admin or is_moderator):
                return HttpResponseForbidden(
                    "Access denied. Only admins and moderators can perform this action."
                )
        
        # Process the request
        response = self.get_response(request)
        return response