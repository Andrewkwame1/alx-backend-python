from rest_framework import serializers
from .models import User, Conversation, Message


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """
    full_name = serializers.SerializerMethodField()
    display_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['user_id', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'created_at', 'full_name', 'display_name']
        read_only_fields = ['user_id', 'created_at']

    def get_full_name(self, obj):
        """
        Return the user's full name.
        """
        return f"{obj.first_name} {obj.last_name}".strip()

    def validate_email(self, value):
        """
        Validate email format and uniqueness.
        """
        if not value:
            raise serializers.ValidationError("Email is required.")
        return value


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Message model.
    """
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['message_id', 'sender', 'conversation', 'message_body', 'sent_at', 'sender_name']
        read_only_fields = ['message_id', 'sender', 'sent_at']

    def get_sender_name(self, obj):
        """
        Return the sender's full name.
        """
        return f"{obj.sender.first_name} {obj.sender.last_name}".strip()

    def validate_message_body(self, value):
        """
        Validate message body is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Message body cannot be empty.")
        return value.strip()


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Conversation model.
    Includes nested relationships for participants and messages.
    """
    messages = MessageSerializer(many=True, read_only=True)
    participants = UserSerializer(many=True, read_only=True)
    participant_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['conversation_id', 'participants', 'messages', 'created_at', 'participant_count', 'last_message']
        read_only_fields = ['conversation_id', 'created_at']

    def get_participant_count(self, obj):
        """
        Return the number of participants in the conversation.
        """
        return obj.participants.count()

    def get_last_message(self, obj):
        """
        Return the last message in the conversation.
        """
        last_message = obj.messages.first()  # Using first() since ordering is by -sent_at
        if last_message:
            return {
                'message_id': str(last_message.message_id),
                'message_body': last_message.message_body,
                'sender': last_message.sender.email,
                'sent_at': last_message.sent_at
            }
        return None

    def validate(self, data):
        """
        Validate conversation data.
        """
        if hasattr(self, 'initial_data'):
            participants = self.initial_data.get('participants', [])
            if len(participants) < 2:
                raise serializers.ValidationError("A conversation must have at least 2 participants.")
        return data