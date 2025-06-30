from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class ChatSession(models.Model):
    user = models.ForeignKey('appAccounts.CustomUser', on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True) 
    expires_at = models.DateTimeField()  
    is_active = models.BooleanField(default=True)

    
    # Enhanced NLP tracking
    nlp_model_used = models.CharField(max_length=50, default='spacy_tfidf_hybrid', help_text='NLP model/approach used')
    total_queries = models.PositiveIntegerField(default=0, help_text='Total queries in this session')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session {self.session_id} - {self.user.username if self.user else 'Anonymous'}"
    
    def save(self, *args, **kwargs):
        # Set expiry to 24 hours from creation if not set
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if session has expired"""
        return timezone.now() > self.expires_at

    def extend_session(self):
        """Extend session by 24 hours from now"""
        self.expires_at = timezone.now() + timedelta(hours=24)
        self.last_activity = timezone.now()
        self.save()

    @classmethod
    def cleanup_expired_sessions(cls):
        """Clean up expired sessions"""
        expired_sessions = cls.objects.filter(expires_at__lt=timezone.now())
        count = expired_sessions.count()
        expired_sessions.delete()
        return count

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    response = models.TextField()
    matched_resource = models.ForeignKey('appAdmin.ResourceMetadata', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Enhanced NLP scoring fields
    similarity_score = models.FloatField(null=True, blank=True, help_text='Combined similarity score')
    tfidf_score = models.FloatField(null=True, blank=True, help_text='TF-IDF similarity score')
    spacy_score = models.FloatField(null=True, blank=True, help_text='spaCy semantic similarity score')
    keyword_score = models.FloatField(null=True, blank=True, help_text='Keyword matching score')
    confidence_level = models.CharField(max_length=10, choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], null=True, blank=True)
    
    # Query processing metadata
    processed_query_length = models.PositiveIntegerField(null=True, blank=True, help_text='Length of processed query')
    semantic_keywords_found = models.PositiveIntegerField(default=0, help_text='Number of semantic keywords extracted')
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message {self.id} - Score: {self.similarity_score or 0:.3f}"

    def save(self, *args, **kwargs):
        # Auto-increment session query count
        if not self.pk:  # Only for new messages
            self.session.total_queries += 1
            self.session.save()
        super().save(*args, **kwargs)