from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

# Try to import DRF components, but don't fail if not installed
try:
    from rest_framework import viewsets, status
    from rest_framework.decorators import action
    from rest_framework.response import Response
    from .permissions import IsParticipantOfConversation, IsMessageSender
    DRF_AVAILABLE = True
except ImportError:
    DRF_AVAILABLE = False

# Try to import models
try:
    from .models import Message, Conversation
    from django.contrib.auth import get_user_model
    User = get_user_model()
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False


def chat_home(request):
    """
    Home page for chat application
    """
    return JsonResponse({
        'message': 'Welcome to Chat Application',
        'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
        'path': request.path,
        'method': request.method,
    })


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """
    Endpoint to send a message (tests rate limiting middleware)
    """
    try:
        data = json.loads(request.body)
        message_content = data.get('message', '')
        conversation_id = data.get('conversation_id')
        
        if not message_content:
            return JsonResponse({
                'error': 'Message content is required'
            }, status=400)
        
        # For testing purposes without database
        return JsonResponse({
            'status': 'success',
            'message': 'Message sent successfully',
            'content': message_content,
            'conversation_id': conversation_id,
            'sender': str(request.user) if request.user.is_authenticated else 'Anonymous'
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_messages(request, conversation_id=None):
    """
    Endpoint to retrieve messages
    """
    if not MODELS_AVAILABLE:
        return JsonResponse({
            'message': 'Mock response - models not configured',
            'conversation_id': conversation_id,
            'messages': []
        })
    
    if conversation_id:
        try:
            messages = Message.objects.filter(
                conversation_id=conversation_id,
                is_deleted=False
            ).select_related('sender')
            
            return JsonResponse({
                'conversation_id': conversation_id,
                'messages': [
                    {
                        'id': msg.id,
                        'sender': msg.sender.username,
                        'content': msg.content,
                        'created_at': msg.created_at.isoformat()
                    }
                    for msg in messages
                ]
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({
        'error': 'Please provide conversation_id'
    }, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_message(request, message_id):
    """
    Endpoint to delete a message (tests role permission middleware)
    This should only be accessible to admins/moderators
    """
    if not MODELS_AVAILABLE:
        return JsonResponse({
            'status': 'success',
            'message': f'Mock delete - Message {message_id} would be deleted',
            'deleted_by': str(request.user)
        })
    
    try:
        message = get_object_or_404(Message, id=message_id)
        # Tests expect the message to be removed from the DB
        message.delete()

        return JsonResponse({
            'status': 'success',
            'message': f'Message {message_id} deleted successfully',
            'deleted_by': str(request.user)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def moderate_conversation(request, conversation_id):
    """
    Endpoint for conversation moderation (tests role permission middleware)
    This should only be accessible to admins/moderators
    """
    try:
        data = json.loads(request.body)
        action = data.get('action', '')
        
        return JsonResponse({
            'status': 'success',
            'message': f'Moderation action "{action}" applied to conversation {conversation_id}',
            'moderated_by': str(request.user)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
def test_middleware(request):
    """
    Test endpoint to verify all middleware is working
    """
    middleware_status = {
        'request_logging': 'Check requests.log file',
        'time_restriction': 'Active - Access restricted outside 9 AM - 6 PM',
        'rate_limiting': 'Active - Max 5 POST requests per minute',
        'role_permission': 'Active - Admin/Moderator only for DELETE operations',
        'current_user': str(request.user),
        'is_authenticated': request.user.is_authenticated,
        'user_role': getattr(request.user, 'role', 'N/A') if request.user.is_authenticated else 'N/A',
        'is_admin': request.user.is_staff if request.user.is_authenticated else False,
        'ip_address': request.META.get('REMOTE_ADDR', 'Unknown')
    }
    
    return JsonResponse(middleware_status)


def access_denied(request):
    """
    Custom access denied page
    """
    return JsonResponse({
        'error': 'Access Denied',
        'message': 'You do not have permission to access this resource'
    }, status=403)


# DRF ViewSets (only if DRF is available)
if DRF_AVAILABLE and MODELS_AVAILABLE:
    try:
        from rest_framework import serializers

        # Try to import existing serializers; if missing, provide minimal ones
        try:
            from .serializers import ConversationSerializer, MessageSerializer, UserSerializer
        except Exception:
            class UserSerializer(serializers.ModelSerializer):
                class Meta:
                    model = User
                    fields = ['id', 'username', 'email']

            class MessageSerializer(serializers.ModelSerializer):
                sender = UserSerializer(read_only=True)

                class Meta:
                    model = Message
                    fields = ['id', 'conversation', 'sender', 'content', 'sent_at']

            class ConversationSerializer(serializers.ModelSerializer):
                class Meta:
                    model = Conversation
                    fields = ['id', 'user1', 'user2', 'created_at']

        class ConversationViewSet(viewsets.ModelViewSet):
            queryset = Conversation.objects.all()
            serializer_class = ConversationSerializer
            permission_classes = [IsParticipantOfConversation]

        class MessageViewSet(viewsets.ModelViewSet):
            queryset = Message.objects.all()
            serializer_class = MessageSerializer
            permission_classes = [IsMessageSender]

        class UserViewSet(viewsets.ReadOnlyModelViewSet):
            queryset = User.objects.all()
            serializer_class = UserSerializer

    except Exception as e:
        print(f"Warning: Could not create ViewSets: {e}")