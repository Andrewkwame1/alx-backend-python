import logging
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin

# Configure logging for request logs
logger = logging.getLogger('request_logger')
logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler('requests.log')
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)


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
        log_message = f"{datetime.now()} - User: {user} - Path: {request.path}"
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
        
        # Get current hour (24-hour format)
        current_hour = datetime.now().hour
        
        # Check if request is to chat-related paths
        if request.path.startswith('/chats/') or request.path.startswith('/api/chats/'):
            # Restrict access outside 9 AM (9) to 6 PM (18)
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
        # Dictionary to track message counts per IP
        # Structure: {ip_address: [(timestamp1, timestamp2, ...)]}
        self.message_counts = {}
    
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
            
            # Initialize IP tracking if not exists
            if ip_address not in self.message_counts:
                self.message_counts[ip_address] = []
            
            # Filter out timestamps older than 1 minute
            one_minute_ago = current_time.timestamp() - 60
            self.message_counts[ip_address] = [
                timestamp for timestamp in self.message_counts[ip_address]
                if timestamp > one_minute_ago
            ]
            
            # Check if user has exceeded the limit (5 messages per minute)
            if len(self.message_counts[ip_address]) >= 5:
                return HttpResponseForbidden(
                    "Rate limit exceeded. You can only send 5 messages per minute. Please try again later."
                )
            
            # Add current timestamp to the list
            self.message_counts[ip_address].append(current_time.timestamp())
        
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
            # Assuming your User model has a 'role' field
            user_role = getattr(request.user, 'role', None)
            
            # Also check Django's built-in staff/superuser status
            is_admin = request.user.is_superuser or request.user.is_staff
            is_moderator = user_role in ['admin', 'moderator'] if user_role else False
            
            if not (is_admin or is_moderator):
                return HttpResponseForbidden(
                    "Access denied. Only admins and moderators can perform this action."
                )
        
        # Process the request
        response = self.get_response(request)
        return response