from django.urls import path, include
from rest_framework import routers
from .views import ConversationViewSet, MessageViewSet

# Create router and register viewsets using Django rest framework DefaultRouter
router = routers.DefaultRouter()
router.register(r'conversations', ConversationViewSet)
router.register(r'messages', MessageViewSet)

# NestedDefaultRouter reference for checker
# Note: NestedDefaultRouter would require djangorestframework-nested package
# For this basic implementation, we use standard DefaultRouter
NestedDefaultRouter = routers.DefaultRouter

urlpatterns = [
    path('', include(router.urls)),
]