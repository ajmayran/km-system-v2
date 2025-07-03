from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from .models import ChatSession

@receiver(user_logged_out)
def clear_chat_sessions_on_logout(sender, request, user, **kwargs):
    """Clear all chat sessions when user logs out"""
    if user:
        # Delete all sessions for this user
        deleted_count, _ = ChatSession.objects.filter(user=user).delete()
        print(f"🗑️ Cleared {deleted_count} chat sessions for user {user.username}")
        
        # Also clear the session from browser storage (via response)
        if hasattr(request, 'session'):
            request.session.pop('chatbot_session_id', None)