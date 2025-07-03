import re
import json
import logging
import random
import numpy as np
from django.db import models
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy

from appAdmin.models import (
    ResourceMetadata, KnowledgeResources, Commodity, 
    Event, InformationSystem, Map, Media, News, Policy,
    Project, Publication, Technology, TrainingSeminar, Webinar, Product,
    CMI  
)
from appCmi.models import (
    Forum, ForumComment, FAQ
)

# Import for local AI
try:
    from sentence_transformers import SentenceTransformer
    from transformers import pipeline
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

def load_stopwords():
    """Load custom stopwords from stopwords.txt file"""
    stopwords = set()
    
    try:
        with open('utils/stopwords/stopwords.txt', 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word and not word.startswith('//'):
                    stopwords.add(word)
        print(f"✅ Loaded {len(stopwords)} custom stopwords")
    except FileNotFoundError:
        print("⚠️ Custom stopwords file not found, using default English stopwords")
        stopwords = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
    
    return stopwords

def load_basic_responses():
    """Load basic responses from JSON file"""
    try:
        with open('chatbot/data/basic-response.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ Basic response file not found, using default responses")
        return {
            "greetings": {
                "hello": {
                    "patterns": ["hello", "hi", "hey", "good morning", "good afternoon"],
                    "responses": ["👋 Hello! I'm your AI assistant for AANR Knowledge Hub. How can I help you today?"]
                },
                "goodbye": {
                    "patterns": ["bye", "goodbye", "see you"],
                    "responses": ["👋 Goodbye! Thank you for using AANR Knowledge Hub. Have a wonderful day!"]
                },
                "thanks": {
                    "patterns": ["thank you", "thanks", "thank u"],
                    "responses": ["🙏 You're very welcome! Happy to help with your questions."]
                },
                "help": {
                    "patterns": ["help", "what can you do", "how can you help"],
                    "responses": ["🤖 I can help you with agriculture, aquaculture, and natural resources."]
                }
            }
        }

logger = logging.getLogger(__name__)

class IntelligentChatbotService:

    def __init__(self):
        self.knowledge_data = []
        
        # Load stopwords and basic responses using functions
        self.stopwords = load_stopwords()
        self.basic_responses = load_basic_responses()
        
        # Initialize TF-IDF vectorizer with custom stopwords
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words=list(self.stopwords),
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8
        )
        self.knowledge_vectors = None
        self.document_texts = []
        
        # Initialize spaCy model for NLP text matching
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
        
        # Initialize single AI model for understanding user input
        self.ai_model = None
        if TRANSFORMERS_AVAILABLE:
            self._initialize_ai_model()
        
        self.knowledge_base_loaded = False
        self.knowledge_embeddings = None
        self._conversation_cache = {}

    def _initialize_ai_model(self):
        """Initialize single AI model for user input understanding"""
        try:
            print("🧠 Loading AI model for user input understanding...")
            
            # Single model for intent classification and semantic understanding
            self.ai_model = {
                'sentence_transformer': SentenceTransformer('all-MiniLM-L6-v2'),
                'intent_classifier': pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=0 if torch.cuda.is_available() else -1
                )
            }
            
            print("✅ AI model loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading AI model: {e}")
            print("💡 Falling back to basic NLP processing")
            self.ai_model = None

    def _ensure_knowledge_base_loaded(self):
        """Lazy load knowledge base only when needed"""
        if not self.knowledge_base_loaded:
            print("📚 Loading knowledge base (first time)...")
            self._load_knowledge_base()
            self.knowledge_base_loaded = True

    def _classify_user_intent(self, query):
        """Classify user intent using AI model"""
        # First check for basic responses
        basic_intent = self._check_basic_response(query)
        if basic_intent:
            return basic_intent
        
        if not self.ai_model:
            return self._classify_intent_basic(query)
        
        try:
            # Define possible intents
            candidate_labels = [
                "request for examples or samples",
                "looking for specific information", 
                "asking for location or contact details",
                "requesting farming or agricultural advice",
                "seeking aquaculture information",
                "asking about training programs",
                "browsing or exploring content",
                "asking about CMI services",
                "content discovery for specific topic"
            ]
            
            result = self.ai_model['intent_classifier'](query, candidate_labels)
            
            main_topic = self._extract_main_topic(query)
            content_type = self._extract_content_type(query)
            
            # Map to our internal intent system
            intent_mapping = {
                "request for examples or samples": "sample_request",
                "looking for specific information": "specific_query",
                "asking for location or contact details": "location_query",
                "requesting farming or agricultural advice": "agriculture_query", 
                "seeking aquaculture information": "aquaculture_query",
                "asking about training programs": "program_query",
                "browsing or exploring content": "browse_request",
                "asking about CMI services": "cmi_query",
                "content discovery for specific topic": "topic_content_request"
            }
            
            top_intent = result['labels'][0]
            confidence = result['scores'][0]
            
            detected_intent = intent_mapping.get(top_intent, "topic_content_request")
        
            return {
                'intent': detected_intent,
                'confidence': confidence,
                'main_topic': main_topic,
                'content_type': content_type,
                'is_basic': False
            }
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            return self._classify_intent_basic(query)

    def _check_basic_response(self, query):
        """Check if query matches basic response patterns"""
        query_lower = query.lower()
        
        for category, data in self.basic_responses.get('greetings', {}).items():
            patterns = data.get('patterns', [])
            for pattern in patterns:
                if pattern in query_lower:
                    return {
                        'intent': 'basic_response',
                        'category': category,
                        'confidence': 0.9,
                        'is_basic': True
                    }
        return None

    def _extract_main_topic(self, query):     
        """Extract the main topic/subject from the query using NLP and stopwords filtering"""
        if not query:
            return None
            
        # Remove stopwords and extract meaningful terms
        words = query.lower().split()
        meaningful_words = [word for word in words if word not in self.stopwords and len(word) > 2]
        
        if not meaningful_words:
            return None
        
        # Use spaCy for better entity recognition if available
        if self.nlp:
            doc = self.nlp(query)
            # Look for named entities first
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'GPE'] and len(ent.text) > 2:
                    return ent.text.upper()
            
            # Look for nouns
            nouns = [token.text for token in doc if token.pos_ == 'NOUN' and len(token.text) > 2]
            if nouns:
                return nouns[0].upper()
        
        # Domain-specific keywords priority
        domain_keywords = ['raise', 'agriculture', 'aquaculture', 'cmi', 'aanr', 'farming', 'fish', 'crop', 'livestock']
        for word in meaningful_words:
            if word.lower() in domain_keywords:
                return word.upper()
        
        # Return first meaningful word
        return meaningful_words[0].upper() if meaningful_words else None
    
    def _extract_content_type(self, query):
        """Extract what type of content is being requested"""
        query_lower = query.lower()
        
        content_types = {
            'faq': ['faq', 'question', 'answer'],
            'forum': ['forum', 'discussion', 'community'],
            'resource': ['resource', 'document', 'publication'],
            'training': ['training', 'seminar', 'course'],
            'event': ['event', 'workshop', 'conference'],
            'cmi': ['cmi', 'office', 'location']
        }
        
        for content_type, keywords in content_types.items():
            if any(keyword in query_lower for keyword in keywords):
                return content_type
        
        return 'general'

    def _classify_intent_basic(self, query):
        """Basic intent classification using patterns"""
        query_lower = query.lower()
        
        main_topic = self._extract_main_topic(query)
        content_type = self._extract_content_type(query)
        
        # Sample/example requests
        if any(word in query_lower for word in ['sample', 'example', 'show me', 'give me']):
            return {'intent': 'sample_request', 'confidence': 0.8, 'main_topic': main_topic, 'content_type': content_type}
        
        # Location requests
        elif any(word in query_lower for word in ['where', 'location', 'address', 'contact']):
            return {'intent': 'location_query', 'confidence': 0.7, 'main_topic': main_topic, 'content_type': content_type}
        
        # Agriculture requests
        elif any(word in query_lower for word in ['farm', 'crop', 'plant', 'agriculture']):
            return {'intent': 'agriculture_query', 'confidence': 0.7, 'main_topic': main_topic, 'content_type': content_type}
        
        # Default - if we have a topic, treat as topic request
        elif main_topic:
            return {'intent': 'topic_content_request', 'confidence': 0.6, 'main_topic': main_topic, 'content_type': content_type}
        else:
            return {'intent': 'general_query', 'confidence': 0.5, 'main_topic': main_topic, 'content_type': content_type}

    def _semantic_search_with_nlp(self, query, intent_info, top_k=5):
        """Enhanced semantic search using AI model and NLP for text matching"""
        if not self.ai_model:
            return self._nlp_text_matching(query, intent_info, top_k)
        
        try:
            # Handle different intents
            if intent_info['intent'] == 'topic_content_request':
                return self._handle_topic_content_request(query, intent_info, top_k)
            elif intent_info['intent'] == 'sample_request':
                return self._handle_sample_request(query, top_k)
            
            # Regular semantic search
            query_embedding = self.ai_model['sentence_transformer'].encode([query])
            
            if self.knowledge_embeddings is None:
                self._create_knowledge_embeddings()
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, self.knowledge_embeddings)[0]
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:top_k * 2]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:
                    item = self.knowledge_data[idx]
                    
                    # Use NLP for additional text matching score
                    nlp_score = self._calculate_nlp_score(query, item)
                    combined_score = (similarities[idx] * 0.7) + (nlp_score * 0.3)
                    
                    results.append({
                        'resource': item,
                        'similarity_score': float(combined_score),
                        'ai_score': float(similarities[idx]),
                        'nlp_score': nlp_score,
                        'confidence': self._get_confidence_level(combined_score)
                    })
            
            # Sort by combined score
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"Semantic search error: {e}")
            return self._nlp_text_matching(query, intent_info, top_k)

    def _nlp_text_matching(self, query, intent_info, top_k=5):
        """NLP-based text matching for database fetching"""
        results = []
        query_processed = preprocess_text(query)
        query_words = set(query_processed.split())
        
        # Remove stopwords from query
        query_words = query_words - self.stopwords
        
        if not query_words:
            return []
        
        for item in self.knowledge_data:
            score = self._calculate_nlp_score(query, item)
            
            if score > 0:
                results.append({
                    'resource': item,
                    'similarity_score': score,
                    'nlp_score': score,
                    'confidence': self._get_confidence_level(score)
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:top_k]

    def _calculate_nlp_score(self, query, item):
        """Calculate NLP-based similarity score between query and item"""
        score = 0
        query_processed = preprocess_text(query)
        title_processed = preprocess_text(item['title'])
        desc_processed = preprocess_text(item['description'])
        
        # Remove stopwords
        query_words = set(query_processed.split()) - self.stopwords
        title_words = set(title_processed.split()) - self.stopwords
        desc_words = set(desc_processed.split()) - self.stopwords
        
        if not query_words:
            return 0
        
        # Calculate word overlap scores
        title_overlap = len(query_words.intersection(title_words))
        desc_overlap = len(query_words.intersection(desc_words))
        
        # Weight title matches higher
        score += title_overlap * 3
        score += desc_overlap * 1
        
        # Use spaCy for semantic similarity if available
        if self.nlp:
            try:
                query_doc = self.nlp(query)
                item_doc = self.nlp(f"{item['title']} {item['description']}")
                semantic_score = query_doc.similarity(item_doc)
                score += semantic_score * 2
            except:
                pass
        
        # Normalize score
        max_possible_score = len(query_words) * 3 + 2  # Max title + semantic
        return min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0

    def _handle_topic_content_request(self, query, intent_info, top_k):
        """Handle requests for content about a specific topic"""
        main_topic = intent_info.get('main_topic')
        content_type = intent_info.get('content_type', 'general')
        
        if not main_topic:
            return self._nlp_text_matching(query, intent_info, top_k)
        
        results = []
        topic_lower = main_topic.lower()
        
        # Filter by content type if specified
        filtered_data = self.knowledge_data
        if content_type != 'general':
            filtered_data = [item for item in self.knowledge_data if item.get('type') == content_type]
        
        for item in filtered_data:
            score = 0
            title_lower = item['title'].lower()
            desc_lower = item['description'].lower()
            
            # Topic matching with higher scores for exact matches
            if topic_lower in title_lower:
                score += 5
            if topic_lower in desc_lower:
                score += 3
            
            # Word-level matching
            topic_words = topic_lower.split()
            for word in topic_words:
                if len(word) > 2 and word not in self.stopwords:
                    if word in title_lower:
                        score += 2
                    elif word in desc_lower:
                        score += 1
            
            if score > 0:
                results.append({
                    'resource': item,
                    'similarity_score': score,
                    'topic_score': score,
                    'confidence': 'high' if score >= 5 else 'medium' if score >= 2 else 'low'
                })
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:top_k]

    def _handle_sample_request(self, query, top_k):
        """Handle requests for samples/examples"""
        results = []
        query_lower = query.lower()
        
        # Extract what type of sample they want
        target_type = None
        if 'faq' in query_lower:
            target_type = 'faq'
        elif 'forum' in query_lower:
            target_type = 'forum'
        elif 'resource' in query_lower:
            target_type = 'resource'
        elif 'cmi' in query_lower:
            target_type = 'cmi'
        
        # Extract number if specified
        numbers = re.findall(r'\d+', query)
        requested_count = int(numbers[0]) if numbers else top_k
        
        # Filter by type if specified
        filtered_items = self.knowledge_data
        if target_type:
            filtered_items = [item for item in self.knowledge_data if item.get('type') == target_type]
        
        # Return the requested number of samples
        for i, item in enumerate(filtered_items[:requested_count]):
            results.append({
                'resource': item,
                'similarity_score': 1.0 - (i * 0.1),
                'confidence': 'high'
            })
        
        return results

    def find_similar_content(self, query, top_k=5):
        """Find similar content using NLP and AI models (for views.py compatibility)"""
        self._ensure_knowledge_base_loaded()
        
        # Basic intent info for compatibility
        intent_info = {
            'intent': 'general_query',
            'main_topic': self._extract_main_topic(query),
            'content_type': self._extract_content_type(query)
        }
        
        return self._semantic_search_with_nlp(query, intent_info, top_k)

    def _generate_basic_response(self, intent_info):
        """Generate response from basic response patterns"""
        category = intent_info.get('category', 'hello')
        responses = self.basic_responses.get('greetings', {}).get(category, {}).get('responses', [])
        
        if responses:
            response = random.choice(responses)
            
            # Generate appropriate suggestions based on category
            suggestions = []
            if category == 'hello':
                suggestions = ['What can you help me with?', 'Show me farming resources', 'Find CMI locations']
            elif category == 'help':
                suggestions = ['Give me sample 1 FAQ', 'Show me farming techniques', 'Find CMI offices']
            else:
                suggestions = ['Ask another question', 'Browse available topics', 'Find more resources']
            
            return {
                'response': response,
                'confidence': 'high',
                'suggestions': suggestions,
                'matched_resources': [],
                'ai_powered': False,
                'basic_response': True
            }
        
        return {
            'response': "Hello! How can I help you today?",
            'confidence': 'medium',
            'suggestions': ['What can you help with?'],
            'matched_resources': [],
            'ai_powered': False,
            'basic_response': True
        }

    def generate_intelligent_response(self, query):
        """Main method for generating intelligent responses"""
        query = query.strip()
        query_lower = query.lower()

        # Check cache first
        if query_lower in self._conversation_cache:
            return self._conversation_cache[query_lower]
        
        # Classify user intent
        intent_info = self._classify_user_intent(query)
        print(f"🧠 Detected intent: {intent_info}")
        
        # Handle basic responses
        if intent_info.get('is_basic'):
            response = self._generate_basic_response(intent_info)
            self._conversation_cache[query_lower] = response
            return response
        
        # Load knowledge base for complex queries
        self._ensure_knowledge_base_loaded()
        
        # Handle different intents
        if intent_info['intent'] == 'sample_request':
            matched_resources = self._semantic_search_with_nlp(query, intent_info, top_k=5)
            return self._generate_sample_response(query, matched_resources, intent_info)
        elif intent_info['intent'] == 'topic_content_request':
            matched_resources = self._semantic_search_with_nlp(query, intent_info, top_k=8)
            return self._generate_topic_content_response(query, matched_resources, intent_info)
        else:
            # Regular processing
            matched_resources = self._semantic_search_with_nlp(query, intent_info, top_k=5)
            print(f"🔍 Found {len(matched_resources)} matches")
            
            if matched_resources:
                return self._generate_detailed_response(query, matched_resources)
            else:
                return self._generate_no_results_response(query)

    def _generate_sample_response(self, query, matched_resources, intent_info):
        """Generate response for sample requests"""
        if not matched_resources:
            return {
                'response': "I couldn't find any samples matching your request. Here are some available options:\n\n📚 Browse our knowledge base\n💬 Check forum discussions\n❓ View frequently asked questions\n🏢 Find CMI locations",
                'confidence': 'low',
                'suggestions': ['Show me popular FAQs', 'Find recent forum posts', 'Browse knowledge resources'],
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
            
            type_icons = {
                'faq': '❓', 'forum': '💬', 'resource': '📄',
                'commodity': '🌾', 'cmi': '🏢', 'category': '📚'
            }
            icon = type_icons.get(resource_type, '📌')
            
            title = resource['title'][:60] + '...' if len(resource['title']) > 60 else resource['title']
            response_parts.append(f"{i}. {icon} **{title}**")
            
            desc = resource['description'][:100] + '...' if len(resource['description']) > 100 else resource['description']
            response_parts.append(f"   {desc}")
            response_parts.append("")
        
        return {
            'response': '\n'.join(response_parts),
            'confidence': 'high',
            'suggestions': ['Show me more examples', 'Find specific topic samples', 'Browse different categories'],
            'matched_resources': [match['resource'] for match in matched_resources],
            'ai_powered': True,
            'local_ai': True
        }

    def _generate_topic_content_response(self, query, matched_resources, intent_info):
        """Generate response specifically for topic content requests"""
        main_topic = intent_info.get('main_topic', 'the requested topic')
        content_type = intent_info.get('content_type', 'content')
        
        if not matched_resources:
            return {
                'response': f"I couldn't find specific {content_type} about '{main_topic}'. Try asking about related topics or browse our available resources.\n\n🌾 Agricultural resources\n🐟 Aquaculture information\n💬 Forum discussions\n❓ FAQs\n🏢 CMI services",
                'confidence': 'low',
                'suggestions': [f"Tell me about {main_topic.lower()}", f"Find {main_topic.lower()} resources"],
                'matched_resources': []
            }
        
        # Group results by type
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
            'category': {'icon': '📚', 'label': 'Knowledge Categories'},
            'event': {'icon': '📅', 'label': 'Events'},
            'training': {'icon': '🎓', 'label': 'Training Programs'},
            'news': {'icon': '📰', 'label': 'News'}
        }
        
        # Display grouped results
        for resource_type, matches in grouped_results.items():
            if matches:
                type_data = type_info.get(resource_type, {'icon': '📌', 'label': resource_type.title()})
                response_parts.append(f"{type_data['icon']} **{type_data['label']}:**")
                response_parts.append("")
                
                for i, match in enumerate(matches[:3], 1):
                    resource = match['resource']
                    title = resource['title'][:60] + '...' if len(resource['title']) > 60 else resource['title']
                    desc = resource['description'][:120] + '...' if len(resource['description']) > 120 else resource['description']
                    
                    response_parts.append(f"  **{i}. {title}**")
                    response_parts.append(f"     {desc}")
                    response_parts.append("")
        
        response_parts.append(f"💡 *Found {len(matched_resources)} results related to {main_topic}. Click any item above for details.*")
        
        return {
            'response': '\n'.join(response_parts),
            'confidence': 'high' if len(matched_resources) >= 3 else 'medium',
            'suggestions': [f"Tell me more about {main_topic.lower()}", "Find examples and samples", "Browse related topics"],
            'matched_resources': [match['resource'] for match in matched_resources],
            'ai_powered': True,
            'local_ai': True,
            'topic_focused': True
        }

    def _generate_detailed_response(self, query, matched_resources):
        """Generate detailed response from matched resources"""
        if not matched_resources:
            return self._generate_no_results_response(query)
        
        best_match = matched_resources[0]
        resource = best_match['resource']
        
        response_text = f"**{resource['title']}**\n\n{resource['description']}"
        
        # Add source information
        response_text += f"\n\n📋 **Source:** {resource['type'].title()}"
        if resource.get('author'):
            response_text += f" by {resource['author']}"
        
        return {
            'response': response_text,
            'confidence': best_match['confidence'],
            'suggestions': self._generate_dynamic_suggestions(query, matched_resources),
            'matched_resources': [resource],
            'ai_powered': True,
            'local_ai': True
        }

    def _generate_dynamic_suggestions(self, query, matched_resources):
        """Generate contextual suggestions"""
        suggestions = []
        query_words = query.lower().split()
        
        # Domain-specific suggestions
        if any(word in query_words for word in ['farm', 'crop', 'agriculture']):
            suggestions.extend(['Tell me about sustainable farming practices', 'Find crop disease management guides'])
        elif any(word in query_words for word in ['fish', 'aqua', 'tilapia']):
            suggestions.extend(['Show me fish farming techniques', 'What are common fish diseases?'])
        elif any(word in query_words for word in ['cmi', 'office', 'location']):
            suggestions.extend(['Find all CMI office locations', 'What services does CMI provide?'])
        
        # Fallback suggestions
        while len(suggestions) < 3:
            fallback = ['What can you help me with?', 'Show me popular topics', 'Find expert discussions']
            for sug in fallback:
                if sug not in suggestions:
                    suggestions.append(sug)
                    break
            break
        
        return suggestions[:3]

    def _generate_no_results_response(self, query):
        """Generate helpful response when no results found"""
        return {
            'response': f"I couldn't find specific information about '{query}'. Try asking about agriculture, aquaculture, CMI services, or browse our available resources.\n\n🌾 Agricultural resources and techniques\n🐟 Aquaculture and fisheries information\n💬 Community forum discussions\n❓ Frequently asked questions\n🏢 CMI locations and services",
            'confidence': 'low',
            'suggestions': ['Browse available topics', 'Find popular discussions', 'Show CMI locations'],
            'matched_resources': []
        }

    def _get_confidence_level(self, similarity_score):
        """Get confidence level based on similarity score"""
        if similarity_score >= 0.7:
            return 'high'
        elif similarity_score >= 0.4:
            return 'medium'
        else:
            return 'low'

    def _create_knowledge_embeddings(self):
        """Create embeddings for all knowledge items using AI model"""
        if not self.ai_model or not self.ai_model.get('sentence_transformer'):
            return
        
        if self.knowledge_embeddings is not None:
            return  

        try:
            print("🧠 Creating AI embeddings for semantic search...")
            embeddings = self.ai_model['sentence_transformer'].encode(self.document_texts)
            self.knowledge_embeddings = embeddings
            print(f"✅ Created embeddings for {len(self.document_texts)} documents")
        except Exception as e:
            print(f"❌ Error creating embeddings: {e}")
            self.knowledge_embeddings = None

    def generate_response(self, query):
        """Main response generation entry point"""
        return self.generate_intelligent_response(query)

    def generate_source_response(self, query, resource_id, resource_type):
        """Generate detailed response for clicked source"""
        self._ensure_knowledge_base_loaded()
        
        # Find the specific resource
        target_resource = None
        for item in self.knowledge_data:
            if str(item.get('actual_id')) == str(resource_id) and item.get('type') == resource_type:
                target_resource = item
                break
        
        if not target_resource:
            return {
                'response': "I couldn't find detailed information about that resource.",
                'confidence': 'low',
                'suggestions': ['Browse other resources', 'Ask a different question'],
                'matched_resources': []
            }
        
        response_parts = []
        response_parts.append(f"📋 **{target_resource['title']}**\n")
        response_parts.append(f"{target_resource['description']}\n")
        
        # Add type-specific information
        if target_resource.get('location'):
            response_parts.append(f"📍 **Location:** {target_resource['location']}")
        if target_resource.get('organizer'):
            response_parts.append(f"👥 **Organizer:** {target_resource['organizer']}")
        if target_resource.get('start_date'):
            response_parts.append(f"📅 **Start Date:** {target_resource['start_date']}")
        
        suggestions = [
            f"Find more {resource_type}s",
            f"Related to {target_resource['title'][:20]}...",
            "Ask another question",
            "Browse other topics"
        ]
        
        return {
            'response': '\n'.join(response_parts),
            'confidence': 'high',
            'suggestions': suggestions,
            'matched_resources': [target_resource],
            'ai_powered': True
        }

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
                        'issuing_body': policy.issuing_body,
                        'policy_number': policy.policy_number,
                        'effective_date': policy.effective_date.strftime('%Y-%m-%d') if policy.effective_date else None,
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
                        'publisher': publication.publisher,
                        'publication_year': publication.publication_year,
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
                        'technology_category': technology.technology_category,
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

            print(f"🎉 Successfully loaded {len(self.knowledge_data)} items into knowledge base")
       
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            print(f"❌ Error loading knowledge base: {e}")

# Global service instance
_chatbot_service = None

def get_chatbot_service():
    """Get or create the chatbot service instance (lazy loading)"""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = IntelligentChatbotService()
    return _chatbot_service

class ChatbotServiceProxy:
    """Proxy to delay service initialization until first use"""
    def __getattr__(self, name):
        service = get_chatbot_service()
        return getattr(service, name)

# This creates a proxy that behaves like the service instance
chatbot_service = ChatbotServiceProxy()