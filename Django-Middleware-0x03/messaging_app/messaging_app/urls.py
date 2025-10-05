# messaging_app/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from chats.views import ConversationViewSet, MessageViewSet, UserViewSet
from chats.auth import (
    CustomTokenObtainPairView,
    register_user,
    login_user,
    logout_user
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'users', UserViewSet)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API routes with pagination and filtering
    path('api/v1/', include(router.urls)),

    # Authentication endpoints
    path('api/v1/auth/register/', register_user, name='register'),
    path('api/v1/auth/login/', login_user, name='login'),
    path('api/v1/auth/logout/', logout_user, name='logout'),

    # JWT Token endpoints21
    path('api/v1/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # DRF Browsable API (for development)
    path('api-auth/', include('rest_framework.urls')),
]