# chats/filters.py

from django_filters import rest_framework as filters
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

from .models import Message, Conversation

User = get_user_model()


class MessageFilter(filters.FilterSet):
    """
    MessageFilter class as requested to retrieve conversations with specific users
    or messages within a time range.
    """

    # Filter by conversation
    conversation = filters.ModelChoiceFilter(
        queryset=Conversation.objects.all(),
        help_text="Filter messages by conversation ID"
    )

    # Filter by sender (specific user)
    sender = filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        help_text="Filter messages by sender user ID"
    )

    # Filter by sender username - for retrieving conversations with specific users
    sender_username = filters.CharFilter(
        field_name='sender__username',
        lookup_expr='icontains',
        help_text="Retrieve conversations with specific users by username"
    )

    # Time range filters - messages within a time range
    sent_at_after = filters.DateTimeFilter(
        field_name='sent_at',
        lookup_expr='gte',
        help_text="Messages within time range - after this timestamp"
    )

    sent_at_before = filters.DateTimeFilter(
        field_name='sent_at',
        lookup_expr='lte',
        help_text="Messages within time range - before this timestamp"
    )

    # Date filters (without time)
    date_after = filters.DateFilter(
        field_name='sent_at__date',
        lookup_expr='gte',
        help_text="Messages after this date (YYYY-MM-DD)"
    )

    date_before = filters.DateFilter(
        field_name='sent_at__date',
        lookup_expr='lte',
        help_text="Messages before this date (YYYY-MM-DD)"
    )

    # Content search
    message_body = filters.CharFilter(
        field_name='message_body',
        lookup_expr='icontains',
        help_text="Search messages by content"
    )

    # Predefined time range filters
    TIME_RANGE_CHOICES = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('last_week', 'Last 7 days'),
        ('last_month', 'Last 30 days'),
        ('last_year', 'Last year'),
    ]

    time_range = filters.ChoiceFilter(
        choices=TIME_RANGE_CHOICES,
        method='filter_time_range',
        help_text="Filter messages within predefined time ranges"
    )

    # Filter messages from conversations with specific users
    conversation_with_user = filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        method='filter_conversation_with_user',
        help_text="Retrieve conversations with specific users"
    )

    def filter_time_range(self, queryset, name, value):
        """
        Custom method to filter messages within a time range using predefined options.
        """
        now = timezone.now()

        if value == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(sent_at__gte=start_date)

        if value == 'yesterday':
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            return queryset.filter(sent_at__range=[start_date, end_date])

        if value == 'last_week':
            start_date = now - timedelta(days=7)
            return queryset.filter(sent_at__gte=start_date)

        if value == 'last_month':
            start_date = now - timedelta(days=30)
            return queryset.filter(sent_at__gte=start_date)

        if value == 'last_year':
            start_date = now - timedelta(days=365)
            return queryset.filter(sent_at__gte=start_date)

        return queryset

    def filter_conversation_with_user(self, queryset, name, value):
        """
        Custom method to retrieve conversations with specific users.
        """
        if value:
            # Get all conversations that include the specified user
            conversation_ids = Conversation.objects.filter(
                participants=value
            ).values_list('conversation_id', flat=True)

            # Return messages from those conversations
            return queryset.filter(conversation_id__in=conversation_ids)

        return queryset

    class Meta:
        model = Message
        fields = {
            'sent_at': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'message_body': ['icontains', 'exact'],
        }