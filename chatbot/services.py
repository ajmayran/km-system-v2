import re
import json
import logging
import random
import numpy as np
from django.db import models
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import threading
from datetime import datetime, timedelta
from django.core.cache import cache

from appAdmin.models import (
    ResourceMetadata, KnowledgeResources, Commodity, 
    Event, InformationSystem, Map, Media, News, Policy,
    Project, Publication, Technology, TrainingSeminar, Webinar, Product,
    CMI  
)
from appCmi.models import (
    Forum, ForumComment, FAQ
)

# Import for local AI and FAISS
try:
    from sentence_transformers import SentenceTransformer
    from transformers import pipeline
    import torch
    import faiss
    TRANSFORMERS_AVAILABLE = True
    FAISS_AVAILABLE = True
    print("✅ Transformers and FAISS libraries loaded successfully!")
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    FAISS_AVAILABLE = False
    print(f"⚠️ Missing libraries: {e}")
    print("💡 Install with: pip install transformers sentence-transformers torch faiss-cpu")

# Global singleton instances - loaded once and reused
_ai_models = None
_nlp_model = None
_vectorizer = None
_stopwords = None
_basic_responses = None
_faiss_index = None
_faiss_embeddings = None
_model_loading_lock = threading.Lock()
_knowledge_base_cache = None
_knowledge_base_last_updated = None

