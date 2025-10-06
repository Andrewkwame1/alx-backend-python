from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsParticipantOfConversation(BasePermission):
    """
    Custom permission to only allow participants of a conversation to access it.
    This permission class ensures that only participants can access, modify,
    or delete messages and conversations they are part of.
    """

    def has_permission(self, request, view):
        """
        Initial permission check.
        Ensure user is authenticated and allow create operations.
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow creating new conversations/messages
        if request.method == 'POST':
            return True

        return True  # Further checks in has_object_permission

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.
        Allow access only to conversation participants.
        For messages, check both sender and conversation participant status.
        """
        # For conversation objects
        if hasattr(obj, 'user1') and hasattr(obj, 'user2'):
            return request.user in [obj.user1, obj.user2]

        # For message objects
        if hasattr(obj, 'conversation'):
            conversation = obj.conversation
            is_participant = request.user in [conversation.user1, conversation.user2]
            
            # For safe methods (GET, HEAD, OPTIONS), being a participant is enough
            if request.method in permissions.SAFE_METHODS:
                return is_participant
                
            # For modify/delete operations, must be the sender
            if request.method in ['PUT', 'PATCH', 'DELETE']:
                return obj.sender == request.user
                
            return is_participant

        return False


class IsMessageSender(BasePermission):
    """
    Custom permission to only allow message senders to edit/delete their messages.
    This permission is more strict than IsParticipantOfConversation as it only
    allows the original sender to modify messages.
    """

    def has_permission(self, request, view):
        """
        Initial permission check.
        Only allow authenticated users.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.
        Allow read access to conversation participants,
        but restrict modifications to the message sender.
        """
        # First check if user is a conversation participant
        if hasattr(obj, 'conversation'):
            is_participant = request.user in [
                obj.conversation.user1,
                obj.conversation.user2
            ]
            
            # For safe methods, being a participant is enough
            if request.method in permissions.SAFE_METHODS:
                return is_participant

            # For modifications, must be the sender
            return obj.sender == request.user

        return False


class IsOwnerOrParticipant(BasePermission):
    """
    Custom permission combining ownership and participation rights.
    This permission is useful for operations that should be allowed for
    both the owner/sender and participants of a conversation.
    """

    def has_permission(self, request, view):
        """
        Initial permission check.
        Only allow authenticated users.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.
        Allow access if user is either the owner/sender or a participant.
        """
        # For message objects
        if hasattr(obj, 'sender') and hasattr(obj, 'conversation'):
            return (
                obj.sender == request.user or
                request.user in [obj.conversation.user1, obj.conversation.user2]
            )

        # For conversation objects
        if hasattr(obj, 'user1') and hasattr(obj, 'user2'):
            return request.user in [obj.user1, obj.user2]

        return False


class IsMessageSender(BasePermission):
    """
    Custom permission to only allow the sender of a message to modify/delete it.
    """
    def has_object_permission(self, request, view, obj):
        # obj is a Message instance
        # Allow sender or staff to modify
        return obj.sender == request.user or request.user.is_staff

class IsConversationParticipant(permissions.BasePermission):
    """
    Custom permission to only allow participants of a conversation to access messages.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for conversation participants
        if request.method in permissions.SAFE_METHODS:
            return request.user in [obj.conversation.user1, obj.conversation.user2]

        # Write permissions (PUT, PATCH, DELETE) only for message sender
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return obj.sender == request.user

        return False

    def has_permission(self, request, view):
        # For creating new messages, check if user is part of conversation
        if request.method == 'POST':
            conversation_id = request.data.get('conversation')
            if not conversation_id:
                return False

            try:
                conversation = view.get_queryset().first().conversation.__class__.objects.get(id=conversation_id)
                return request.user in [conversation.user1, conversation.user2]
            except:
                return False

        return True