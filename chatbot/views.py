import json
import uuid
import asyncio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import ChatSession, ChatMessage
from .services import chatbot_service
from appAdmin.models import ResourceMetadata
from .services import get_chatbot_service 
from asgiref.sync import sync_to_async
from .spell_corrector import get_spell_correction_stats
from django.http import JsonResponse

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
        if source_click and clicked_resource_id:
            bot_response = chatbot_service.generate_source_response(
                message, 
                clicked_resource_id, 
                clicked_resource_type
            )
        else:
            # Regular chatbot processing
            bot_response = chatbot_service.generate_response(message)
        
        # Get detailed AI similarity scores using the new method
        similar_content = chatbot_service.find_similar_content(message, top_k=1)
        ai_scores = {}
        similarity_score = 0.0
        
        if similar_content:
            best_match = similar_content[0]
            similarity_score = best_match['similarity_score']
            ai_scores = {
                'combined_score': similarity_score,
                'semantic_score': best_match.get('ai_score', 0.0),
                'nlp_score': best_match.get('nlp_score', 0.0),
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
            tfidf_score=ai_scores.get('nlp_score', 0.0),
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
    """Debug endpoint to check AI model status - FIXED"""
    try:
        service = get_chatbot_service()
        
        # Get knowledge base data
        knowledge_data, document_texts, knowledge_vectors, knowledge_embeddings = service._get_knowledge_data()
        
        # Check AI models status
        ai_models = service._get_ai_models()
        nlp_model = service._get_nlp_model()
        
        # Properly check FAISS availability
        faiss_available = False
        try:
            import faiss
            faiss_available = True
        except ImportError:
            faiss_available = False
        
        ai_status = {
            'knowledge_items': len(knowledge_data) if knowledge_data else 0,
            'document_texts': len(document_texts) if document_texts else 0,
            'ai_models_loaded': bool(ai_models),
            'ai_models_available': bool(ai_models and ai_models is not False),
            'sentence_transformer': bool(ai_models and isinstance(ai_models, dict) and 'sentence_transformer' in ai_models),
            'intent_classifier': bool(ai_models and isinstance(ai_models, dict) and 'intent_classifier' in ai_models),
            'spacy_model': str(nlp_model) if nlp_model else 'Not loaded',
            'spacy_available': bool(nlp_model and nlp_model is not False),
            'transformers_available': bool(ai_models),
            'embeddings_created': bool(knowledge_embeddings is not None),
            'tfidf_vectors_created': bool(knowledge_vectors is not None),
            'stopwords_loaded': len(service.stopwords) if hasattr(service, 'stopwords') else 0,
            'basic_responses_loaded': len(service.basic_responses.get('greetings', {})) if hasattr(service, 'basic_responses') else 0,
            'local_ai_enabled': True,
            'external_api_usage': False,
            'service_initialized': True,
            'vectorizer_ready': bool(service.vectorizer),
            'faiss_available': faiss_available,  # ← Fixed FAISS detection
            'faiss_functional': False  # We'll test this next
        }
        
        # Test FAISS functionality if available
        if faiss_available:
            try:
                import faiss
                import numpy as np
                
                # Test basic FAISS functionality
                dimension = 128
                index = faiss.IndexFlatL2(dimension)
                
                # Add a test vector
                test_vector = np.random.random((1, dimension)).astype('float32')
                index.add(test_vector)
                
                # Test search
                query = np.random.random((1, dimension)).astype('float32')
                distances, indices = index.search(query, 1)
                
                ai_status['faiss_functional'] = True
                ai_status['faiss_version'] = getattr(faiss, '__version__', 'Version not available')
                
            except Exception as e:
                ai_status['faiss_functional'] = False
                ai_status['faiss_error'] = str(e)
        
        # Add cache information
        try:
            from chatbot.services import _knowledge_base_cache, _json_knowledge_cache
            ai_status['knowledge_cache_active'] = bool(_knowledge_base_cache)
            ai_status['json_cache_active'] = bool(_json_knowledge_cache)
        except ImportError:
            ai_status['cache_status'] = 'Could not check cache status'
        
        # Only test if explicitly requested
        run_tests = request.GET.get('test', 'false').lower() == 'true'
        
        if run_tests and knowledge_data and len(knowledge_data) > 0:
            print("🧪 Running AI tests (explicitly requested)")
            test_queries = ["give me sample RAISE that is in FAQ", "where are CMI locations", "show me farming techniques"]
            ai_status['test_results'] = {}
            
            for query in test_queries:
                try:
                    intent = service._classify_user_intent(query)
                    results = service.find_similar_content(query, top_k=2)
                    ai_status['test_results'][query] = {
                        'intent_detected': intent.get('intent', 'unknown'),
                        'intent_confidence': intent.get('confidence', 0.0),
                        'results_found': len(results),
                        'ai_processing': True,
                        'test_passed': True
                    }
                except Exception as e:
                    ai_status['test_results'][query] = {
                        'error': str(e),
                        'test_passed': False
                    }
        else:
            ai_status['test_results'] = 'Not run - add ?test=true to URL to run AI tests'
        
        # Check JSON knowledge base file
        try:
            from chatbot.services import get_knowledge_base_json_path
            import os
            json_path = get_knowledge_base_json_path()
            if os.path.exists(json_path):
                file_size = round(os.path.getsize(json_path) / (1024 * 1024), 2)
                ai_status['json_file_exists'] = True
                ai_status['json_file_size_mb'] = file_size
                ai_status['json_file_path'] = json_path
            else:
                ai_status['json_file_exists'] = False
                ai_status['json_file_path'] = json_path
        except Exception as e:
            ai_status['json_file_error'] = str(e)
        
        return JsonResponse(ai_status)
        
    except Exception as e:
        import traceback
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'service_available': False
        }
        print(f"❌ Debug AI Status Error: {e}")
        print(traceback.format_exc())
        return JsonResponse(error_info, status=500)

