from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Message, MessageHistory
from .serializers import MessageSerializer, MessageHistorySerializer

@login_required
def delete_user(request):
    """View to allow users to delete their own account"""
    if request.method == 'POST':
        user = request.user
        # Logout the user before deletion
        from django.contrib.auth import logout
        logout(request)
        # Delete the user account
        user.delete()
        django_messages.success(request, 'Your account has been successfully deleted.')
        return redirect('home')
    
    return render(request, 'messaging/delete_user_confirm.html')


@cache_page(60)
@login_required
def unread_messages(request):
    """Display only unread messages in user's inbox using the unread manager"""
    user = request.user
    # Use the unread manager to display only unread messages in user's inbox
    messages_queryset = Message.unread.unread_for_user(user)
    
    return JsonResponse({
        'unread_messages': MessageSerializer(messages_queryset, many=True).data,
        'count': messages_queryset.count()
    })


@cache_page(60)
@login_required
def message_list(request):
    """List all messages for the authenticated user with optimized queries"""
    sender = request.user
    receiver = request.GET.get('receiver', None)
    
    # Use the unread manager to display only unread messages in user's inbox
    messages_queryset = Message.unread.for_user(sender)
    
    if receiver:
        messages_queryset = messages_queryset.filter(
            sender__username=receiver
        ).select_related('sender', 'receiver', 'parent_message').only(
            'id', 'sender__username', 'receiver__username', 'content', 'timestamp', 'read'
        )
    
    return JsonResponse({
        'messages': MessageSerializer(messages_queryset, many=True).data,
        'count': messages_queryset.count()
    })


@cache_page(60)
@login_required
def user_messages(request):
    """Get all messages for the authenticated user with optimized prefetch and select related"""
    receiver = request.GET.get('receiver', None)
    
    # Filter messages where current user is sender with optimizations
    if receiver:
        messages_queryset = Message.objects.filter(
            sender=request.user,
            receiver__username=receiver
        ).select_related('sender', 'receiver', 'parent_message').prefetch_related('messagehistory_set')
    else:
        messages_queryset = Message.objects.filter(
            sender=request.user
        ).select_related('sender', 'receiver', 'parent_message').prefetch_related('messagehistory_set')
    
    return JsonResponse({
        'messages': MessageSerializer(messages_queryset, many=True).data,
        'count': messages_queryset.count()
    })


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for Message operations with optimized queries"""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get messages optimized with select_related and prefetch_related"""
        sender = self.request.user
        receiver = self.request.query_params.get('receiver', None)
        
        queryset = Message.objects.filter(
            sender=sender
        ).select_related('sender', 'receiver', 'parent_message').prefetch_related('messagehistory_set')
        
        if receiver:
            queryset = queryset | Message.objects.filter(
                receiver=self.request.user,
                sender__username=receiver
            ).select_related('sender', 'receiver', 'parent_message').prefetch_related('messagehistory_set')
        
        return queryset
    
    @method_decorator(cache_page(60))
    def list(self, request, *args, **kwargs):
        """List messages with caching"""
        return super().list(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def edit_history(self, request, pk=None):
        """Get edit history for a message"""
        message = self.get_object()
        history = MessageHistory.objects.filter(message=message)
        serializer = MessageHistorySerializer(history, many=True)
        return Response(serializer.data)