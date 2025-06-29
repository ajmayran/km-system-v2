import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import ChatSession, ChatMessage
from .services import chatbot_service
from appAdmin.models import ResourceMetadata

@csrf_exempt
@require_POST
def chat_message(request):
    """Handle chat messages with advanced spaCy NLP processing"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get or create chat session
        if session_id:
            try:
                chat_session = ChatSession.objects.get(session_id=session_id)
            except ChatSession.DoesNotExist:
                chat_session = ChatSession.objects.create(
                    session_id=str(uuid.uuid4()),
                    user=request.user if request.user.is_authenticated else None
                )
        else:
            chat_session = ChatSession.objects.create(
                session_id=str(uuid.uuid4()),
                user=request.user if request.user.is_authenticated else None
            )
        
        # Generate response using advanced spaCy NLP
        bot_response = chatbot_service.generate_response(message)
        
        # Get detailed NLP similarity scores
        similar_content = chatbot_service.find_similar_content(message, top_k=1)
        nlp_scores = {}
        similarity_score = 0.0
        
        if similar_content:
            best_match = similar_content[0]
            similarity_score = best_match['similarity_score']
            nlp_scores = {
                'combined_score': similarity_score,
                'tfidf_score': best_match.get('tfidf_score', 0.0),
                'spacy_score': best_match.get('spacy_score', 0.0),
                'keyword_score': best_match.get('keyword_score', 0.0)
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
        
        # Save chat message with enhanced NLP data
        chat_message_obj = ChatMessage.objects.create(
            session=chat_session,
            message=message,
            response=bot_response['response'],
            matched_resource=matched_resource,
            similarity_score=similarity_score
        )
        
        # Prepare enhanced response with NLP details
        response_data = {
            'session_id': chat_session.session_id,
            'message_id': chat_message_obj.id,
            'response': bot_response['response'],
            'confidence': bot_response.get('confidence', 'medium'),
            'similarity_score': round(similarity_score, 3),
            'nlp_scores': nlp_scores,  # Add detailed NLP scoring
            'suggestions': bot_response.get('suggestions', []),
            'matched_resources': [],
            'nlp_powered': True,
            'spacy_enabled': chatbot_service.nlp is not None  # Indicate if spaCy is working
        }
        
        # Add matched resources with enhanced data
        for resource_data in bot_response.get('matched_resources', []):
            try:
                resource_info = {
                    'id': resource_data.get('actual_id', resource_data.get('id')),
                    'title': resource_data['title'],
                    'description': resource_data['description'][:200] + '...' if len(resource_data['description']) > 200 else resource_data['description'],
                    'type': resource_data['type'],
                    'url': resource_data['url']
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
        print(f"Chatbot error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

def debug_knowledge_base(request):
    """Debug endpoint to check advanced spaCy NLP knowledge base"""
    try:
        debug_info = {
            'knowledge_items': len(chatbot_service.knowledge_data),
            'has_tfidf_vectors': chatbot_service.knowledge_vectors is not None,
            'vector_shape': chatbot_service.knowledge_vectors.shape if chatbot_service.knowledge_vectors is not None else None,
            'vocabulary_size': len(chatbot_service.vectorizer.vocabulary_) if hasattr(chatbot_service.vectorizer, 'vocabulary_') else 0,
            'spacy_model': str(chatbot_service.nlp) if chatbot_service.nlp else 'Not loaded',
            'custom_stopwords_count': len(chatbot_service.custom_stopwords) if chatbot_service.custom_stopwords else 0,
            'sample_items': [
                {
                    'id': item['id'],
                    'title': item['title'][:50] + '...' if len(item['title']) > 50 else item['title'],
                    'type': item['type'],
                    'processed_text_length': len(item['processed_text']) if 'processed_text' in item else 0,
                    'semantic_keywords_count': len(item.get('semantic_keywords', [])),
                    'has_spacy_doc': item.get('spacy_doc') is not None
                }
                for item in chatbot_service.knowledge_data[:5]
            ],
            'nlp_status': 'active' if chatbot_service.knowledge_vectors is not None else 'inactive'
        }
        
        # Test advanced NLP similarity search
        if chatbot_service.knowledge_vectors is not None:
            test_queries = ["rice farming techniques", "aquaculture methods", "CMI locations"]
            debug_info['test_results'] = {}
            
            for query in test_queries:
                test_results = chatbot_service.find_similar_content(query, top_k=3)
                debug_info['test_results'][query] = [
                    {
                        'title': result['resource']['title'],
                        'type': result['resource']['type'],
                        'combined_score': result['similarity_score'],
                        'tfidf_score': result.get('tfidf_score', 0.0),
                        'spacy_score': result.get('spacy_score', 0.0),
                        'keyword_score': result.get('keyword_score', 0.0),
                        'confidence': result['confidence']
                    }
                    for result in test_results
                ]
        
        return JsonResponse(debug_info)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def chat_history(request):
    """Get chat history with enhanced NLP similarity scores"""
    try:
        sessions = ChatSession.objects.filter(user=request.user)[:5]
        
        history = []
        for session in sessions:
            messages = session.messages.all()[:10]
            session_data = {
                'session_id': session.session_id,
                'created_at': session.created_at.isoformat(),
                'messages': [
                    {
                        'id': msg.id,
                        'message': msg.message,
                        'response': msg.response,
                        'timestamp': msg.timestamp.isoformat(),
                        'similarity_score': msg.similarity_score,
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
        
        return JsonResponse({'history': history, 'nlp_powered': True, 'spacy_enabled': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def refresh_knowledge_base(request):
    """Refresh the advanced spaCy NLP knowledge base"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        chatbot_service._load_knowledge_base()
        return JsonResponse({
            'success': True, 
            'message': 'Advanced spaCy NLP knowledge base refreshed successfully',
            'items_loaded': len(chatbot_service.knowledge_data),
            'vector_shape': chatbot_service.knowledge_vectors.shape if chatbot_service.knowledge_vectors is not None else None,
            'spacy_model': str(chatbot_service.nlp) if chatbot_service.nlp else 'Not loaded',
            'stopwords_count': len(chatbot_service.custom_stopwords) if chatbot_service.custom_stopwords else 0
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)