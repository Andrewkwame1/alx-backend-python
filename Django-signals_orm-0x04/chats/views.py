# chats/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, UserSerializer
from .permissions import IsParticipantOfConversation, IsMessageSender
from .filters import MessageFilter
from .pagination import CustomPageNumberPagination

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']

    def get_queryset(self):
        """
        Filter users to exclude the current user and only show active users.
        """
        return User.objects.filter(is_active=True).exclude(id=self.request.user.id)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        """
        Return conversations where the current user is a participant.
        """
        return Conversation.objects.filter(
            participants=self.request.user
        ).distinct().order_by('-updated_at')

    def perform_create(self, serializer):
        """
        Create a new conversation and add the current user as a participant.
        """
        conversation = serializer.save(created_by=self.request.user)
        conversation.participants.add(self.request.user)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """
        Add a participant to the conversation.
        """
        conversation = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
            conversation.participants.add(user)
            return Response(
                {'message': f'User {user.username} added to conversation'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages with pagination and filtering implemented.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]

    # FILTERING IMPLEMENTATION - Using MessageFilter as requested
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MessageFilter  # This is the MessageFilter class as requested
    search_fields = ['content']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    # PAGINATION IMPLEMENTATION - 20 messages per page as requested
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        """
        Return messages from conversations where the current user is a participant.
        """
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related('conversation', 'sender').order_by('-timestamp')

    def perform_create(self, serializer):
        """
        Create a new message with the current user as sender.
        """
        serializer.save(sender=self.request.user)

    def get_permissions(self):
        """
        Apply different permissions based on the action.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only message sender can edit/delete their messages
            permission_classes = [IsAuthenticated, IsMessageSender]
        else:
            # Default permissions - IsParticipantOfConversation as requested
            permission_classes = [IsAuthenticated, IsParticipantOfConversation]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60))
    def conversation_messages(self, request):
        """
        Get paginated messages for a specific conversation with filtering support.
        Cached for 60 seconds.
        """
        conversation_id = request.query_params.get('conversation_id')

        if not conversation_id:
            return Response(
                {'error': 'conversation_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            conversation = Conversation.objects.get(id=conversation_id)

            # Check if user is participant (permission check)
            if request.user not in conversation.participants.all():
                return Response(
                    {'error': 'You are not a participant of this conversation'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get messages for the conversation
            messages = Message.objects.filter(
                conversation=conversation
            ).select_related('sender').order_by('-timestamp')

            # Apply the MessageFilter for filtering
            filtered_messages = MessageFilter(request.GET, queryset=messages).qs

            # Apply pagination (20 messages per page)
            page = self.paginate_queryset(filtered_messages)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(filtered_messages, many=True)
            return Response(serializer.data)

        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def filter_by_user(self, request):
        """
        Custom endpoint to retrieve conversations with specific users.
        """
        user_id = request.query_params.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_user = User.objects.get(id=user_id)

            # Get messages from conversations that include both current user and target user
            messages = self.get_queryset().filter(
                conversation__participants=target_user
            )

            # Apply pagination
            page = self.paginate_queryset(messages)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(messages, many=True)
            return Response(serializer.data)

        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def filter_by_time_range(self, request):
        """
        Custom endpoint to retrieve messages within a time range.
        """
        time_range = request.query_params.get('time_range')

        if not time_range:
            return Response(
                {'error': 'time_range parameter is required (today, yesterday, last_week, last_month, last_year)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use the MessageFilter to filter by time range
        messages = self.get_queryset()
        filtered_messages = MessageFilter({'time_range': time_range}, queryset=messages).qs

        # Apply pagination
        page = self.paginate_queryset(filtered_messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(filtered_messages, many=True)
        return Response(serializer.data)