def refresh_knowledge_base(request):
    """Refresh the intelligent AI knowledge base"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Clear the cache to force reload
        from chatbot.services import clear_knowledge_base_cache
        clear_knowledge_base_cache()
        
        service = get_chatbot_service()
        
        # Get fresh knowledge data
        knowledge_data, document_texts, knowledge_vectors, knowledge_embeddings = service._get_knowledge_data()
        ai_models = service._get_ai_models()
        nlp_model = service._get_nlp_model()
        
        return JsonResponse({
            'success': True, 
            'message': 'Intelligent AI knowledge base refreshed successfully',
            'items_loaded': len(knowledge_data) if knowledge_data else 0,
            'documents_loaded': len(document_texts) if document_texts else 0,
            'ai_model_active': bool(ai_models),
            'models_loaded': list(ai_models.keys()) if ai_models and isinstance(ai_models, dict) else [],
            'spacy_model': str(nlp_model) if nlp_model else 'Not loaded',
            'stopwords_loaded': len(service.stopwords) if hasattr(service, 'stopwords') else 0,
            'basic_responses_loaded': len(service.basic_responses.get('greetings', {})) if hasattr(service, 'basic_responses') else 0,
            'local_ai_enabled': True,
            'intelligent_processing': True,
            'cache_cleared': True
        })
    except Exception as e:
        import traceback
        print(f"❌ Refresh Knowledge Base Error: {e}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    
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
    
@sync_to_async
def get_chatbot_response_sync(query):
    return chatbot_service.generate_intelligent_response(query)

async def chatbot_response_async(request):
    query = request.POST.get('message', '').strip()
    
    if not query:
        return JsonResponse({'error': 'No message provided'}, status=400)
    
    try:
        # Run the chatbot processing asynchronously
        response = await get_chatbot_response_sync(query)
        return JsonResponse(response)
        
    except Exception as e:
        return JsonResponse({
            'response': 'Sorry, I encountered an error processing your request.',
            'error': str(e)
        }, status=500)
    
def spell_correction_stats(request):
    """API endpoint to get spell correction statistics"""
    if request.method == 'GET':
        stats = get_spell_correction_stats()
        return JsonResponse({
            'success': True,
            'stats': stats,
            'message': 'Spell correction statistics retrieved successfully'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)