import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import ChatSession, ChatMessage
from .services import chatbot_service
from appAdmin.models import ResourceMetadata

@csrf_exempt
@require_POST
def chat_message(request):
    """Handle chat messages with intelligent AI processing"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        source_click = data.get('source_click', False)
        clicked_resource_id = data.get('clicked_resource_id')
        clicked_resource_type = data.get('clicked_resource_type')
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        if source_click and clicked_resource_id:
            bot_response = chatbot_service.generate_source_response(
                message, 
                clicked_resource_id, 
                clicked_resource_type
            )
        else:
            # Regular chatbot processing
            bot_response = chatbot_service.generate_response(message)
        
        # Clean up expired sessions periodically
        if timezone.now().hour == 0 and timezone.now().minute < 5: 
            ChatSession.cleanup_expired_sessions()
        
        # Get or create chat session with proper expiry handling
        chat_session = None
        
        if session_id:
            try:
                chat_session = ChatSession.objects.get(session_id=session_id)
                
                # Check if session has expired
                if chat_session.is_expired():
                    # Delete expired session and create new one
                    chat_session.delete()
                    chat_session = None
                else:
                    # IMPORTANT: Verify session ownership
                    if request.user.is_authenticated:
                        if chat_session.user != request.user:
                            print(f"Session {session_id} belongs to different user, creating new session")
                            chat_session = None
                    else:
                        # For anonymous users, check if session was created by anonymous user
                        if chat_session.user is not None:
                            print(f"Session {session_id} belongs to authenticated user, creating anonymous session")
                            chat_session = None
                    
                    if chat_session:
                        # Extend session activity
                        chat_session.last_activity = timezone.now()
                        chat_session.save()
                    
            except ChatSession.DoesNotExist:
                chat_session = None
        
        # Create new session if none exists or expired
        if not chat_session:
            chat_session = ChatSession.objects.create(
                session_id=str(uuid.uuid4()),
                user=request.user if request.user.is_authenticated else None,
                nlp_model_used='intelligent_ai_local',
                expires_at=timezone.now() + timedelta(hours=24)
            )
            print(f"Created new session {chat_session.session_id} for user {request.user if request.user.is_authenticated else 'Anonymous'}")
        
        # Generate intelligent response using local AI
        bot_response = chatbot_service.generate_response(message)
        
        # Get detailed AI similarity scores
        similar_content = chatbot_service.find_similar_content(message, top_k=1)
        ai_scores = {}
        similarity_score = 0.0
        
        if similar_content:
            best_match = similar_content[0]
            similarity_score = best_match['similarity_score']
            ai_scores = {
                'combined_score': similarity_score,
                'semantic_score': best_match.get('spacy_score', 0.0),
                'tfidf_score': best_match.get('tfidf_score', 0.0),
                'confidence_level': best_match.get('confidence', 'medium')
            }
        
        # Find matched resource for database storage
        matched_resource = None
        if bot_response.get('matched_resources'):
            best_match = bot_response['matched_resources'][0]
            try:
                if best_match.get('actual_id') and best_match['type'] == 'resource':
                    matched_resource = ResourceMetadata.objects.get(id=best_match['actual_id'])
            except (ResourceMetadata.DoesNotExist, KeyError):
                pass
        
        # Save chat message with AI metadata
        chat_message_obj = ChatMessage.objects.create(
            session=chat_session,
            message=message,
            response=bot_response['response'],
            matched_resource=matched_resource,
            similarity_score=similarity_score,
            spacy_score=ai_scores.get('semantic_score', 0.0),
            tfidf_score=ai_scores.get('tfidf_score', 0.0),
            confidence_level=bot_response.get('confidence', 'medium'),
            processed_query_length=len(message.split()),
            semantic_keywords_found=len(message.split())
        )
        
        # Prepare enhanced response with session info
        response_data = {
            'session_id': chat_session.session_id,
            'session_expires_at': chat_session.expires_at.isoformat(),
            'session_created_at': chat_session.created_at.isoformat(),
            'message_id': chat_message_obj.id,
            'response': bot_response['response'],
            'confidence': bot_response.get('confidence', 'medium'),
            'similarity_score': round(similarity_score, 3),
            'ai_scores': ai_scores,
            'suggestions': bot_response.get('suggestions', []),
            'matched_resources': [],
            'ai_powered': bot_response.get('ai_powered', True),
            'local_ai': bot_response.get('local_ai', True),
            'intelligent_processing': True,
            'intent_detected': True,
            'session_persistent': True,
            'source_click': source_click,
            'url': bot_response.get('url'),
            'user_verified': True
        }
        
        # Add matched resources with enhanced data
        for resource_data in bot_response.get('matched_resources', []):
            try:
                resource_info = {
                    'id': resource_data.get('actual_id', resource_data.get('id')),
                    'title': resource_data['title'],
                    'description': resource_data['description'][:200] + '...' if len(resource_data['description']) > 200 else resource_data['description'],
                    'type': resource_data['type'],
                    'url': resource_data.get('url', '#')
                }
                
                if resource_data['type'] == 'resource':
                    resource_info['resource_type'] = resource_data.get('resource_type', 'unknown')
                elif resource_data['type'] == 'forum':
                    resource_info['author'] = resource_data.get('author', 'Unknown')
                elif resource_data['type'] == 'cmi':
                    resource_info['location'] = resource_data.get('location', '')
                    resource_info['contact'] = resource_data.get('contact', '')
                elif resource_data['type'] == 'faq':
                    resource_info['faq_type'] = 'FAQ'
                
                response_data['matched_resources'].append(resource_info)
            except Exception as e:
                print(f"Error processing resource data: {e}")
                continue
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Intelligent Chatbot error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
    
@csrf_exempt
def get_session_history(request):
    """Get chat history for a specific session"""
    try:
        session_id = request.GET.get('session_id')
        if not session_id:
            return JsonResponse({'error': 'Session ID required'}, status=400)
        
        try:
            chat_session = ChatSession.objects.get(session_id=session_id)
            
            # Check if session has expired
            if chat_session.is_expired():
                return JsonResponse({
                    'session_expired': True,
                    'message': 'Session has expired',
                    'messages': []
                })
            
            # IMPORTANT: Check if session belongs to current user
            if request.user.is_authenticated:
                if chat_session.user != request.user:
                    return JsonResponse({
                        'session_expired': True,
                        'message': 'Session belongs to different user',
                        'messages': []
                    })
            else:
                # For anonymous users, check if session was created by anonymous user
                if chat_session.user is not None:
                    return JsonResponse({
                        'session_expired': True,
                        'message': 'Session belongs to different user',
                        'messages': []
                    })
            
            # Get all messages for this session
            messages = chat_session.messages.all().order_by('timestamp')
            
            message_history = []
            for msg in messages:
                message_data = {
                    'id': msg.id,
                    'message': msg.message,
                    'response': msg.response,
                    'timestamp': msg.timestamp.isoformat(),
                    'similarity_score': msg.similarity_score,
                    'confidence_level': msg.confidence_level,
                    'matched_resource': {
                        'id': msg.matched_resource.id,
                        'title': msg.matched_resource.title,
                        'slug': msg.matched_resource.slug,
                        'resource_type': msg.matched_resource.resource_type
                    } if msg.matched_resource else None
                }
                message_history.append(message_data)
            
            return JsonResponse({
                'session_id': chat_session.session_id,
                'session_expires_at': chat_session.expires_at.isoformat(),
                'session_created_at': chat_session.created_at.isoformat(),
                'total_queries': chat_session.total_queries,
                'messages': message_history,
                'session_expired': False,
                'session_persistent': True,
                'user_verified': True
            })
            
        except ChatSession.DoesNotExist:
            return JsonResponse({
                'session_expired': True,
                'message': 'Session not found',
                'messages': []
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
def debug_ai_status(request):
    """Debug endpoint to check AI model status"""
    try:
        ai_status = {
            'knowledge_items': len(chatbot_service.knowledge_data),
            'ai_models_loaded': bool(chatbot_service.ai_models),
            'sentence_transformer': 'sentence_transformer' in chatbot_service.ai_models,
            'intent_classifier': 'intent_classifier' in chatbot_service.ai_models,
            'qa_pipeline': 'qa_pipeline' in chatbot_service.ai_models,
            'spacy_model': str(chatbot_service.nlp) if chatbot_service.nlp else 'Not loaded',
            'transformers_available': hasattr(chatbot_service, 'ai_models'),
            'embeddings_created': hasattr(chatbot_service, 'knowledge_embeddings'),
            'conversation_history_size': len(getattr(chatbot_service, 'conversation_history', [])),
            'local_ai_enabled': True,
            'external_api_usage': False
        }
        
        # Test AI functionality
        if chatbot_service.ai_models:
            test_queries = ["give me sample 1 FAQ", "where are CMI locations", "show me farming techniques"]
            ai_status['test_results'] = {}
            
            for query in test_queries:
                try:
                    intent = chatbot_service._classify_user_intent(query)
                    results = chatbot_service.find_similar_content(query, top_k=2)
                    ai_status['test_results'][query] = {
                        'intent_detected': intent.get('intent', 'unknown'),
                        'intent_confidence': intent.get('confidence', 0.0),
                        'results_found': len(results),
                        'ai_processing': True
                    }
                except Exception as e:
                    ai_status['test_results'][query] = {'error': str(e)}
        
        return JsonResponse(ai_status)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def chat_history(request):
    """Get chat history with AI intelligence indicators"""
    try:
        sessions = ChatSession.objects.filter(user=request.user)[:5]
        
        history = []
        for session in sessions:
            messages = session.messages.all()[:10]
            session_data = {
                'session_id': session.session_id,
                'created_at': session.created_at.isoformat(),
                'nlp_model_used': session.nlp_model_used,
                'total_queries': session.total_queries,
                'ai_powered': True,
                'messages': [
                    {
                        'id': msg.id,
                        'message': msg.message,
                        'response': msg.response,
                        'timestamp': msg.timestamp.isoformat(),
                        'similarity_score': msg.similarity_score,
                        'confidence_level': msg.confidence_level,
                        'ai_processed': True,
                        'matched_resource': {
                            'id': msg.matched_resource.id,
                            'title': msg.matched_resource.title,
                            'slug': msg.matched_resource.slug,
                            'resource_type': msg.matched_resource.resource_type
                        } if msg.matched_resource else None
                    } for msg in messages
                ]
            }
            history.append(session_data)
        
        return JsonResponse({
            'history': history, 
            'ai_powered': True, 
            'local_ai_enabled': True,
            'intelligent_processing': True
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def refresh_knowledge_base(request):
    """Refresh the intelligent AI knowledge base"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        chatbot_service._load_knowledge_base()
        
        return JsonResponse({
            'success': True, 
            'message': 'Intelligent AI knowledge base refreshed successfully',
            'items_loaded': len(chatbot_service.knowledge_data),
            'ai_models_active': bool(chatbot_service.ai_models),
            'models_loaded': list(chatbot_service.ai_models.keys()) if chatbot_service.ai_models else [],
            'spacy_model': str(chatbot_service.nlp) if chatbot_service.nlp else 'Not loaded',
            'local_ai_enabled': True,
            'intelligent_processing': True
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)