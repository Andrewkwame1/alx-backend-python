from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.http import HttpResponseForbidden

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