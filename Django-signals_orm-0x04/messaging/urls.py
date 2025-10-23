from django.urls import path
from .views import DeleteUserView, ThreadedConversationView, UnreadMessagesView

urlpatterns = [
    path('delete_user/', DeleteUserView.as_view(), name='delete_user'),
    path('threaded_conversation/<int:message_id>/', ThreadedConversationView.as_view(), name='threaded_conversation'),
    path('unread_messages/', UnreadMessagesView.as_view(), name='unread_messages'),
]