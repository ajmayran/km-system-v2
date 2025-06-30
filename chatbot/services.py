import re
import logging
import numpy as np
from django.db import models
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from spacy.lang.en.stop_words import STOP_WORDS

# Import for local AI
try:
    from sentence_transformers import SentenceTransformer
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    import torch
    TRANSFORMERS_AVAILABLE = True
    print("✅ Transformers libraries loaded successfully!")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not installed. Install with: pip install transformers sentence-transformers torch")

# Text preprocessing utilities
def preprocess_text(text):
    """Preprocess text for better matching"""
    if not text:
        return ""
    
    # Basic cleaning
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text

def find_similar_resources(query, knowledge_data, top_k=5):
    """Basic similarity search function"""
    results = []
    query_words = set(preprocess_text(query).split())
    
    for item in knowledge_data:
        text = f"{item['title']} {item['description']}"
        item_words = set(preprocess_text(text).split())
        
        # Calculate simple word overlap
        overlap = len(query_words.intersection(item_words))
        if overlap > 0:
            similarity = overlap / max(len(query_words), len(item_words))
            results.append({
                'resource': item,
                'similarity_score': similarity,
                'tfidf_score': 0.0,
                'spacy_score': 0.0,
                'text_score': similarity,
                'confidence': 'high' if similarity > 0.3 else 'medium'
            })
    
    # Sort by similarity and return top results
    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    return results[:top_k]

from appAdmin.models import (
    ResourceMetadata, KnowledgeResources, Commodity, 
    Event, InformationSystem, Map, Media, News, Policy,
    Project, Publication, Technology, TrainingSeminar, Webinar, Product,
    CMI  
)
from appCmi.models import (
    Forum, ForumComment, FAQ
)

logger = logging.getLogger(__name__)