def preprocess_text(text):
    """Preprocess text for better matching"""
    if not text:
        return ""
    
    # Enhanced text cleaning for better matching
    text = text.lower()
    # Remove extra punctuation but keep meaningful structure
    text = re.sub(r'[^\w\s\-]', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text

def load_stopwords():
    """Load custom stopwords from stopwords.txt file - cached globally"""
    global _stopwords
    if _stopwords is not None:
        return _stopwords
    
    _stopwords = set()
    
    try:
        with open('utils/stopwords/stopwords.txt', 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word and not word.startswith('//'):
                    _stopwords.add(word)
        print(f"✅ Loaded {len(_stopwords)} custom stopwords")
    except FileNotFoundError:
        print("⚠️ Custom stopwords file not found, using default English stopwords")
        _stopwords = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
    
    return _stopwords

def get_ai_models():
    """Get AI models - loaded once globally and reused across all requests"""
    global _ai_models, _model_loading_lock
    
    if _ai_models is not None:
        return _ai_models
    
    if not TRANSFORMERS_AVAILABLE:
        return None
    
    # Use thread lock to ensure models are loaded only once even with concurrent requests
    with _model_loading_lock:
        # Double-check pattern to prevent race conditions
        if _ai_models is not None:
            return _ai_models
        
        try:
            print("🧠 Loading AI models (one-time initialization)...")
            
            # Load models once and cache them
            _ai_models = {
                'sentence_transformer': SentenceTransformer('all-MiniLM-L6-v2'),
                'intent_classifier': pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=0 if torch.cuda.is_available() else -1
                )
            }
            
            print("✅ AI models loaded successfully and cached!")
            return _ai_models
            
        except Exception as e:
            print(f"❌ Error loading AI models: {e}")
            print("💡 Falling back to basic NLP processing")
            _ai_models = False  # Mark as failed to avoid retrying
            return None

def build_faiss_index(embeddings):
    """Build FAISS index for fast similarity search"""
    global _faiss_index, _faiss_embeddings
    
    if not FAISS_AVAILABLE or embeddings is None:
        return None
    
    try:
        # Convert to numpy array if needed
        if not isinstance(embeddings, np.ndarray):
            embeddings = np.array(embeddings)
        
        # Ensure embeddings are float32 for FAISS
        embeddings = embeddings.astype('float32')
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        
        # Use IndexFlatIP for inner product (cosine similarity after normalization)
        index = faiss.IndexFlatIP(dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to index
        index.add(embeddings)
        
        _faiss_index = index
        _faiss_embeddings = embeddings
        
        print(f"✅ Built FAISS index with {index.ntotal} vectors of dimension {dimension}")
        return index
        
    except Exception as e:
        print(f"❌ Error building FAISS index: {e}")
        return None

def get_faiss_index():
    """Get FAISS index"""
    return _faiss_index

def faiss_similarity_search(query_embedding, top_k=10):
    """Perform similarity search using FAISS"""
    if _faiss_index is None or query_embedding is None:
        return [], []
    
    try:
        # Ensure query embedding is the right shape and type
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        query_embedding = query_embedding.astype('float32')
        
        # Normalize query embedding for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = _faiss_index.search(query_embedding, top_k)
        
        return scores[0], indices[0]
        
    except Exception as e:
        print(f"❌ Error in FAISS search: {e}")
        return [], []

def get_knowledge_base_cache():
    """Get knowledge base from cache or load if needed with FAISS indexing"""
    global _knowledge_base_cache, _knowledge_base_last_updated
    
    # Cache for 1 hour to avoid constant database queries
    cache_duration = timedelta(hours=1)
    current_time = datetime.now()
    
    # Check if cache is still valid
    if (_knowledge_base_cache is not None and 
        _knowledge_base_last_updated is not None and 
        current_time - _knowledge_base_last_updated < cache_duration):
        return _knowledge_base_cache
    
    # Load fresh data if cache is expired or empty
    print("📚 Loading knowledge base into cache...")
    knowledge_data, document_texts = _load_knowledge_base_from_db()
    
    _knowledge_base_cache = {
        'knowledge_data': knowledge_data,
        'document_texts': document_texts,
        'knowledge_vectors': None,
        'knowledge_embeddings': None,
        'faiss_index': None
    }
    _knowledge_base_last_updated = current_time
    
    # Create TF-IDF vectors
    if document_texts:
        try:
            vectorizer = get_vectorizer()
            _knowledge_base_cache['knowledge_vectors'] = vectorizer.fit_transform(document_texts)
            print(f"✅ Created TF-IDF vectors for {len(document_texts)} documents")
        except Exception as e:
            print(f"⚠️ Could not create TF-IDF vectors: {e}")
    
    # Create AI embeddings and FAISS index if available
    ai_models = get_ai_models()
    if ai_models and document_texts:
        try:
            print("🧠 Creating AI embeddings...")
            embeddings = ai_models['sentence_transformer'].encode(document_texts, show_progress_bar=True)
            _knowledge_base_cache['knowledge_embeddings'] = embeddings
            
            # Build FAISS index
            faiss_index = build_faiss_index(embeddings)
            _knowledge_base_cache['faiss_index'] = faiss_index
            
            print(f"✅ Created embeddings and FAISS index for {len(document_texts)} documents")
        except Exception as e:
            print(f"❌ Error creating embeddings/FAISS index: {e}")
    
    print(f"🎉 Knowledge base cached with {len(knowledge_data)} items")
    return _knowledge_base_cache

def get_nlp_model():
    """Get spaCy model - loaded once globally and reused"""
    global _nlp_model
    
    if _nlp_model is not None:
        return _nlp_model if _nlp_model is not False else None
    
    try:
        _nlp_model = spacy.load("en_core_web_md")
        print("✅ Loaded spaCy model: en_core_web_md")
        return _nlp_model
    except OSError:
        try:
            _nlp_model = spacy.load("en_core_web_sm")
            print("✅ Loaded spaCy model: en_core_web_sm")
            return _nlp_model
        except OSError:
            print("⚠️ Warning: No spaCy model found. Using basic processing.")
            _nlp_model = False  # Mark as unavailable
            return None

def get_vectorizer():
    """Get TF-IDF vectorizer - initialized once and reused"""
    global _vectorizer
    
    if _vectorizer is not None:
        return _vectorizer
    
    stopwords = load_stopwords()
    _vectorizer = TfidfVectorizer(
        max_features=10000,  # Increased for better coverage
        stop_words=list(stopwords),
        ngram_range=(1, 3),  # Include trigrams for better context
        min_df=1,
        max_df=0.8,
        sublinear_tf=True  # Use log scaling
    )
    
    return _vectorizer

def load_basic_responses():
    """Load basic responses from JSON file - cached globally"""
    global _basic_responses
    if _basic_responses is not None:
        return _basic_responses
    
    try:
        with open('chatbot/data/basic-response.json', 'r', encoding='utf-8') as f:
            _basic_responses = json.load(f)
            print("✅ Loaded basic responses from file")
            return _basic_responses
    except FileNotFoundError:
        print("⚠️ Basic response file not found, using default responses")
        _basic_responses = {
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
        return _basic_responses

logger = logging.getLogger(__name__)

class IntelligentChatbotService:
    """Optimized chatbot service with FAISS for improved accuracy"""

    def __init__(self):
        # Use global cached resources instead of loading per instance
        self.knowledge_data, self.document_texts = _load_knowledge_base_from_db()
        self.stopwords = load_stopwords()
        self.basic_responses = load_basic_responses()
        
        # Reference to global models (loaded once)
        self.ai_models = get_ai_models()
        self.nlp = get_nlp_model()
        self.vectorizer = get_vectorizer()
        
        # Conversation cache for this session
        self._conversation_cache = {}
        
        print("✅ ChatbotService initialized with cached models and FAISS")

    def _get_knowledge_data(self):
        """Get knowledge data from cache"""
        cache = get_knowledge_base_cache()
        return (cache['knowledge_data'], cache['document_texts'], 
                cache['knowledge_vectors'], cache['knowledge_embeddings'])

    def _enhanced_semantic_search_with_faiss(self, query, intent_info, top_k=5):
        """Enhanced semantic search using FAISS for better accuracy"""
        knowledge_data, document_texts, knowledge_vectors, knowledge_embeddings = self._get_knowledge_data()
        
        if not self.ai_models or not FAISS_AVAILABLE:
            return self._nlp_text_matching(query, intent_info, top_k, knowledge_data)
        
        try:
            # Handle different intents with specialized processing
            if intent_info['intent'] == 'topic_content_request':
                return self._handle_topic_content_request_faiss(query, intent_info, top_k, knowledge_data)
            elif intent_info['intent'] == 'sample_request':
                return self._handle_sample_request(query, top_k, knowledge_data)
            
            # Enhanced query preprocessing
            enhanced_query = self._enhance_query_for_search(query, intent_info)
            
            # Get query embedding
            query_embedding = self.ai_models['sentence_transformer'].encode([enhanced_query])
            
            # Use FAISS for fast similarity search
            scores, indices = faiss_similarity_search(query_embedding, top_k * 3)  # Get more candidates
            
            if len(scores) == 0:
                return self._nlp_text_matching(query, intent_info, top_k, knowledge_data)
            
            results = []
            for score, idx in zip(scores, indices):
                if idx < len(knowledge_data) and score > 0.3:  # Higher threshold for quality
                    item = knowledge_data[idx]
                    
                    # Additional scoring with multiple factors
                    enhanced_score = self._calculate_enhanced_score(query, item, float(score), intent_info)
                    
                    results.append({
                        'resource': item,
                        'similarity_score': enhanced_score,
                        'faiss_score': float(score),
                        'confidence': self._get_confidence_level(enhanced_score)
                    })
            
            # Re-rank results based on enhanced scoring
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Apply diversity filter to avoid too similar results
            filtered_results = self._apply_diversity_filter(results, top_k)
            
            return filtered_results[:top_k]
            
        except Exception as e:
            print(f"Enhanced semantic search error: {e}")
            return self._nlp_text_matching(query, intent_info, top_k, knowledge_data)

    def _enhance_query_for_search(self, query, intent_info):
        """Enhance query with context for better search results"""
        enhanced_parts = [query]
        
        # Add main topic if available
        if intent_info.get('main_topic'):
            enhanced_parts.append(intent_info['main_topic'])
        
        # Add domain-specific terms based on content type
        content_type = intent_info.get('content_type', 'general')
        domain_terms = {
            'agriculture': ['farming', 'crop', 'agriculture', 'cultivation'],
            'aquaculture': ['fish', 'aquaculture', 'fisheries', 'aquatic'],
            'technology': ['innovation', 'technology', 'tools', 'equipment'],
            'training': ['education', 'training', 'learning', 'seminar'],
            'cmi': ['office', 'location', 'contact', 'services']
        }
        
        if content_type in domain_terms:
            enhanced_parts.extend(domain_terms[content_type][:2])  # Add top 2 relevant terms
        
        return ' '.join(enhanced_parts)

    def _calculate_enhanced_score(self, query, item, faiss_score, intent_info):
        """Calculate enhanced scoring with multiple factors"""
        base_score = faiss_score
        
        # Factor 1: Title relevance (higher weight)
        title_score = self._calculate_text_relevance(query, item['title']) * 0.4
        
        # Factor 2: Description relevance
        desc_score = self._calculate_text_relevance(query, item['description']) * 0.2
        
        # Factor 3: Type matching
        type_score = 0
        content_type = intent_info.get('content_type', 'general')
        if content_type != 'general' and item.get('type') == content_type:
            type_score = 0.1
        
        # Factor 4: Recent content boost
        recency_score = self._calculate_recency_score(item) * 0.1
        
        # Factor 5: Topic relevance
        topic_score = 0
        main_topic = intent_info.get('main_topic')
        if main_topic:
            topic_score = self._calculate_topic_relevance(main_topic, item) * 0.2
        
        # Combine all scores
        enhanced_score = base_score + title_score + desc_score + type_score + recency_score + topic_score
        
        return min(enhanced_score, 1.0)  # Cap at 1.0

    def _calculate_text_relevance(self, query, text):
        """Calculate text relevance using word overlap and semantic similarity"""
        if not text:
            return 0
        
        query_words = set(preprocess_text(query).split()) - self.stopwords
        text_words = set(preprocess_text(text).split()) - self.stopwords
        
        if not query_words:
            return 0
        
        # Word overlap score
        overlap = len(query_words.intersection(text_words))
        overlap_score = overlap / len(query_words)
        
        # Semantic similarity using spaCy if available
        semantic_score = 0
        if self.nlp:
            try:
                query_doc = self.nlp(query)
                text_doc = self.nlp(text)
                semantic_score = query_doc.similarity(text_doc)
            except:
                pass
        
        return (overlap_score * 0.7) + (semantic_score * 0.3)

    def _calculate_recency_score(self, item):
        """Give slight boost to more recent content"""
        try:
            # Look for date fields
            date_fields = ['created_at', 'date_posted', 'publication_date', 'start_date']
            for field in date_fields:
                if field in item and item[field]:
                    # Simple recency boost (can be enhanced)
                    return 0.1
            return 0
        except:
            return 0

    def _calculate_topic_relevance(self, topic, item):
        """Calculate how relevant the item is to the main topic"""
        if not topic:
            return 0
        
        topic_lower = topic.lower()
        title_lower = item['title'].lower()
        desc_lower = item['description'].lower()
        
        score = 0
        if topic_lower in title_lower:
            score += 0.5
        if topic_lower in desc_lower:
            score += 0.3
        
        # Check for topic words
        topic_words = topic_lower.split()
        for word in topic_words:
            if len(word) > 2 and word not in self.stopwords:
                if word in title_lower:
                    score += 0.2
                elif word in desc_lower:
                    score += 0.1
        
        return min(score, 1.0)

    def _apply_diversity_filter(self, results, target_count):
        """Apply diversity filter to avoid too similar results"""
        if len(results) <= target_count:
            return results
        
        filtered = [results[0]]  # Always include the best match
        
        for result in results[1:]:
            # Check if this result is too similar to already selected ones
            is_diverse = True
            for selected in filtered:
                similarity = self._calculate_result_similarity(result, selected)
                if similarity > 0.85:  # Too similar
                    is_diverse = False
                    break
            
            if is_diverse:
                filtered.append(result)
                if len(filtered) >= target_count:
                    break
        
        return filtered

    def _calculate_result_similarity(self, result1, result2):
        """Calculate similarity between two results"""
        title1 = preprocess_text(result1['resource']['title'])
        title2 = preprocess_text(result2['resource']['title'])
        
        words1 = set(title1.split()) - self.stopwords
        words2 = set(title2.split()) - self.stopwords
        
        if not words1 or not words2:
            return 0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0

    def _handle_topic_content_request_faiss(self, query, intent_info, top_k, knowledge_data):
        """Handle topic content requests with FAISS optimization"""
        main_topic = intent_info.get('main_topic')
        if not main_topic:
            return self._enhanced_semantic_search_with_faiss(query, intent_info, top_k)
        
        # Create topic-enhanced query
        topic_query = f"{query} {main_topic}"
        enhanced_intent = intent_info.copy()
        enhanced_intent['intent'] = 'general_query'  # Avoid recursion
        
        return self._enhanced_semantic_search_with_faiss(topic_query, enhanced_intent, top_k)

    def _classify_user_intent(self, query):
        """Classify user intent using cached AI model"""
        # First check for basic responses
        basic_intent = self._check_basic_response(query)
        if basic_intent:
            return basic_intent
        
        if not self.ai_models:
            return self._classify_intent_basic(query)
        
        try:
            # Enhanced intent classification with more specific categories
            candidate_labels = [
                "browsing or exploring specific content", 
                "request for examples or samples",
                "looking for specific information", 
                "asking for location or contact details",
                "requesting farming or agricultural advice",
                "seeking aquaculture information",
                "asking about training programs",
                "browsing or exploring content",
                "asking about CMI services",
                "content discovery for specific topic",
                "technical question about agriculture",
                "asking for research or publications"
            ]
            
            result = self.ai_models['intent_classifier'](query, candidate_labels)
            
            main_topic = self._extract_main_topic(query)
            content_type = self._extract_content_type(query)
            
            # Enhanced intent mapping
            intent_mapping = {
                "browsing or exploring specific content": "topic_content_request",
                "request for examples or samples": "sample_request",
                "looking for specific information": "specific_query",
                "asking for location or contact details": "location_query",
                "requesting farming or agricultural advice": "agriculture_query", 
                "seeking aquaculture information": "aquaculture_query",
                "asking about training programs": "program_query",
                "browsing or exploring content": "browse_request",
                "asking about CMI services": "cmi_query",
                "content discovery for specific topic": "topic_content_request",
                "technical question about agriculture": "technical_query",
                "asking for research or publications": "research_query"
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
        
        # Check all categories in the basic responses
        for category_name, category_data in self.basic_responses.items():
            for response_type, response_data in category_data.items():
                patterns = response_data.get('patterns', [])
                for pattern in patterns:
                    if pattern.lower() in query_lower:
                        responses = response_data.get('responses', [])
                        if responses:
                            return {
                                'intent': 'basic_response',
                                'category': response_type,
                                'category_name': category_name,
                                'response': random.choice(responses),
                                'confidence': 0.9,
                                'is_basic': True
                            }
        
        return None

    def _extract_main_topic(self, query):     
        """Extract the main topic/subject from the query using NLP and stopwords filtering"""
        if not query:
            return None
            
        # Enhanced topic extraction
        words = query.lower().split()
        
        action_words = {'browse', 'show', 'find', 'get', 'view', 'display', 'search', 'look', 'explore', 'give', 'tell', 'what', 'how', 'where', 'when', 'why'}
        meaningful_words = [word for word in words if word not in self.stopwords and word not in action_words and len(word) > 2]
            
        if not meaningful_words:
            return None
        
        if self.nlp:
            try:
                doc = self.nlp(query)
                # Look for named entities first (but skip BROWSE type entities)
                for ent in doc.ents:
                    if (ent.label_ in ['ORG', 'PRODUCT', 'GPE', 'PERSON'] and 
                        len(ent.text) > 2 and 
                        ent.text.lower() not in action_words):
                        return ent.text.upper()
                
                # Look for important nouns (excluding action words)
                nouns = [token.text for token in doc 
                        if (token.pos_ in ['NOUN', 'PROPN'] and 
                            len(token.text) > 2 and 
                            token.text.lower() not in action_words)]
                if nouns:
                    return nouns[0].upper()
            except Exception as e:
                print(f"spaCy processing error: {e}")
        
        domain_keywords = {
            'high': {
                'aquaculture': ['aquaculture', 'aquatic', 'fisheries', 'fish', 'tilapia', 'bangus', 'pond'],
                'agriculture': ['agriculture', 'farming', 'agricultural', 'farm', 'crop', 'crops'],
                'rice': ['rice', 'palay', 'grain'],
                'technology': ['technology', 'tech', 'innovation', 'equipment', 'tools'],
                'cmi': ['cmi', 'office', 'location', 'institution'],
                'research': ['research', 'study', 'publication', 'paper'],
                'training': ['training', 'seminar', 'workshop', 'course'],
                'forum': ['forum', 'discussion', 'community'],
                'news': ['news', 'update', 'announcement']
            },
            'medium': {
                'livestock': ['livestock', 'cattle', 'goat', 'poultry', 'chicken'],
                'coconut': ['coconut', 'coco'],
                'corn': ['corn', 'maize'],
                'environment': ['environment', 'natural', 'resources', 'sustainability'],
                'market': ['market', 'price', 'trading', 'economics']
            }
        }
        
        query_lower = query.lower()
        for priority in ['high', 'medium']:
            for main_topic, keywords in domain_keywords[priority].items():
                for keyword in keywords:
                    if keyword in query_lower:
                        # Check if this keyword appears with "resources" to form compound topic
                        if 'resources' in query_lower and keyword in query_lower:
                            return f"{main_topic.upper()}"
                        elif keyword in meaningful_words:
                            return main_topic.upper()
        
        # Fallback: return first meaningful word that's not an action word
        for word in meaningful_words:
            if word.lower() not in action_words:
                return word.upper()
        
        return meaningful_words[0].upper() if meaningful_words else None
    
    def _extract_content_type(self, query):
        """Extract what type of content is being requested"""
        query_lower = query.lower()
        
        content_types = {
            'faq': ['faq', 'question', 'answer', 'frequently asked'],
            'forum': ['forum', 'discussion', 'community', 'post'],
            'resource': ['resource', 'document', 'publication', 'paper'],
            'training': ['training', 'seminar', 'course', 'workshop'],
            'event': ['event', 'conference', 'meeting'],
            'cmi': ['cmi', 'office', 'location', 'contact'],
            'news': ['news', 'announcement', 'update'],
            'technology': ['technology', 'innovation', 'tool', 'equipment'],
            'research': ['research', 'study', 'analysis', 'findings']
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
        
        # Enhanced pattern matching
        patterns = {
            'sample_request': ['sample', 'example', 'show me', 'give me', 'demonstrate'],
            'location_query': ['where', 'location', 'address', 'contact', 'find office'],
            'agriculture_query': ['farm', 'crop', 'plant', 'agriculture', 'cultivation', 'harvest'],
            'aquaculture_query': ['fish', 'aquaculture', 'fisheries', 'aquatic', 'pond'],
            'technical_query': ['how to', 'technical', 'procedure', 'method', 'process'],
            'research_query': ['research', 'study', 'publication', 'paper', 'findings'],
            'faq_query': ['faq', 'question', 'answer', 'frequently asked'],
            'program_query': ['training', 'seminar', 'workshop', 'course', 'education'],
        }
        
        for intent, keywords in patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                confidence = 0.8 if len([k for k in keywords if k in query_lower]) > 1 else 0.7
                return {
                    'intent': intent, 
                    'confidence': confidence, 
                    'main_topic': main_topic, 
                    'content_type': content_type,
                    'is_basic': False
                }
        
        if main_topic:
            return {
                'intent': 'topic_content_request', 
                'confidence': 0.6, 
                'main_topic': main_topic, 
                'content_type': content_type,
                'is_basic': False
            }
        else:
            return {
                'intent': 'general_query', 
                'confidence': 0.5, 
                'main_topic': main_topic, 
                'content_type': content_type,
                'is_basic': False
            }

    # Update the main semantic search method to use FAISS
    def _semantic_search_with_nlp(self, query, intent_info, top_k=5):
        """Main semantic search method - now using FAISS for better accuracy"""
        return self._enhanced_semantic_search_with_faiss(query, intent_info, top_k)

    # Keep the existing methods for fallback and compatibility
    def _nlp_text_matching(self, query, intent_info, top_k=5, knowledge_data=None):
        """NLP-based text matching using cached data (fallback method)"""
        if knowledge_data is None:
            knowledge_data, _, _, _ = self._get_knowledge_data()
        
        results = []
        query_processed = preprocess_text(query)
        query_words = set(query_processed.split())
        
        # Remove stopwords from query
        query_words = query_words - self.stopwords
        
        if not query_words:
            return []
        
        for item in knowledge_data:
            score = self._calculate_nlp_score(query, item)
            
            if score > 0.1:  # Lower threshold for fallback
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
        
        # Calculate word overlap scores with better weighting
        title_overlap = len(query_words.intersection(title_words))
        desc_overlap = len(query_words.intersection(desc_words))
        
        # Enhanced scoring
        score += title_overlap * 4  # Increased title weight
        score += desc_overlap * 1.5  # Slightly increased description weight
        
        # Bonus for exact phrase matches
        if query_processed in title_processed:
            score += 5
        elif query_processed in desc_processed:
            score += 2
        
        # Use spaCy for semantic similarity if available
        if self.nlp:
            try:
                query_doc = self.nlp(query)
                item_doc = self.nlp(f"{item['title']} {item['description']}")
                semantic_score = query_doc.similarity(item_doc)
                score += semantic_score * 3  # Increased semantic weight
            except:
                pass
        
        # Normalize score with better scaling
        max_possible_score = len(query_words) * 4 + 8  # Adjusted for new weights
        return min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0

    # Keep all existing response generation methods unchanged
    def _handle_topic_content_request(self, query, intent_info, top_k, knowledge_data):
        """Handle requests for content about a specific topic"""
        main_topic = intent_info.get('main_topic')
        content_type = intent_info.get('content_type', 'general')
        
        if not main_topic:
            return self._nlp_text_matching(query, intent_info, top_k, knowledge_data)
        
        results = []
        topic_lower = main_topic.lower()
        
        # Filter by content type if specified
        filtered_data = knowledge_data
        if content_type != 'general':
            filtered_data = [item for item in knowledge_data if item.get('type') == content_type]
        
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

    def _handle_sample_request(self, query, top_k, knowledge_data):
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
        elif 'product' in query_lower:
            target_type = 'product'
        
        # Extract number if specified
        numbers = re.findall(r'\d+', query)
        requested_count = int(numbers[0]) if numbers else top_k
        
        # Filter by type if specified
        filtered_items = knowledge_data
        if target_type:
            filtered_items = [item for item in knowledge_data if item.get('type') == target_type]
        
        # Return the requested number of samples
        for i, item in enumerate(filtered_items[:requested_count]):
            results.append({
                'resource': item,
                'similarity_score': 1.0 - (i * 0.1),
                'confidence': 'high'
            })
        
        return results

    def find_similar_content(self, query, top_k=5):
        """Find similar content using FAISS-enhanced search (for views.py compatibility)"""
        # Basic intent info for compatibility
        intent_info = {
            'intent': 'general_query',
            'main_topic': self._extract_main_topic(query),
            'content_type': self._extract_content_type(query)
        }
        
        return self._enhanced_semantic_search_with_faiss(query, intent_info, top_k)

    def _generate_basic_response(self, intent_info):
        """Generate response from basic response patterns"""
        # If response is already in intent_info, use it directly
        if 'response' in intent_info:
            response = intent_info['response']
        else:
            # Fallback to category lookup
            category_name = intent_info.get('category_name', 'greetings')
            category = intent_info.get('category', 'hello')
            
            category_data = self.basic_responses.get(category_name, {})
            response_data = category_data.get(category, {})
            responses = response_data.get('responses', [])
            
            if responses:
                response = random.choice(responses)
            else:
                response = "Hello! How can I help you today?"
        
        # Generate appropriate suggestions based on category
        suggestions = self._generate_basic_suggestions(intent_info)
        
        return {
            'response': response,
            'confidence': 'high',
            'suggestions': suggestions,
            'matched_resources': [],
            'ai_powered': False,
            'basic_response': True
        }
    
    def _generate_basic_suggestions(self, intent_info):
        """Generate contextual suggestions for basic responses"""
        category_name = intent_info.get('category_name', 'greetings')
        category = intent_info.get('category', 'hello')
        
        # Context-aware suggestions based on the basic response category
        suggestion_map = {
            'greetings': {
                'hello': ['What can you help me with?', 'Show me farming resources', 'About KM Hub'],
                'goodbye': ['Ask another question', 'Browse available topics', 'Find more resources'],
                'thanks': ['Ask another question', 'Browse other topics', 'What else can you help with?']
            },
            'help_requests': {
                'general_help': ['Find farming techniques', 'Browse aquaculture resources'],
                'capabilities': ['What is RAISE-ABH?', 'What is RAISE Program?', 'Show me training programs']
            },
            'conversation': {
                'ask_another_question': ['What is sustainable farming?', 'How to start fish farming?', 'Find CMI offices'],
                'browse_topics': ['Rice farming techniques', 'Tilapia cultivation', 'CMI services'],
                'how_to_use': ['What can you help me with?', 'Find resources']
            },
            'status_checks': {
                'how_are_you': ['What can you help me with?', 'Show me farming resources', 'Find expert advice'],
                'are_you_real': ['What are your capabilities?','How can you help?']
            },
            'errors_clarifications': {
                'dont_understand': [ 'What can you help with?', 'Browse farming resources'],
                'repeat': ['Ask a specific question', 'Browse available topics', 'Find resources'],
                'no_results': ['Try broader terms', 'Show popular topics', 'Browse all resources']
            },
            'suggestions': {
                'popular_topics': ['What is RAISE-ABH?', 'Rice farming techniques', 'Find CMI offices'],
                'getting_started': ['Show me farming basics', 'Find beginner resources', 'CMI training programs']
            }
        }
        
        # Get suggestions for the specific category
        category_suggestions = suggestion_map.get(category_name, {})
        suggestions = category_suggestions.get(category, [])
        
        # Fallback suggestions if none found
        if not suggestions:
            suggestions = ['What can you help me with?', 'Show me farming resources', 'Browse available topics']
        
        return suggestions[:3]

    def generate_intelligent_response(self, query):
        """Main method for generating intelligent responses with FAISS"""
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
        
        # Handle different intents using FAISS-enhanced search
        if intent_info['intent'] == 'sample_request':
            matched_resources = self._enhanced_semantic_search_with_faiss(query, intent_info, top_k=5)
            return self._generate_sample_response(query, matched_resources, intent_info)
        elif intent_info['intent'] == 'topic_content_request':
            matched_resources = self._enhanced_semantic_search_with_faiss(query, intent_info, top_k=8)
            return self._generate_topic_content_response(query, matched_resources, intent_info)
        else:
            # Regular processing with FAISS
            matched_resources = self._enhanced_semantic_search_with_faiss(query, intent_info, top_k=5)
            print(f"🔍 Found {len(matched_resources)} matches using FAISS")
            
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
                'suggestions': [ 'Find recent forum posts', 'Browse knowledge resources'],
                'matched_resources': []
            }
        
        response_parts = []
        query_lower = query.lower()
        
        # Determine what type of sample was requested
        sample_type_map = {
            'faq': "❓ **Here are sample FAQs:**",
            'forum': "💬 **Here are sample forum discussions:**",
            'resource': "📄 **Here are sample resources:**",
            'product': "🛒 **Here are sample products:**",
            'publication': "📚 **Here are sample publications:**",
            'training': "🎓 **Here are sample training programs:**",
            'event': "📅 **Here are sample events:**",
            'project': "🌍 **Here are sample projects:**",
            'webinar': "💻 **Here are sample webinars:**",
            'commodity': "🌾 **Here are sample commodities:**"
        }

        # Find matching type or use default
        sample_header = "📚 **Here are some examples from our knowledge base:**"
        for key, header in sample_type_map.items():
            if key in query_lower:
                sample_header = header
                break

        response_parts.append(sample_header)
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
            'local_ai': True,
            'faiss_enhanced': True
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
        
        response_parts.append(f"💡 *Found {len(matched_resources)} results related to {main_topic} using enhanced AI search.*")
        
        return {
            'response': '\n'.join(response_parts),
            'confidence': 'high' if len(matched_resources) >= 3 else 'medium',
            'suggestions': [f"Tell me more about {main_topic.lower()}", "Find examples and samples", "Browse related topics"],
            'matched_resources': [match['resource'] for match in matched_resources],
            'ai_powered': True,
            'local_ai': True,
            'topic_focused': True,
            'faiss_enhanced': True
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
            'local_ai': True,
            'faiss_enhanced': True
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
            fallback = ['What can you help me with?', 'Find expert discussions']
            for sug in fallback:
                if sug not in suggestions:
                    suggestions.append(sug)
                    break
            break
        
        return suggestions[:3]

    def _generate_no_results_response(self, query):
        """Generate helpful response when no results found"""
        return {
            'response': f"I couldn't find specific information about '{query}' using our enhanced search. Try asking about agriculture, aquaculture, CMI services, or browse our available resources.\n\n🌾 Agricultural resources and techniques\n🐟 Aquaculture and fisheries information\n💬 Community forum discussions\n❓ Frequently asked questions\n🏢 CMI locations and services",
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

    def generate_response(self, query):
        """Main response generation entry point"""
        return self.generate_intelligent_response(query)

    def generate_source_response(self, query, resource_id, resource_type):
        """Generate detailed response for clicked source"""
        knowledge_data, _, _, _ = self._get_knowledge_data()
        
        # Find the specific resource
        target_resource = None
        for item in knowledge_data:
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
            'ai_powered': True,
            'faiss_enhanced': True
        }

# Keep all existing database loading functions unchanged
def _load_knowledge_base_from_db():
    """Load knowledge base from database - called only when cache expires"""
    knowledge_data = []
    document_texts = []
    
    try:
        print("Loading knowledge base from database...")
        
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
                
                knowledge_data.append(knowledge_item)
                document_texts.append(combined_text)
                
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
            
            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

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
            
            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        # 4. Load Events
        events = Event.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {events.count()} events")

        for event in events:
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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        # 5. Load Information Systems
        info_systems = InformationSystem.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {info_systems.count()} information systems")

        for info_system in info_systems:
            ombined_text = f"{info_system.metadata.title} {info_system.metadata.description} {info_system.system_owner}"

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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        # 6. Load Maps
        maps = Map.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {maps.count()} maps")

        for map_item in maps:
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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        # 7. Load Media
        media_items = Media.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {media_items.count()} media items")

        for media in media_items:
            ombined_text = f"{media.metadata.title} {media.metadata.description} {media.author} {media.media_type}"

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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        # 8. Load News
        news_items = News.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {news_items.count()} news items")

        for news in news_items:
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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        # 9. Load Policies
        policies = Policy.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {policies.count()} policies")

        for policy in policies:
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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        # 10. Load Projects
        projects = Project.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {projects.count()} projects")

        for project in projects:
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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        # 11. Load Publications
        publications = Publication.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {publications.count()} publications")

        for publication in publications:
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
                 
            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        # 12. Load Technologies
        technologies = Technology.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {technologies.count()} technologies")

        for technology in technologies:
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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)        
        
        # 13. Load Training/Seminars
        trainings = TrainingSeminar.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {trainings.count()} training/seminar items")

        for training in trainings:
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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text) 

        # 14. Load WEbinars
        webinars = Webinar.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {webinars.count()} webinars")

        for webinar in webinars:
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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text) 

        # 15. Load Products
        products = Product.objects.select_related('metadata').filter(metadata__is_approved=True)
        print(f"Found {products.count()} products")

        for product in products:
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
            
            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text) 

        # 16. Load Forum Discussions
        forums = Forum.objects.all()
        print(f"Found {forums.count()} forum discussions")

        for forum in forums:
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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text) 

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
        
            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text) 

        # 18. Load FAQ Data
        faqs = FAQ.objects.filter(is_active=True)
        print(f"Found {faqs.count()} FAQs")

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

            knowledge_data.append(knowledge_item)
            document_texts.append(combined_text)

        # Insert other models here...

        print(f"🎉 Successfully loaded {len(knowledge_data)} items into knowledge base")
        return knowledge_data, document_texts
   
    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}")
        print(f"❌ Error loading knowledge base: {e}")
        return [], []

# Global service instance with proper singleton pattern
_chatbot_service_instance = None
_service_lock = threading.Lock()

def get_chatbot_service():
    """Get or create the chatbot service instance with thread-safe singleton pattern"""
    global _chatbot_service_instance
    
    if _chatbot_service_instance is not None:
        return _chatbot_service_instance
    
    with _service_lock:
        # Double-check pattern to prevent race conditions
        if _chatbot_service_instance is not None:
            return _chatbot_service_instance
        
        print("🚀 Initializing FAISS-enhanced ChatbotService singleton...")
        _chatbot_service_instance = IntelligentChatbotService()
        print("✅ FAISS-enhanced ChatbotService singleton ready!")
        return _chatbot_service_instance

# This creates the singleton instance
chatbot_service = get_chatbot_service()