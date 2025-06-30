from django.urls import path, include
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('chat/', views.chat_message, name='chat_message'),
    path('history/', views.chat_history, name='chat_history'),
    path('refresh/', views.refresh_knowledge_base, name='refresh_knowledge_base'),
    path('debug-ai-status/', views.debug_ai_status, name='debug_ai_status'),
    path('session-history/', views.get_session_history, name='get_session_history'),
]