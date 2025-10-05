from rest_framework import permissions


class IsParticipantOfConversation(BasePermission):
    """
    Custom permission to only allow participants of a conversation to access it.
    This is the main permission class as requested in the requirements.
    """

    def has_permission(self, request, view):
        """
        Return True if the user is authenticated.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission to only allow participants of a conversation
        to view, edit, or delete messages/conversations.
        """
        # For conversation objects
        if hasattr(obj, 'participants'):
            return request.user in obj.participants.all()

        # For message objects - check if user is participant of the conversation
        if hasattr(obj, 'conversation'):
            return request.user in obj.conversation.participants.all()

        # For other objects, deny access by default
        return False


class IsMessageSender(BasePermission):
    """
    Custom permission to only allow message senders to edit/delete their messages.
    """

    def has_permission(self, request, view):
        """
        Return True if the user is authenticated.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission to only allow message senders to edit/delete.
        """
        # Allow read permissions for any authenticated user who is a participant
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'conversation'):
                return request.user in obj.conversation.participants.all()
            return False

        # Write permissions only for the message sender
        return obj.sender == request.user


class IsOwnerOrParticipant(BasePermission):
    """
    Custom permission to only allow owners or participants to access objects.
    """

    def has_permission(self, request, view):
        """
        Return True if the user is authenticated.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission to only allow owners or participants.
        """
        # If the object has a sender field (like messages)
        if hasattr(obj, 'sender'):
            return obj.sender == request.user

        # If the object has participants (like conversations)
        if hasattr(obj, 'participants'):
            return request.user in obj.participants.all()

        # For message objects
        if hasattr(obj, 'conversation'):
            return (obj.sender == request.user or
                    request.user in obj.conversation.participants.all())

        return False


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