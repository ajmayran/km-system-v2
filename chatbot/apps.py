from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'

    def ready(self):
        import chatbot.signals 
        from .spell_corrector import get_spell_corrector
        get_spell_corrector()