class IntelligentChatbotService:
    def __init__(self):
        self.knowledge_data = []
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8
        )
        self.knowledge_vectors = None
        self.document_texts = []
        
        # Initialize spaCy model
        try:
            self.nlp = spacy.load("en_core_web_md")
            print("✅ Loaded spaCy model: en_core_web_md")
        except OSError:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("✅ Loaded spaCy model: en_core_web_sm")
            except OSError:
                print("⚠️ Warning: No spaCy model found. Using basic processing.")
                self.nlp = None
        
        # Initialize local AI models
        self.ai_models = {}
        if TRANSFORMERS_AVAILABLE:
            self._initialize_ai_models()
        
        # Create enhanced stopwords list
        self.custom_stopwords = self._load_custom_stopwords()
        
        self._load_knowledge_base()

    def _initialize_ai_models(self):
        """Initialize local AI models for intelligent processing"""
        try:
            print("🧠 Loading local AI models...")
            
            self.ai_models['sentence_transformer'] = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Loaded sentence transformer model")
            
            # 2. Intent classification pipeline
            self.ai_models['intent_classifier'] = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            print("✅ Loaded intent classification model")
            
            self.ai_models['qa_pipeline'] = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad",
                device=0 if torch.cuda.is_available() else -1
            )
            print("✅ Loaded question-answering model")
            
            try:
                self.ai_models['conversation_tokenizer'] = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
                self.ai_models['conversation_model'] = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")
                print("✅ Loaded conversational tokenizer and model")
                
                self.ai_models['conversation_generator'] = pipeline(
                    "text-generation",
                    model="microsoft/DialoGPT-small",
                    tokenizer="microsoft/DialoGPT-small",
                    device=0 if torch.cuda.is_available() else -1,
                    max_length=150,
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=50256
                )
                print("✅ Loaded conversation generator")
                
            except Exception as e:
                print(f"⚠️ Could not load conversational model: {e}")
                print("💡 Using Q&A model for conversations instead")
            
            # 5. General text generation pipeline
            try:
                self.ai_models['text_generator'] = pipeline(
                    "text-generation",
                    model="gpt2",  # Small GPT-2 model for local generation
                    device=0 if torch.cuda.is_available() else -1,
                    max_length=150,
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=50256
                )
                print("✅ Loaded text generation model")
            except Exception as e:
                print(f"⚠️ Could not load text generation model: {e}")
            
            # Initialize conversation history for context
            self.conversation_history = []
            
            print("🎉 All local AI models loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading AI models: {e}")
            print("💡 Falling back to basic NLP processing")

    def _classify_user_intent(self, query):
        """Classify user intent using local AI"""
        if not self.ai_models.get('intent_classifier'):
            return self._classify_intent_basic(query)
        
        try:
            # Define possible intents
            candidate_labels = [
                "request for examples or samples",
                "looking for specific information", 
                "asking for location or contact details",
                "requesting farming or agricultural advice",
                "seeking aquaculture information",
                "general conversation or greeting",
                "asking about training programs",
                "technical support question",
                "browsing or exploring content",
                "asking about CMI services",
                "content discovery for specific topic",  
                "information request about specific subject"  
            ]
            
            result = self.ai_models['intent_classifier'](query, candidate_labels)

            main_topic = self._extract_main_topic(query)
            content_type = self._extract_content_type(query)
            
            # Map to our internal intent system
            intent_mapping = {
                "request for examples or samples": "sample_request",
                "looking for specific information": "specific_query",
                "asking for location or contact details": "location_query",
                "requesting farming or agricultural advice": "agriculture_query", 
                "seeking aquaculture information": "aquaculture_query",
                "general conversation or greeting": "general_conversation",
                "asking about training programs": "program_query",
                "technical support question": "support_query",
                "browsing or exploring content": "browse_request",
                "asking about CMI services": "cmi_query",
                "content discovery for specific topic": "topic_content_request",  
                "information request about specific subject": "topic_content_request" 
            }
            
            top_intent = result['labels'][0]
            confidence = result['scores'][0]
            
            if any(word in query.lower() for word in ['content', 'information', 'details', 'about', 'on']) and confidence < 0.7:
                detected_intent = "topic_content_request"
            else:
                detected_intent = intent_mapping.get(top_intent, "topic_content_request")
        
            return {
                'intent': detected_intent,
                'confidence': confidence,
                'main_topic': main_topic,
                'content_type': content_type,
                'raw_classification': result
            }
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            return self._classify_intent_basic(query)

    def _extract_main_topic(self, query):     
            """Extract the main topic/subject from the query"""
            # Remove content-type words to find the main topic
            content_words = ['content', 'information', 'details', 'about', 'on', 'for', 'regarding', 'materials', 'data']
            
            # Clean the query
            words = query.lower().split()
            topic_words = [word for word in words if word not in content_words and len(word) > 2]
            
            # Get the most important topic word (usually the first meaningful word)
            if topic_words:
                return topic_words[0].upper()  # Return as uppercase for better matching
            
            return None  
    
    def _extract_content_type(self, query):
            """Extract what type of content is being requested"""
            query_lower = query.lower()
            
            if 'content' in query_lower:
                return 'content'
            elif 'information' in query_lower:
                return 'information'
            elif 'details' in query_lower:
                return 'details'
            elif 'materials' in query_lower:
                return 'materials'
            elif 'data' in query_lower:
                return 'data'
            else:
                return 'general'
        

    def _classify_intent_basic(self, query):
        """Basic intent classification using patterns"""
        query_lower = query.lower()
        
        main_topic = self._extract_main_topic(query)
        content_type = self._extract_content_type(query)
        
        # Topic content requests - NEW PATTERN
        if any(word in query_lower for word in ['content', 'information', 'details', 'about', 'materials', 'data']) and main_topic:
            return {
                'intent': 'topic_content_request', 
                'confidence': 0.8,
                'main_topic': main_topic,
                'content_type': content_type
            }
        
        # Conversational patterns
        elif any(word in query_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'bye', 'goodbye', 'thanks', 'thank you', 'help', 'what can you', 'what do you']):
            return {'intent': 'general_conversation', 'confidence': 0.9}
        
        # Sample/example requests
        elif any(word in query_lower for word in ['sample', 'example', 'show me', 'give me']):
            return {'intent': 'sample_request', 'confidence': 0.8}
        
        # Location requests
        elif any(word in query_lower for word in ['where', 'location', 'address', 'contact']):
            return {'intent': 'location_query', 'confidence': 0.7}
        
        # Agriculture requests
        elif any(word in query_lower for word in ['farm', 'crop', 'plant', 'agriculture']):
            return {'intent': 'agriculture_query', 'confidence': 0.7}
        
        # FAQ requests
        elif any(word in query_lower for word in ['faq', 'question', 'answer']):
            return {'intent': 'faq_request', 'confidence': 0.8}
        
        # Default - if we have a topic, treat as topic request
        elif main_topic:
            return {
                'intent': 'topic_content_request', 
                'confidence': 0.6,
                'main_topic': main_topic,
                'content_type': 'general'
            }
        else:
            return {'intent': 'general_query', 'confidence': 0.5}

    def _enhanced_semantic_search(self, query, intent_info, top_k=5):
        """Enhanced semantic search with topic-focused understanding"""
        if not self.ai_models.get('sentence_transformer'):
            return self.find_similar_content_topic_focused(query, intent_info, top_k=top_k)
        
        try:
            # Handle topic content requests specially
            if intent_info['intent'] == 'topic_content_request':
                return self._handle_topic_content_request(query, intent_info, top_k)
            elif intent_info['intent'] == 'sample_request':
                return self._handle_sample_request(query, top_k)
            
            # Regular semantic search for other intents
            query_embedding = self.ai_models['sentence_transformer'].encode([query])
            
            # Create embeddings if not exists
            if not hasattr(self, 'knowledge_embeddings'):
                self._create_knowledge_embeddings()
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, self.knowledge_embeddings)[0]
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:top_k * 2]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:
                    item = self.knowledge_data[idx]
                    results.append({
                        'resource': item,
                        'similarity_score': float(similarities[idx]),
                        'tfidf_score': 0.0,
                        'spacy_score': float(similarities[idx]),
                        'text_score': 0.0,
                        'confidence': self._get_confidence_level(similarities[idx])
                    })
            
            return results[:top_k]
            
        except Exception as e:
            print(f"Enhanced semantic search error: {e}")
            return self.find_similar_content_topic_focused(query, intent_info, top_k=top_k)
        
    def _handle_topic_content_request(self, query, intent_info, top_k):
        """Handle requests for content about a specific topic"""
        main_topic = intent_info.get('main_topic')
        content_type = intent_info.get('content_type', 'content')
        
        print(f"🎯 Looking for {content_type} about topic: {main_topic}")
        
        if not main_topic:
            # Fallback to regular search if no clear topic extracted
            return self._enhanced_semantic_search_fallback(query, top_k)
        
        results = []
        
        # First, do exact topic matching
        topic_lower = main_topic.lower()
        
        # Score items based on topic relevance
        for item in self.knowledge_data:
            score = 0
            title_lower = item['title'].lower()
            desc_lower = item['description'].lower()
            
            # High score for exact topic match in title
            if topic_lower in title_lower:
                score += 3
            
            # Medium score for topic match in description
            if topic_lower in desc_lower:
                score += 2
            
            # Lower score for partial matches
            topic_words = topic_lower.split()
            for word in topic_words:
                if len(word) > 2:  # Ignore short words
                    if word in title_lower:
                        score += 1
                    elif word in desc_lower:
                        score += 0.5
            
            # Bonus for certain content types
            if item['type'] in ['resource', 'faq', 'forum']:
                score += 0.5
            
            if score > 0:
                results.append({
                    'resource': item,
                    'similarity_score': score,
                    'tfidf_score': 0.0,
                    'spacy_score': score,
                    'text_score': score,
                    'confidence': 'high' if score >= 3 else 'medium' if score >= 1.5 else 'low',
                    'topic_match': True,
                    'topic_score': score
                })
        
        # Sort by topic relevance score
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # If we have good results, return them
        if results and results[0]['similarity_score'] >= 1:
            return results[:top_k]
        
        # If no good topic matches, fall back to semantic search
        print(f"⚠️ No strong topic matches for '{main_topic}', falling back to semantic search")
        return self._enhanced_semantic_search_fallback(query, top_k)
    
    def _enhanced_semantic_search_fallback(self, query, top_k):
        """Fallback semantic search when topic extraction fails"""
        if not self.ai_models.get('sentence_transformer'):
            return self.find_similar_content(query, top_k=top_k)
        
        try:
            query_embedding = self.ai_models['sentence_transformer'].encode([query])
            
            if not hasattr(self, 'knowledge_embeddings'):
                self._create_knowledge_embeddings()
            
            similarities = cosine_similarity(query_embedding, self.knowledge_embeddings)[0]
            top_indices = np.argsort(similarities)[::-1][:top_k * 2]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:
                    item = self.knowledge_data[idx]
                    results.append({
                        'resource': item,
                        'similarity_score': float(similarities[idx]),
                        'tfidf_score': 0.0,
                        'spacy_score': float(similarities[idx]),
                        'text_score': 0.0,
                        'confidence': self._get_confidence_level(similarities[idx])
                    })
            
            return results[:top_k]
            
        except Exception as e:
            print(f"Fallback semantic search error: {e}")
            return []
    
    def find_similar_content_topic_focused(self, query, intent_info, top_k=5):
        """Topic-focused search fallback without transformers"""
        main_topic = intent_info.get('main_topic')
        
        if not main_topic:
            return self.find_similar_content(query, top_k=top_k)
        
        results = []
        topic_lower = main_topic.lower()
        
        for item in self.knowledge_data:
            text_content = f"{item['title']} {item['description']}".lower()
            
            # Calculate topic relevance
            topic_score = 0
            if topic_lower in text_content:
                # Check where the topic appears
                if topic_lower in item['title'].lower():
                    topic_score += 2  # Higher weight for title matches
                if topic_lower in item['description'].lower():
                    topic_score += 1  # Lower weight for description matches
            
            # Simple word overlap for additional context
            query_words = set(query.lower().split())
            content_words = set(text_content.split())
            overlap = len(query_words.intersection(content_words))
            
            total_score = topic_score + (overlap * 0.1)
            
            if total_score > 0:
                results.append({
                    'resource': item,
                    'similarity_score': total_score,
                    'tfidf_score': total_score,
                    'spacy_score': 0.0,
                    'text_score': total_score,
                    'confidence': 'high' if total_score >= 2 else 'medium'
                })
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:top_k]

    def _handle_sample_request(self, query, top_k):
        """Handle requests for samples/examples"""
        results = []
        query_lower = query.lower()
        
        # Extract what type of sample they want
        if 'faq' in query_lower:
            target_type = 'faq'
        elif 'forum' in query_lower or 'discussion' in query_lower:
            target_type = 'forum'
        elif 'resource' in query_lower:
            target_type = 'resource'
        elif 'cmi' in query_lower:
            target_type = 'cmi'
        else:
            target_type = None
        
        # Extract number if specified
        import re
        numbers = re.findall(r'\d+', query)
        requested_count = int(numbers[0]) if numbers else top_k
        
        # Filter by type if specified
        if target_type:
            filtered_items = [item for item in self.knowledge_data if item.get('type') == target_type]
        else:
            filtered_items = self.knowledge_data
        
        # Return the requested number of samples
        for i, item in enumerate(filtered_items[:requested_count]):
            results.append({
                'resource': item,
                'similarity_score': 1.0 - (i * 0.1),  # Decreasing score
                'tfidf_score': 0.0,
                'spacy_score': 0.0,
                'text_score': 1.0 - (i * 0.1),
                'confidence': 'high'
            })
        
        return results

    def _generate_qa_response(self, query, similar_content):
        """Generate direct answers using QA model"""
        if not self.ai_models.get('qa_pipeline'):
            return self._generate_fallback_response(query, similar_content)
        
        try:
            best_match = similar_content[0]
            resource = best_match['resource']
            
            # Prepare context for QA
            context = f"{resource['title']}. {resource['description']}"
            if len(context) > 500:  # Limit context length
                context = context[:500] + "..."
            
            # Get AI-generated answer
            result = self.ai_models['qa_pipeline'](question=query, context=context)
            ai_answer = result['answer']
            confidence = result['score']
            
            # Enhance the response
            if confidence > 0.7:
                response_text = f"**{resource['title']}**\n\n{ai_answer}"
            else:
                response_text = f"**{resource['title']}**\n\n{resource['description']}\n\n💡 *Based on the content above: {ai_answer}*"
            
            # Add source information
            response_text += f"\n\n📋 **Source:** {resource['type'].title()}"
            if resource.get('author'):
                response_text += f" by {resource['author']}"
            
            return {
                'response': response_text,
                'confidence': 'high' if confidence > 0.7 else 'medium',
                'suggestions': self._generate_dynamic_suggestions(query, similar_content),
                'matched_resources': [resource],
                'ai_powered': True,
                'local_ai': True
            }
            
        except Exception as e:
            print(f"QA generation error: {e}")
            return self._generate_fallback_response(query, similar_content)

    def _generate_dynamic_suggestions(self, query, similar_content):
        """Generate contextual suggestions based on AI analysis"""
        suggestions = []
        
        # Analyze query intent for better suggestions
        query_words = query.lower().split()
        
        # Domain-specific suggestions
        if any(word in query_words for word in ['farm', 'crop', 'plant', 'agriculture']):
            suggestions.extend([
                "Tell me about sustainable farming practices",
                "What are the latest agricultural technologies?",
                "Find crop disease management guides"
            ])
        elif any(word in query_words for word in ['fish', 'aqua', 'tilapia', 'pond']):
            suggestions.extend([
                "Explain aquaculture best practices",
                "Show me fish farming techniques",
                "What are common fish diseases?"
            ])
        elif any(word in query_words for word in ['cmi', 'office', 'contact', 'location']):
            suggestions.extend([
                "Find all CMI office locations",
                "How to contact CMI experts?",
                "What services does CMI provide?"
            ])
        
        # Add suggestions based on similar content
        for match in similar_content[:2]:
            resource = match['resource']
            if resource['type'] == 'faq':
                suggestions.append(f"More about: {resource['title'][:35]}...")
            elif resource['type'] == 'forum':
                suggestions.append(f"Join discussion: {resource['title'][:30]}...")
        
        # Fallback suggestions
        while len(suggestions) < 3:
            fallback = [
                "What can you help me with?",
                "Show me popular topics",
                "Find expert discussions"
            ]
            for sug in fallback:
                if sug not in suggestions:
                    suggestions.append(sug)
                    break
            break
        
        return suggestions[:3]

    def generate_intelligent_response(self, query):
        """Main method for generating intelligent responses using local AI"""
        query = query.strip()
        
        # 1. Classify user intent with topic extraction
        intent_info = self._classify_user_intent(query)
        print(f"🧠 Detected intent: {intent_info}")
        
        # 2. Handle based on AI-detected intent
        if intent_info['intent'] == 'general_conversation':
            return self._generate_conversational_response(query, intent_info)
        elif intent_info['intent'] == 'sample_request':
            matched_resources = self._enhanced_semantic_search(query, intent_info, top_k=5)
            return self._generate_sample_response(query, matched_resources, intent_info)
        elif intent_info['intent'] == 'topic_content_request':
            # Special handling for topic content requests
            matched_resources = self._enhanced_semantic_search(query, intent_info, top_k=8)
            return self._generate_topic_content_response(query, matched_resources, intent_info)
        else:
            # Regular processing for other intents
            matched_resources = self._enhanced_semantic_search(query, intent_info, top_k=5)
            print(f"🔍 Found {len(matched_resources)} matches")
            
            if matched_resources and len(matched_resources) > 0:
                return self._generate_qa_response(query, matched_resources)
            else:
                return self._generate_no_results_response(query)
            
    def _generate_topic_content_response(self, query, matched_resources, intent_info):
        """Generate response specifically for topic content requests"""
        main_topic = intent_info.get('main_topic', 'the requested topic')
        content_type = intent_info.get('content_type', 'content')
        
        if not matched_resources:
            return {
                'response': f"I couldn't find specific {content_type} about '{main_topic}'. Try asking about related topics or browse our available resources.\n\n🌾 Agricultural resources\n🐟 Aquaculture information\n💬 Forum discussions\n❓ FAQs\n🏢 CMI services",
                'confidence': 'low',
                'suggestions': [
                    f"Tell me about {main_topic.lower()}",
                    f"Find {main_topic.lower()} resources",
                    f"Show me {main_topic.lower()} examples",
                    "Browse available topics"
                ],
                'matched_resources': []
            }
        
        # Group results by type for better organization
        grouped_results = {}
        for match in matched_resources:
            resource_type = match['resource']['type']
            if resource_type not in grouped_results:
                grouped_results[resource_type] = []
            grouped_results[resource_type].append(match)
        
        response_parts = []
        response_parts.append(f"🎯 **{content_type.title()} about {main_topic}:**\n")
        
        # Type icons and labels
        type_info = {
            'faq': {'icon': '❓', 'label': 'Frequently Asked Questions'},
            'forum': {'icon': '💬', 'label': 'Forum Discussions'},
            'resource': {'icon': '📄', 'label': 'Resources & Publications'},
            'commodity': {'icon': '🌾', 'label': 'Commodity Information'},
            'cmi': {'icon': '🏢', 'label': 'CMI Information'},
            'category': {'icon': '📚', 'label': 'Knowledge Categories'}
        }
        
        # Display grouped results
        for resource_type, matches in grouped_results.items():
            if matches:
                type_data = type_info.get(resource_type, {'icon': '📌', 'label': resource_type.title()})
                response_parts.append(f"\n{type_data['icon']} **{type_data['label']}:**")
                
                for i, match in enumerate(matches[:3], 1):  # Show top 3 per type
                    resource = match['resource']
                    title = resource['title'][:50] + '...' if len(resource['title']) > 50 else resource['title']
                    desc = resource['description'][:80] + '...' if len(resource['description']) > 80 else resource['description']
                    
                    # Highlight topic matches
                    if main_topic.lower() in title.lower():
                        title = f"**{title}**"
                    
                    response_parts.append(f"  {i}. {title}")
                    response_parts.append(f"     {desc}")
        
        # Add helpful footer
        response_parts.append(f"\n💡 *Found {len(matched_resources)} results related to {main_topic}. Click any item above for details.*")
        
        # Generate contextual suggestions
        suggestions = [
            f"Tell me more about {main_topic.lower()}",
            f"Find {main_topic.lower()} examples",
            f"Show {main_topic.lower()} techniques",
            "Browse related topics"
        ]
        
        return {
            'response': '\n'.join(response_parts),
            'confidence': 'high' if len(matched_resources) >= 3 else 'medium',
            'suggestions': suggestions,
            'matched_resources': [match['resource'] for match in matched_resources],
            'ai_powered': True,
            'local_ai': True,
            'topic_focused': True,
            'main_topic': main_topic
        }

    def _generate_conversational_response(self, query, intent_info):
        """Generate natural conversational responses using REAL AI generation"""
        query_lower = query.lower()
        
        # Try to use the conversation generator first (DialoGPT)
        if self.ai_models.get('conversation_generator'):
            try:
                # Format query for DialoGPT
                conversation_prompt = f"User: {query}\nBot:"
                
                # Generate response using DialoGPT
                result = self.ai_models['conversation_generator'](
                    conversation_prompt,
                    max_length=len(conversation_prompt.split()) + 30,
                    num_return_sequences=1,
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=50256,
                    eos_token_id=50256
                )
                
                generated_text = result[0]['generated_text']
                # Extract just the bot response
                ai_response = generated_text.replace(conversation_prompt, "").strip()
                
                # Clean up the response
                if ai_response.startswith("Bot:"):
                    ai_response = ai_response[4:].strip()
                
                # Enhance with domain context if the response is too generic
                if len(ai_response) < 20 or any(word in query_lower for word in ['what are you', 'who are you']):
                    if any(word in query_lower for word in ['hello', 'hi', 'hey']):
                        ai_response = "Hello! I'm your AI assistant for AANR Knowledge Hub. I specialize in agriculture, aquaculture, and natural resources. What would you like to explore?"
                    elif any(word in query_lower for word in ['bye', 'goodbye']):
                        ai_response = "Goodbye! Thank you for using AANR Knowledge Hub. Have a wonderful day!"
                    elif any(word in query_lower for word in ['what are you', 'who are you']):
                        ai_response = "I'm an intelligent AI assistant created specifically for AANR Knowledge Hub. I help with agriculture, aquaculture, and natural resources information using advanced AI models."
                    elif any(word in query_lower for word in ['thank', 'thanks']):
                        ai_response = "You're very welcome! I'm glad I could help you with your questions about agriculture and natural resources."
                    else:
                        ai_response = f"{ai_response}\n\nI'm here to help with agriculture, aquaculture, and natural resources. What specific information are you looking for?"
                
                return {
                    'response': ai_response,
                    'confidence': 'high',
                    'suggestions': self._generate_conversational_suggestions(query_lower),
                    'matched_resources': [],
                    'ai_powered': True,
                    'local_ai': True,
                    'conversational': True,
                    'generated': True  
                }
                
            except Exception as e:
                print(f"DialoGPT conversation error: {e}")
        
        # Fallback to using manual conversation handling with raw models
        if self.ai_models.get('conversation_tokenizer') and self.ai_models.get('conversation_model'):
            try:
                import torch
                
                # Encode the conversation
                tokenizer = self.ai_models['conversation_tokenizer']
                model = self.ai_models['conversation_model']
                
                # Format input for DialoGPT
                input_text = f"{query}{tokenizer.eos_token}"
                input_ids = tokenizer.encode(input_text, return_tensors='pt')
                
                # Generate response
                with torch.no_grad():
                    output = model.generate(
                        input_ids,
                        max_length=input_ids.shape[1] + 50,
                        num_beams=2,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id,
                        early_stopping=True
                    )
                
                # Decode response
                response_ids = output[0][input_ids.shape[1]:]
                ai_response = tokenizer.decode(response_ids, skip_special_tokens=True).strip()
                
                # Enhance with domain-specific context
                if len(ai_response) < 10:  # If response is too short
                    ai_response = self._generate_domain_specific_response(query_lower)
                
                return {
                    'response': ai_response,
                    'confidence': 'high',
                    'suggestions': self._generate_conversational_suggestions(query_lower),
                    'matched_resources': [],
                    'ai_powered': True,
                    'local_ai': True,
                    'conversational': True,
                    'generated': True
                }
                
            except Exception as e:
                print(f"Manual conversation generation error: {e}")
        
        # Fallback to text generation with GPT-2
        if self.ai_models.get('text_generator'):
            try:
                # Create a domain-specific prompt
                prompt = f"As an AI assistant for agriculture and natural resources, when asked '{query}', I respond: "
                
                result = self.ai_models['text_generator'](
                    prompt,
                    max_length=len(prompt.split()) + 40,
                    num_return_sequences=1,
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=50256
                )
                
                generated_text = result[0]['generated_text']
                # Extract just the response part
                ai_response = generated_text.replace(prompt, "").strip()
                
                # Clean up common artifacts
                ai_response = ai_response.split('\n')[0]  # Take first line only
                if len(ai_response) < 10:
                    ai_response = self._generate_domain_specific_response(query_lower)
                
                return {
                    'response': ai_response,
                    'confidence': 'medium',
                    'suggestions': self._generate_conversational_suggestions(query_lower),
                    'matched_resources': [],
                    'ai_powered': True,
                    'local_ai': True,
                    'conversational': True,
                    'generated': True
                }
                
            except Exception as e:
                print(f"Text generation error: {e}")
        
        # Final fallback to Q&A model
        return self._generate_qa_conversational_response(query, intent_info)     

    def _generate_domain_specific_response(self, query_lower):
        """Generate domain-specific responses for agriculture/aquaculture topics"""
        if any(word in query_lower for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm your intelligent AI assistant for AANR Knowledge Hub. I can help you with agriculture, aquaculture, and natural resources. What would you like to know?"
        elif any(word in query_lower for word in ['bye', 'goodbye', 'see you']):
            return "Goodbye! Thank you for using AANR Knowledge Hub. Feel free to return anytime for more assistance with agriculture and aquaculture topics!"
        elif any(word in query_lower for word in ['what are you', 'who are you']):
            return "I'm an intelligent AI assistant designed specifically for AANR Knowledge Hub. I use advanced language models to help you find information about agriculture, aquaculture, and natural resources."
        elif any(word in query_lower for word in ['thank', 'thanks']):
            return "You're very welcome! I'm glad I could assist you. If you have more questions about agriculture, aquaculture, or natural resources, feel free to ask!"
        elif any(word in query_lower for word in ['help', 'what can you do']):
            return "I can help you with a wide range of topics related to agriculture, aquaculture, and natural resources. Try asking me about farming techniques, fish farming, CMI locations, or any specific questions you have!"
        else:
            return "I understand you're looking for information. I specialize in agriculture, aquaculture, and natural resources. What specific topic would you like to explore?" 

    def _generate_qa_conversational_response(self, query, intent_info):
        """Use Q&A model for conversational responses (current implementation)"""
        # Your existing Q&A-based conversation logic here
        if not self.ai_models.get('qa_pipeline'):
            return self._generate_fallback_conversational_response(query.lower())
        
        try:
            chatbot_context = """
            I am an intelligent AI assistant for AANR Knowledge Hub. I help users find information about:
            - Agriculture and farming resources and techniques
            - Aquaculture and fisheries information  
            - Community forum discussions and expert advice
            - CMI locations and services
            - Knowledge resources and publications
            - Training programs and events
            
            I can understand natural language and provide helpful, contextual responses.
            I use local AI models to ensure data privacy and security.
            """
            
            result = self.ai_models['qa_pipeline'](question=query, context=chatbot_context)
            ai_response = result['answer']
            confidence = result['score']
            
            return {
                'response': ai_response,
                'confidence': 'high' if confidence > 0.5 else 'medium',
                'suggestions': self._generate_conversational_suggestions(query.lower()),
                'matched_resources': [],
                'ai_powered': True,
                'local_ai': True,
                'conversational': True
            }
            
        except Exception as e:
            print(f"Q&A conversational error: {e}")
            return self._generate_fallback_conversational_response(query.lower())

    def _generate_fallback_conversational_response(self, query_lower):
        """Fallback conversational responses when AI fails"""
        if any(greeting in query_lower for greeting in ['hello', 'hi', 'hey']):
            return {
                'response': "👋 Hello! I'm your AI assistant for AANR Knowledge Hub. How can I help you today?",
                'confidence': 'high',
                'suggestions': ['What can you help with?', 'Show me farming resources', 'Find CMI locations'],
                'matched_resources': [],
                'ai_powered': False,
                'conversational': True
            }
        elif any(farewell in query_lower for farewell in ['bye', 'goodbye', 'see you']):
            return {
                'response': "👋 Goodbye! Thank you for using AANR Knowledge Hub. Have a wonderful day!",
                'confidence': 'high', 
                'suggestions': ['Hello again!', 'What topics are available?'],
                'matched_resources': [],
                'ai_powered': False,
                'conversational': True
            }
        elif any(thanks in query_lower for thanks in ['thank', 'thanks']):
            return {
                'response': "🙏 You're welcome! Happy to help with your agricultural and natural resource questions.",
                'confidence': 'high',
                'suggestions': ['Ask another question', 'Show me more resources'],
                'matched_resources': [],
                'ai_powered': False,
                'conversational': True
            }
        else:
            return {
                'response': "💬 I understand you're looking to chat. I'm here to help with agriculture, aquaculture, and natural resources. What would you like to know?",
                'confidence': 'medium',
                'suggestions': ['What can you help with?', 'Show me popular topics'],
                'matched_resources': [],
                'ai_powered': False,
                'conversational': True
            }

    def _generate_conversational_suggestions(self, query_lower):
        """Generate suggestions based on conversational context"""
        if 'hello' in query_lower or 'hi' in query_lower:
            return [
                'What can you help me with?',
                'Give me sample 1 FAQ',
                'Show me farming resources'
            ]
        elif 'bye' in query_lower or 'goodbye' in query_lower:
            return [
                'Hello again!',
                'What topics are available?',
                'Show me popular resources'
            ]
        elif 'thank' in query_lower:
            return [
                'Ask another question',
                'Find more resources',
                'Show me different topics'
            ]
        else:
            return [
                'What can you help with?',
                'Browse available topics',
                'Find specific information'
            ]

    def _generate_sample_response(self, query, matched_resources, intent_info):
        """Generate response for sample requests"""
        if not matched_resources:
            return {
                'response': "I couldn't find any samples matching your request. Here are some available options:\n\n📚 Browse our knowledge base\n💬 Check forum discussions\n❓ View frequently asked questions\n🏢 Find CMI locations",
                'confidence': 'low',
                'suggestions': [
                    'Show me popular FAQs',
                    'Find recent forum posts', 
                    'Browse knowledge resources',
                    'What topics are available?'
                ],
                'matched_resources': []
            }
        
        response_parts = []
        query_lower = query.lower()
        
        # Determine what type of sample was requested
        if 'faq' in query_lower:
            response_parts.append("❓ **Here are sample FAQs:**")
        elif 'forum' in query_lower:
            response_parts.append("💬 **Here are sample forum discussions:**")
        elif 'resource' in query_lower:
            response_parts.append("📄 **Here are sample resources:**")
        else:
            response_parts.append("📚 **Here are some examples from our knowledge base:**")
        
        response_parts.append("")
        
        # List the samples
        for i, match in enumerate(matched_resources, 1):
            resource = match['resource']
            resource_type = resource.get('type', 'item')
            
            # Add type icon
            type_icons = {
                'faq': '❓', 'forum': '💬', 'resource': '📄',
                'commodity': '🌾', 'cmi': '🏢', 'category': '📚'
            }
            icon = type_icons.get(resource_type, '📌')
            
            title = resource['title'][:60] + '...' if len(resource['title']) > 60 else resource['title']
            response_parts.append(f"{i}. {icon} **{title}**")
            
            # Add brief description
            desc = resource['description'][:100] + '...' if len(resource['description']) > 100 else resource['description']
            response_parts.append(f"   {desc}")
            response_parts.append("")
        
        # Generate suggestions
        suggestions = [
            "Show me more examples",
            "Find specific topic samples",
            "Browse different categories",
            "What other types are available?"
        ]
        
        return {
            'response': '\n'.join(response_parts),
            'confidence': 'high',
            'suggestions': suggestions,
            'matched_resources': [match['resource'] for match in matched_resources],
            'ai_powered': True,
            'local_ai': True
        }

    def _generate_no_results_response(self, query):
        """Generate helpful response when no results found"""
        return {
            'response': f"I couldn't find specific information about '{query}'. Try asking about agriculture, aquaculture, CMI services, or browse our available resources.\n\n🌾 Agricultural resources and techniques\n🐟 Aquaculture and fisheries information\n💬 Community forum discussions\n❓ Frequently asked questions\n🏢 CMI locations and services",
            'confidence': 'low',
            'suggestions': ["Browse available topics", "Find popular discussions", "Show CMI locations"],
            'matched_resources': []
        }

    def _generate_fallback_response(self, query, similar_content):
        """Fallback when AI models fail"""
        if similar_content:
            best_match = similar_content[0]
            resource = best_match['resource']
            
            return {
                'response': f"📚 **{resource['title']}**\n\n{resource['description']}",
                'confidence': 'medium',
                'suggestions': ["Tell me more about this", "Find related content", "Ask another question"],
                'matched_resources': [resource],
                'ai_powered': False
            }
        else:
            return self._generate_no_results_response(query)

    def _get_confidence_level(self, similarity_score):
        """Get confidence level based on similarity score"""
        if similarity_score >= 0.7:
            return 'high'
        elif similarity_score >= 0.4:
            return 'medium'
        else:
            return 'low'

    # Include all your existing methods here with minor modifications...
    def _load_custom_stopwords(self):
        """Load custom stopwords from your stopwords file + spaCy stopwords"""
        custom_stops = set()
        
        # Load from your custom stopwords file
        try:
            with open('utils/stopwords/stopwords.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith('//'):
                        custom_stops.add(word)
        except FileNotFoundError:
            print("Custom stopwords file not found, using default")
        
        # Add spaCy stopwords
        if self.nlp:
            custom_stops.update(STOP_WORDS)
        
        # Add domain-specific stopwords for agriculture
        domain_stops = {
            'said', 'says', 'also', 'would', 'could', 'should', 'may', 'might',
            'one', 'two', 'three', 'many', 'much', 'more', 'most', 'some', 'any',
            'new', 'old', 'good', 'bad', 'big', 'small', 'high', 'low', 'first',
            'last', 'next', 'previous', 'use', 'used', 'using', 'way', 'ways'
        }
        custom_stops.update(domain_stops)
        
        return custom_stops

    def _load_knowledge_base(self):
        """Load comprehensive knowledge base with advanced AI processing"""
        self.knowledge_data = []
        self.document_texts = []
        
        try:
            print("Loading knowledge base with advanced AI processing...")
            
            # 1. Load Resource Metadata
            resources = ResourceMetadata.objects.filter(is_approved=True)
            print(f"Found {resources.count()} approved resources")
            
            for resource in resources:
                try:
                    tags = [tag.name for tag in resource.tags.all()]
                    commodities = [commodity.commodity_name for commodity in resource.commodities.all()]
                    
                    # Create combined text for NLP processing
                    combined_text = f"{resource.title} {resource.description} {' '.join(tags)} {' '.join(commodities)}"
                    
                    knowledge_item = {
                        'id': f"resource_{resource.id}",
                        'actual_id': resource.id,
                        'title': resource.title,
                        'description': resource.description,
                        'type': 'resource',
                        'resource_type': resource.resource_type,
                        'slug': resource.slug,
                        'url': f'/cmis/knowledge-resources/post/{resource.slug}/',
                        'tags': tags,
                        'commodities': commodities,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing resource {resource.id}: {e}")
                    continue

            # 2. Load Knowledge Categories
            knowledge_categories = KnowledgeResources.objects.filter(status='active')
            print(f"Found {knowledge_categories.count()} knowledge categories")
            
            for category in knowledge_categories:
                combined_text = f"{category.knowledge_title} {category.knowledge_description}"
                
                knowledge_item = {
                    'id': f"category_{category.knowledge_id}",
                    'actual_id': category.knowledge_id,
                    'title': category.knowledge_title,
                    'description': category.knowledge_description,
                    'type': 'category',
                    'slug': category.slug,
                    'url': f'/cmis/knowledge-resources/?type={category.machine_name}',
                    'raw_text': combined_text
                }
                
                self.knowledge_data.append(knowledge_item)
                self.document_texts.append(combined_text)

            # 3. Load Commodities
            commodities = Commodity.objects.filter(status='active')
            print(f"Found {commodities.count()} commodities")
            
            for commodity in commodities:
                combined_text = f"{commodity.commodity_name} {commodity.description}"
                
                knowledge_item = {
                    'id': f"commodity_{commodity.commodity_id}",
                    'actual_id': commodity.commodity_id,
                    'title': commodity.commodity_name,
                    'description': commodity.description,
                    'type': 'commodity',
                    'slug': commodity.slug,
                    'url': f'/cmis/commodities/{commodity.slug}',
                    'raw_text': combined_text
                }
                
                self.knowledge_data.append(knowledge_item)
                self.document_texts.append(combined_text)

            # 4. Load Events
            events = Event.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {events.count()} events")
            
            for event in events:
                try:
                    combined_text = f"{event.metadata.title} {event.metadata.description} {event.location} {event.organizer}"
                    
                    knowledge_item = {
                        'id': f"event_{event.id}",
                        'actual_id': event.id,
                        'title': event.metadata.title,
                        'description': f"{event.metadata.description} Location: {event.location}, Organizer: {event.organizer}",
                        'type': 'event',
                        'slug': event.slug,
                        'url': f'/cmis/knowledge-resources/events/{event.slug}/',
                        'location': event.location,
                        'organizer': event.organizer,
                        'start_date': event.start_date.strftime('%Y-%m-%d %H:%M'),
                        'end_date': event.end_date.strftime('%Y-%m-%d %H:%M'),
                        'is_virtual': event.is_virtual,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing event {event.id}: {e}")
                    continue

            # 5. Load Information Systems
            info_systems = InformationSystem.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {info_systems.count()} information systems")
            
            for info_system in info_systems:
                try:
                    combined_text = f"{info_system.metadata.title} {info_system.metadata.description} {info_system.system_owner}"
                    
                    knowledge_item = {
                        'id': f"info_system_{info_system.id}",
                        'actual_id': info_system.id,
                        'title': info_system.metadata.title,
                        'description': f"{info_system.metadata.description} Owner: {info_system.system_owner}",
                        'type': 'info_system',
                        'slug': info_system.slug,
                        'url': info_system.website_url,
                        'system_owner': info_system.system_owner,
                        'website_url': info_system.website_url,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing info system {info_system.id}: {e}")
                    continue

            # 6. Load Maps
            maps = Map.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {maps.count()} maps")
            
            for map_item in maps:
                try:
                    combined_text = f"{map_item.metadata.title} {map_item.metadata.description}"
                    
                    knowledge_item = {
                        'id': f"map_{map_item.id}",
                        'actual_id': map_item.id,
                        'title': map_item.metadata.title,
                        'description': map_item.metadata.description,
                        'type': 'map',
                        'slug': map_item.slug,
                        'url': f'/cmis/knowledge-resources/maps/{map_item.slug}/',
                        'map_url': map_item.map_url,
                        'latitude': float(map_item.latitude) if map_item.latitude else None,
                        'longitude': float(map_item.longitude) if map_item.longitude else None,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing map {map_item.id}: {e}")
                    continue

            # 7. Load Media
            media_items = Media.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {media_items.count()} media items")
            
            for media in media_items:
                try:
                    combined_text = f"{media.metadata.title} {media.metadata.description} {media.author} {media.media_type}"
                    
                    knowledge_item = {
                        'id': f"media_{media.id}",
                        'actual_id': media.id,
                        'title': media.metadata.title,
                        'description': f"{media.metadata.description} Type: {media.media_type}, Author: {media.author}",
                        'type': 'media',
                        'slug': media.slug,
                        'url': f'/cmis/knowledge-resources/media/{media.slug}/',
                        'media_type': media.media_type,
                        'author': media.author,
                        'media_url': media.media_url,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing media {media.id}: {e}")
                    continue

            # 8. Load News
            news_items = News.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {news_items.count()} news items")
            
            for news in news_items:
                try:
                    combined_text = f"{news.metadata.title} {news.metadata.description} {news.content} {news.source}"
                    
                    knowledge_item = {
                        'id': f"news_{news.id}",
                        'actual_id': news.id,
                        'title': news.metadata.title,
                        'description': f"{news.content[:200]}... Source: {news.source}",
                        'type': 'news',
                        'slug': news.slug,
                        'url': f'/cmis/knowledge-resources/news/{news.slug}/',
                        'publication_date': news.publication_date.strftime('%Y-%m-%d'),
                        'source': news.source,
                        'external_url': news.external_url,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing news {news.id}: {e}")
                    continue

            # 9. Load Policies
            policies = Policy.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {policies.count()} policies")
            
            for policy in policies:
                try:
                    combined_text = f"{policy.metadata.title} {policy.metadata.description} {policy.issuing_body} {policy.policy_number}"
                    
                    knowledge_item = {
                        'id': f"policy_{policy.id}",
                        'actual_id': policy.id,
                        'title': policy.metadata.title,
                        'description': f"{policy.metadata.description} Issued by: {policy.issuing_body}",
                        'type': 'policy',
                        'slug': policy.slug,
                        'url': f'/cmis/knowledge-resources/policies/{policy.slug}/',
                        'policy_number': policy.policy_number,
                        'effective_date': policy.effective_date.strftime('%Y-%m-%d'),
                        'issuing_body': policy.issuing_body,
                        'status': policy.status,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing policy {policy.id}: {e}")
                    continue

            # 10. Load Projects
            projects = Project.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {projects.count()} projects")
            
            for project in projects:
                try:
                    combined_text = f"{project.metadata.title} {project.metadata.description} {project.project_lead} {project.funding_source}"
                    
                    knowledge_item = {
                        'id': f"project_{project.id}",
                        'actual_id': project.id,
                        'title': project.metadata.title,
                        'description': f"{project.metadata.description} Lead: {project.project_lead}",
                        'type': 'project',
                        'slug': project.slug,
                        'url': f'/cmis/knowledge-resources/projects/{project.slug}/',
                        'project_lead': project.project_lead,
                        'start_date': project.start_date.strftime('%Y-%m-%d'),
                        'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else None,
                        'funding_source': project.funding_source,
                        'status': project.status,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing project {project.id}: {e}")
                    continue

            # 11. Load Publications
            publications = Publication.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {publications.count()} publications")
            
            for publication in publications:
                try:
                    combined_text = f"{publication.metadata.title} {publication.metadata.description} {publication.authors} {publication.publisher}"
                    
                    knowledge_item = {
                        'id': f"publication_{publication.id}",
                        'actual_id': publication.id,
                        'title': publication.metadata.title,
                        'description': f"{publication.metadata.description} Authors: {publication.authors}",
                        'type': 'publication',
                        'slug': publication.slug,
                        'url': f'/cmis/knowledge-resources/publications/{publication.slug}/',
                        'authors': publication.authors,
                        'publication_date': publication.publication_date.strftime('%Y-%m-%d'),
                        'publisher': publication.publisher,
                        'publication_type': publication.publication_type,
                        'doi': publication.doi,
                        'isbn': publication.isbn,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing publication {publication.id}: {e}")
                    continue

            # 12. Load Technologies
            technologies = Technology.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {technologies.count()} technologies")
            
            for technology in technologies:
                try:
                    combined_text = f"{technology.metadata.title} {technology.metadata.description} {technology.developer}"
                    
                    knowledge_item = {
                        'id': f"technology_{technology.id}",
                        'actual_id': technology.id,
                        'title': technology.metadata.title,
                        'description': f"{technology.metadata.description} Developer: {technology.developer}",
                        'type': 'technology',
                        'slug': technology.slug,
                        'url': f'/cmis/knowledge-resources/technologies/{technology.slug}/',
                        'developer': technology.developer,
                        'release_date': technology.release_date.strftime('%Y-%m-%d') if technology.release_date else None,
                        'patent_number': technology.patent_number,
                        'license_type': technology.license_type,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing technology {technology.id}: {e}")
                    continue

            # 13. Load Training/Seminars
            trainings = TrainingSeminar.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {trainings.count()} training/seminars")
            
            for training in trainings:
                try:
                    combined_text = f"{training.metadata.title} {training.metadata.description} {training.trainers} {training.target_audience}"
                    
                    knowledge_item = {
                        'id': f"training_{training.id}",
                        'actual_id': training.id,
                        'title': training.metadata.title,
                        'description': f"{training.metadata.description} Target: {training.target_audience}",
                        'type': 'training',
                        'slug': training.slug,
                        'url': f'/cmis/knowledge-resources/trainings/{training.slug}/',
                        'location': training.location,
                        'trainers': training.trainers,
                        'target_audience': training.target_audience,
                        'start_date': training.start_date.strftime('%Y-%m-%d %H:%M'),
                        'end_date': training.end_date.strftime('%Y-%m-%d %H:%M'),
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing training {training.id}: {e}")
                    continue

            # 14. Load Webinars
            webinars = Webinar.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {webinars.count()} webinars")
            
            for webinar in webinars:
                try:
                    combined_text = f"{webinar.metadata.title} {webinar.metadata.description} {webinar.presenters} {webinar.platform}"
                    
                    knowledge_item = {
                        'id': f"webinar_{webinar.id}",
                        'actual_id': webinar.id,
                        'title': webinar.metadata.title,
                        'description': f"{webinar.metadata.description} Platform: {webinar.platform}",
                        'type': 'webinar',
                        'slug': webinar.slug,
                        'url': f'/cmis/knowledge-resources/webinars/{webinar.slug}/',
                        'webinar_date': webinar.webinar_date.strftime('%Y-%m-%d %H:%M'),
                        'duration_minutes': webinar.duration_minutes,
                        'platform': webinar.platform,
                        'presenters': webinar.presenters,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing webinar {webinar.id}: {e}")
                    continue

            # 15. Load Products
            products = Product.objects.select_related('metadata').filter(metadata__is_approved=True)
            print(f"Found {products.count()} products")
            
            for product in products:
                try:
                    combined_text = f"{product.metadata.title} {product.metadata.description} {product.manufacturer} {product.features}"
                    
                    knowledge_item = {
                        'id': f"product_{product.id}",
                        'actual_id': product.id,
                        'title': product.metadata.title,
                        'description': f"{product.metadata.description} Manufacturer: {product.manufacturer}",
                        'type': 'product',
                        'slug': product.slug,
                        'url': f'/cmis/knowledge-resources/products/{product.slug}/',
                        'manufacturer': product.manufacturer,
                        'features': product.features,
                        'technical_specifications': product.technical_specifications,
                        'price': float(product.price) if product.price else None,
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing product {product.id}: {e}")
                    continue

            # 16. Load Forum Discussions
            forums = Forum.objects.all()
            print(f"Found {forums.count()} forum discussions")
            
            for forum in forums:
                try:
                    forum_commodities = [commodity.commodity_name for commodity in forum.commodity_id.all()]
                    combined_text = f"{forum.forum_title} {forum.forum_question} {' '.join(forum_commodities)}"
                    
                    knowledge_item = {
                        'id': f"forum_{forum.forum_id}",
                        'actual_id': forum.forum_id,
                        'title': forum.forum_title,
                        'description': forum.forum_question,
                        'type': 'forum',
                        'slug': forum.slug,
                        'url': f'/cmi/forum/{forum.slug}/',
                        'author': f"{forum.author.first_name} {forum.author.last_name}",
                        'commodities': forum_commodities,
                        'date_posted': forum.date_posted.strftime('%Y-%m-%d'),
                        'total_likes': forum.total_likes(),
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing forum {forum.forum_id}: {e}")
                    continue

            # 17. Load CMI Data
            cmis = CMI.objects.filter(status='active')
            print(f"Found {cmis.count()} CMI entries")
            
            for cmi in cmis:
                combined_text = f"{cmi.cmi_name} {cmi.cmi_meaning} {cmi.cmi_description} {cmi.address}"
                
                knowledge_item = {
                    'id': f"cmi_{cmi.cmi_id}",
                    'actual_id': cmi.cmi_id,
                    'title': cmi.cmi_name,
                    'description': f"{cmi.cmi_meaning}. {cmi.cmi_description}",
                    'type': 'cmi',
                    'slug': cmi.slug,
                    'location': cmi.address,
                    'contact': cmi.contact_num,
                    'email': cmi.email,
                    'url': f'/cmis/about-km/',
                    'latitude': float(cmi.latitude) if cmi.latitude else None,
                    'longitude': float(cmi.longitude) if cmi.longitude else None,
                    'date_joined': cmi.date_joined.strftime('%Y-%m-%d') if cmi.date_joined else None,
                    'raw_text': combined_text
                }
                
                self.knowledge_data.append(knowledge_item)
                self.document_texts.append(combined_text)

            # 18. Load FAQ Data
            faqs = FAQ.objects.filter(is_active=True)
            print(f"Found {faqs.count()} FAQ entries")
            
            for faq in faqs:
                combined_text = f"{faq.question} {faq.answer}"
                
                knowledge_item = {
                    'id': f"faq_{faq.faq_id}",
                    'actual_id': faq.faq_id,
                    'title': faq.question,  
                    'description': faq.answer,  
                    'question': faq.question,  
                    'answer': faq.answer,      
                    'type': 'faq',
                    'slug': faq.slug,
                    'url': f'/cmis/faqs/', 
                    'created_by': f"{faq.created_by.first_name} {faq.created_by.last_name}",
                    'created_at': faq.created_at.strftime('%Y-%m-%d'),
                    'total_reactions': faq.total_reactions(),
                    'raw_text': combined_text
                }
                
                self.knowledge_data.append(knowledge_item)
                self.document_texts.append(combined_text)

            # Create TF-IDF vectors if we have content
            if self.document_texts:
                try:
                    self.knowledge_vectors = self.vectorizer.fit_transform(self.document_texts)
                    print(f"✅ Created TF-IDF vectors for {len(self.document_texts)} documents")
                except Exception as e:
                    print(f"⚠️ Could not create TF-IDF vectors: {e}")
                    self.knowledge_vectors = None

            # Create AI embeddings if models are available
            if self.ai_models.get('sentence_transformer'):
                try:
                    self._create_knowledge_embeddings()
                    print("✅ Created AI embeddings for semantic search")
                except Exception as e:
                    print(f"⚠️ Could not create AI embeddings: {e}")

            print(f"🎉 Successfully loaded {len(self.knowledge_data)} items into knowledge base")
            print(f"📊 Breakdown:")
            type_counts = {}
            for item in self.knowledge_data:
                item_type = item['type']
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            for item_type, count in sorted(type_counts.items()):
                print(f"   - {item_type}: {count}")
                
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            print(f"❌ Error loading knowledge base: {e}")

    def _create_knowledge_embeddings(self):
        """Create embeddings for all knowledge items using sentence transformer"""
        if not self.ai_models.get('sentence_transformer'):
            return
        
        try:
            print("🧠 Creating AI embeddings for semantic search...")
            embeddings = self.ai_models['sentence_transformer'].encode(self.document_texts)
            self.knowledge_embeddings = embeddings
            print(f"✅ Created embeddings for {len(self.document_texts)} documents")
        except Exception as e:
            print(f"❌ Error creating embeddings: {e}")
            self.knowledge_embeddings = None

    # Wrapper method for backward compatibility
    def find_similar_content(self, query, threshold=0.05, top_k=5):
        """Wrapper for enhanced semantic search"""
        intent_info = self._classify_user_intent(query)
        return self._enhanced_semantic_search(query, intent_info, top_k)

    # Main entry point - calls the intelligent version
    def generate_response(self, query):
        """Main response generation - now uses AI intelligence"""
        return self.generate_intelligent_response(query)

# Create the intelligent chatbot service
chatbot_service = IntelligentChatbotService()