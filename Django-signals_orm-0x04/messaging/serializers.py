from rest_framework import serializers
from .models import User, Conversation, Message
from rest_framework.exceptions import ValidationError
import uuid
import re

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=255)
    phone_number = serializers.CharField(max_length=20, allow_null=True, allow_blank=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
    
    # full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['user_id', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'created_at', 'updated_at']
        read_only_fields = ["user_id", "created_at", "updated_at"]
        extra_kwargs = {"email": {"required": True}}
     
    def get_full_name(self, obj):
        # Custom method to generate the full name dynamically
        return f'{obj.first_name} {obj.last_name}' 
     
    def validate_first_name(self, value):
         # Ensure first name is not empty and contains only alphabets
         if not value.isalpha():
             raise serializers.ValidationError('First name must contain only alphabetic characters.')
         return value
    
    def validate_last_name(self, value):
         # Ensure last name is not empty and contains only alphabets
         if not value.isalpha():
             raise serializers.ValidationError('Last name must contain only alphabetic characters.')
         return value 
        
    def validate_email(self, value):
        # Check if the email already exists in the database
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email is already in use.')
        return value
    
    # def validate_phone_number(self, value):
    #     # Validate phone number format using a regex.
    #     if value and not re.match(r'^\+?1?\d{9, 15}$', value):
    #         raise serializers.ValidationError('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
    #     return value
    
    def validate_role(self, value):
        # Ensure the role is one of the predifined choices
        if value not in dict(User.ROLE_CHOICES).keys():
            raise serializers.ValidationError(f'Role must be on of the following: {list(dict(User.ROLE_CHOICES).keys())}')
        return value
    
    def validate(self, data):
        # Object-level validation for complex logic involving multiple fields
        if not data.get('first_name') or not data.get('last_name'):
            raise serializers.ValidationError('Both first name and last name are required.')
        return data
        

        
# Message Serializer
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True)
    message_body_text = serializers.CharField(source="message_body", read_only=True)
    sender_email = serializers.SerializerMethodField()
    formatted_sent_at = serializers.SerializerMethodField()
    conversation = serializers.PrimaryKeyRelatedField(queryset=Conversation.objects.all(), write_only=True)

    
    class Meta:
        model = Message
        fields = ['message_id', 'sender', 'sender_id', 'conversation', 'message_body', 'message_body_text', 'formatted_sent_at', 'sent_at']
        read_only_fields = ['message_id', 'sent_at'] 
    
    def get_sender_email(self, obj):
        """Get sender's email address."""
        return obj.sender.email
    
    def get_formatted_sent_at(self, obj):
        """Format the sent_at timestamp for display."""
        return obj.sent_at.strftime('%Y-%m-%d %H:%M:%S') if obj.sent_at else None      


# Conversation Serializer
class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['conversation_id', 'participants', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['conversation_id', 'created_at', 'updated_at'] 
        
        
    def validate_conversation(self, value):
        # Custom validation to check if the user is a participant
        if self.context['request'].user not in value.participants.all():
            raise serializers.ValidationError('User is not a participant in this conversation.')
        return value               
        
                