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
            
            # 1. Sentence embeddings for semantic search (23MB model)
            self.ai_models['sentence_transformer'] = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Loaded sentence transformer model")
            
            # 2. Intent classification pipeline
            self.ai_models['intent_classifier'] = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            print("✅ Loaded intent classification model")
            
            # 3. Question-answering model for dynamic answers
            self.ai_models['qa_pipeline'] = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad",
                device=0 if torch.cuda.is_available() else -1
            )
            print("✅ Loaded question-answering model")
            
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
                "asking about CMI services"
            ]
            
            result = self.ai_models['intent_classifier'](query, candidate_labels)
            
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
                "asking about CMI services": "cmi_query"
            }
            
            top_intent = result['labels'][0]
            confidence = result['scores'][0]
            
            return {
                'intent': intent_mapping.get(top_intent, "general_query"),
                'confidence': confidence,
                'raw_classification': result
            }
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            return self._classify_intent_basic(query)
        

    def _classify_intent_basic(self, query):
        """Basic intent classification using patterns"""
        query_lower = query.lower()
        
        # Conversational/Social interactions
        if any(word in query_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'bye', 'goodbye', 'thanks', 'thank you', 'help', 'what can you', 'what do you']):
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
        
        # Default
        else:
            return {'intent': 'general_query', 'confidence': 0.5}

    def _enhanced_semantic_search(self, query, intent_info, top_k=5):
        """Enhanced semantic search using local AI"""
        if not self.ai_models.get('sentence_transformer'):
            return self.find_similar_content(query, top_k=top_k)
        
        try:
            # Handle special intents
            if intent_info['intent'] == 'sample_request':
                return self._handle_sample_request(query, top_k)
            
            # Get query embedding
            query_embedding = self.ai_models['sentence_transformer'].encode([query])
            
            # Get embeddings for all knowledge items (cache these for performance)
            if not hasattr(self, 'knowledge_embeddings'):
                print("🔄 Creating knowledge embeddings...")
                knowledge_texts = []
                for item in self.knowledge_data:
                    # Combine title and description for better context
                    text = f"{item['title']} {item['description']}"
                    knowledge_texts.append(text)
                
                self.knowledge_embeddings = self.ai_models['sentence_transformer'].encode(knowledge_texts)
                print(f"✅ Created embeddings for {len(knowledge_texts)} knowledge items")
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, self.knowledge_embeddings)[0]
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:top_k * 2]  # Get more for filtering
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
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
            return self.find_similar_content(query, top_k=top_k)

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
        
        # 1. ALWAYS classify user intent using AI first (no hardcoded checks!)
        intent_info = self._classify_user_intent(query)
        print(f"🧠 Detected intent: {intent_info}")
        
        # 2. Handle based on AI-detected intent
        if intent_info['intent'] == 'general_conversation':
            return self._generate_conversational_response(query, intent_info)
        elif intent_info['intent'] == 'sample_request':
            matched_resources = self._enhanced_semantic_search(query, intent_info, top_k=5)
            return self._generate_sample_response(query, matched_resources, intent_info)
        else:
            # For all other intents, do semantic search and generate response
            matched_resources = self._enhanced_semantic_search(query, intent_info, top_k=5)
            print(f"🔍 Found {len(matched_resources)} matches")
            
            if matched_resources and len(matched_resources) > 0:
                return self._generate_qa_response(query, matched_resources)
            else:
                return self._generate_no_results_response(query)
            
    def _generate_conversational_response(self, query, intent_info):
        """Generate natural conversational responses using AI"""
        query_lower = query.lower()
        
        # Use transformers to understand the conversational context
        if not self.ai_models.get('qa_pipeline'):
            return self._generate_fallback_conversational_response(query_lower)
        
        try:
            # Create a context about the chatbot's capabilities
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
            
            # Let the AI generate a natural response
            result = self.ai_models['qa_pipeline'](
                question=query, 
                context=chatbot_context
            )
            
            ai_response = result['answer']
            confidence = result['score']
            
            # Enhance the AI response based on query type
            if any(greeting in query_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
                enhanced_response = f"👋 {ai_response}\n\n✨ I'm powered by local AI models for secure, intelligent assistance. What would you like to know about agriculture, aquaculture, or natural resources?"
                
            elif any(farewell in query_lower for farewell in ['bye', 'goodbye', 'see you', 'farewell']):
                enhanced_response = f"👋 {ai_response}\n\n✨ Thank you for using AANR Knowledge Hub! Feel free to return anytime for more assistance with agriculture, aquaculture, or natural resources. Have a great day! 😊"
                
            elif any(thanks in query_lower for thanks in ['thank', 'thanks', 'appreciate']):
                enhanced_response = f"🙏 {ai_response}\n\n✨ I'm glad I could help! If you have more questions about our knowledge resources, feel free to ask."
                
            elif any(help_word in query_lower for help_word in ['help', 'what can you', 'what do you', 'capabilities']):
                enhanced_response = f"🤖 {ai_response}\n\n🧠 **My AI Capabilities:**\n• Natural language understanding\n• Intent detection and classification\n• Semantic search across all content\n• Contextual response generation\n\n💡 **Try asking me:**\n• \"Give me sample 1 FAQ\"\n• \"Show me farming resources\"\n• \"Where are CMI locations?\""
                
            else:
                # For other conversational queries, use the AI response directly
                enhanced_response = f"💬 {ai_response}\n\n✨ Is there anything specific about agriculture, aquaculture, or natural resources you'd like to explore?"
            
            return {
                'response': enhanced_response,
                'confidence': 'high' if confidence > 0.5 else 'medium',
                'suggestions': self._generate_conversational_suggestions(query_lower),
                'matched_resources': [],
                'ai_powered': True,
                'local_ai': True,
                'conversational': True
            }
            
        except Exception as e:
            print(f"Conversational AI error: {e}")
            return self._generate_fallback_conversational_response(query_lower)

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
                    'url': f'/cmis/commodities/{commodity.slug}',
                    'raw_text': combined_text
                }
                
                self.knowledge_data.append(knowledge_item)
                self.document_texts.append(combined_text)

            # 4. Load Forum Discussions
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
                        'raw_text': combined_text
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(combined_text)
                    
                except Exception as e:
                    print(f"Error processing forum {forum.forum_id}: {e}")
                    continue

            # 5. Load CMI Data
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
                    'location': cmi.address,
                    'contact': cmi.contact_num,
                    'email': cmi.email,
                    'url': f'/cmis/about-km/',
                    'raw_text': combined_text
                }
                
                self.knowledge_data.append(knowledge_item)
                self.document_texts.append(combined_text)

            # 6. Load FAQ Data
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
                    'raw_text': combined_text
                }
                
                self.knowledge_data.append(knowledge_item)
                self.document_texts.append(combined_text)

            print(f"Successfully loaded {len(self.knowledge_data)} items with AI processing")
                
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            print(f"Error loading knowledge base: {e}")

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