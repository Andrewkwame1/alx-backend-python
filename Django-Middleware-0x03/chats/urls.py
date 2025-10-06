from django.urls import path
from . import views


urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/<int:conversation_id>/', views.get_messages, name='get_messages'),
    path('messages/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('conversations/<int:conversation_id>/moderate/', views.moderate_conversation, name='moderate_conversation'),
    path('test-middleware/', views.test_middleware, name='test_middleware'),
]

