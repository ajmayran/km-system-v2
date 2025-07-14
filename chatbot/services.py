import re
import json
import logging
import random
import numpy as np
import spacy
import threading
import os
from fuzzywuzzy import fuzz
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .spell_corrector import (
    correct_spelling_dynamic, 
    get_spell_corrector, 
    advanced_fuzzy_match, 
    fuzzy_match_keywords,
    get_spell_correction_stats
)
# Import for local AI and FAISS
try:
    from sentence_transformers import SentenceTransformer
    from transformers import pipeline
    import torch
    import faiss
    TRANSFORMERS_AVAILABLE = True
    FAISS_AVAILABLE = True
    print("✅ AI libraries loaded successfully!")
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    FAISS_AVAILABLE = False
    print(f"⚠️ Missing AI libraries: {e}")
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

# JSON-based loading for better performance
_json_knowledge_cache = None
_json_last_loaded = None

logger = logging.getLogger(__name__)

def preprocess_text(text):
    """Enhanced preprocessing"""
    if not text:
        return ""
    
    text = text.lower()
    text = re.sub(r'[^\w\s\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text.strip())

    stopwords = load_stopwords()
    words = text.split()
    filtered_words = [word for word in words if word not in stopwords and len(word) > 1]
    
    return ' '.join(filtered_words)

def load_stopwords():
    """Load custom stopwords from stopwords.txt file - cached globally"""
    global _stopwords
    if _stopwords is not None:
        return _stopwords
    
    _stopwords = set()
    
    try:
        stopwords_path = os.path.join(settings.BASE_DIR, 'utils', 'stopwords', 'stopwords.txt')
        with open(stopwords_path, 'r', encoding='utf-8') as f:
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
    
    with _model_loading_lock:
        if _ai_models is not None:
            return _ai_models
        
        try:
            print("🧠 Loading AI models (one-time initialization)...")
            
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
            _ai_models = False
            return None

def warmup_ai_models():
    """Warm up AI models during application startup"""
    print("🔥 Warming up AI models...")
    try:
        # Trigger AI model loading
        get_ai_models()
        # Trigger embedding creation
        get_or_create_ai_cache()
        print("✅ AI models warmed up successfully!")
    except Exception as e:
        print(f"⚠️ AI warmup failed: {e}")

def background_ai_warmup():
    """Load AI models in background"""
    def warmup_thread():
        try:
            warmup_ai_models()
        except Exception as e:
            print(f"❌ Background AI warmup failed: {e}")
    
    threading.Thread(target=warmup_thread, daemon=True).start()

def build_faiss_index(embeddings):
    """Build FAISS index for fast similarity search"""
    global _faiss_index, _faiss_embeddings
    
    if not FAISS_AVAILABLE or embeddings is None:
        return None
    
    try:
        if not isinstance(embeddings, np.ndarray):
            embeddings = np.array(embeddings)
        
        embeddings = embeddings.astype('float32')
        dimension = embeddings.shape[1]
        
        # Use IndexFlatIP for inner product (cosine similarity after normalization)
        index = faiss.IndexFlatIP(dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        
        _faiss_index = index
        _faiss_embeddings = embeddings
        
        print(f"✅ Built FAISS index with {index.ntotal} vectors of dimension {dimension}")
        return index
        
    except Exception as e:
        print(f"❌ Error building FAISS index: {e}")
        return None

def faiss_similarity_search(query_embedding, top_k=10):
    """Perform similarity search using FAISS"""
    if _faiss_index is None or query_embedding is None:
        return [], []
    
    try:
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        query_embedding = query_embedding.astype('float32')
        faiss.normalize_L2(query_embedding)
        
        scores, indices = _faiss_index.search(query_embedding, top_k)
        return scores[0], indices[0]
        
    except Exception as e:
        print(f"❌ Error in FAISS search: {e}")
        return [], []

def get_knowledge_base_json_path():
    """Get path to the knowledge base JSON file"""
    return os.path.join(settings.BASE_DIR, 'chatbot', 'data', 'knowledge_base.json')

def load_knowledge_base_from_json():
    """Load knowledge base from JSON file - ULTRA FAST runtime loading"""
    global _json_knowledge_cache, _json_last_loaded
    
    json_path = get_knowledge_base_json_path()
    
    if not os.path.exists(json_path):
        print("⚠️ Knowledge base JSON not found!")
        print("📝 Run: python manage.py build_knowledge_base")
        return [], []
    
    try:
        file_modified_time = os.path.getmtime(json_path)
        
        # Use cache if file hasn't changed
        if (_json_knowledge_cache is not None and 
            _json_last_loaded is not None and 
            _json_last_loaded >= file_modified_time):
            # print("⚡ Using cached JSON knowledge base")  # Remove logging for speed
            return _json_knowledge_cache['knowledge_data'], _json_knowledge_cache['document_texts']
        
        print("📚 Loading knowledge base from JSON...")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        _json_knowledge_cache = {
            'knowledge_data': json_data['knowledge_data'],
            'document_texts': json_data['document_texts'],
            'metadata': json_data.get('metadata', {})
        }
        _json_last_loaded = file_modified_time
        
        total_items = len(_json_knowledge_cache['knowledge_data'])
        print(f"✅ Loaded {total_items} items from JSON")
        
        return _json_knowledge_cache['knowledge_data'], _json_knowledge_cache['document_texts']
        
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return [], []

def get_knowledge_base_cache():
    """Get knowledge base cache - OPTIMIZED for speed"""
    global _knowledge_base_cache, _knowledge_base_last_updated
    
    # Reduced cache duration for testing - increase to 6 hours in production
    cache_duration = timedelta(hours=6)
    current_time = datetime.now()
    
    if (_knowledge_base_cache is not None and 
        _knowledge_base_last_updated is not None and
        current_time - _knowledge_base_last_updated < cache_duration):
        # print("🚀 Using cached knowledge base")  # Remove logging for speed
        return _knowledge_base_cache
    
    print("📚 Loading knowledge base into cache...")
    
    # Load from JSON instead of database - MUCH FASTER!
    knowledge_data, document_texts = load_knowledge_base_from_json()
    
    if not knowledge_data:
        print("❌ No knowledge data found - please build JSON first")
        return {
            'knowledge_data': [],
            'document_texts': [],
            'knowledge_vectors': None,
            'knowledge_embeddings': None,
            'faiss_index': None
        }
    
    _knowledge_base_cache = {
        'knowledge_data': knowledge_data,
        'document_texts': document_texts,
        'knowledge_vectors': None,
        'knowledge_embeddings': None,
        'faiss_index': None
    }
    _knowledge_base_last_updated = current_time
    
    # Create TF-IDF vectors for fallback - ONLY IF NEEDED
    if document_texts:
        try:
            vectorizer = get_vectorizer()
            _knowledge_base_cache['knowledge_vectors'] = vectorizer.fit_transform(document_texts)
            print(f"✅ Created TF-IDF vectors for {len(document_texts)} documents")
        except Exception as e:
            print(f"⚠️ Could not create TF-IDF vectors: {e}")
    
    print(f"🎉 Knowledge base cached with {len(knowledge_data)} items")
    return _knowledge_base_cache

def get_or_create_ai_cache():
    """Lazily create AI embeddings and FAISS index only when needed"""
    global _knowledge_base_cache
    
    if not _knowledge_base_cache:
        get_knowledge_base_cache()
    
    # Check if AI cache already exists
    if (_knowledge_base_cache.get('knowledge_embeddings') is not None and 
        _knowledge_base_cache.get('faiss_index') is not None):
        return _knowledge_base_cache
    
    document_texts = _knowledge_base_cache.get('document_texts', [])
    ai_models = get_ai_models()
    
    if ai_models and document_texts:
        try:
            print("🧠 Creating AI embeddings (lazy loading)...")
            embeddings = ai_models['sentence_transformer'].encode(document_texts, show_progress_bar=True)
            _knowledge_base_cache['knowledge_embeddings'] = embeddings
            
            # Build FAISS index
            faiss_index = build_faiss_index(embeddings)
            _knowledge_base_cache['faiss_index'] = faiss_index
            
            print(f"✅ Created embeddings and FAISS index for {len(document_texts)} documents")
        except Exception as e:
            print(f"❌ Error creating embeddings/FAISS index: {e}")
    
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
            _nlp_model = False
            return None

def get_vectorizer():
    """Get TF-IDF vectorizer - initialized once and reused"""
    global _vectorizer
    
    if _vectorizer is not None:
        return _vectorizer
    
    stopwords = load_stopwords()
    _vectorizer = TfidfVectorizer(
        max_features=10000,
        stop_words=list(stopwords),
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.8,
        sublinear_tf=True
    )
    
    return _vectorizer

def load_basic_responses():
    """Load basic responses from JSON file - cached globally"""
    global _basic_responses
    if _basic_responses is not None:
        return _basic_responses
    
    try:
        basic_responses_path = os.path.join(settings.BASE_DIR, 'chatbot', 'data', 'basic-response.json')
        with open(basic_responses_path, 'r', encoding='utf-8') as f:
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

class IntelligentChatbotService:
    """Optimized chatbot service with lazy-loaded FAISS for ultra-fast startup"""

    def __init__(self):
        self.stopwords = load_stopwords()
        self.basic_responses = load_basic_responses()
        
        # Get models but don't force AI model loading
        self.ai_models = None  # Load lazily
        self.nlp = None        # Load lazily
        self.vectorizer = get_vectorizer()
        
        # Conversation cache for this session
        self._conversation_cache = {}
        
        print("✅ ChatbotService initialized with lazy loading")

    def _get_ai_models(self):
        """Lazy load AI models only when needed"""
        if self.ai_models is None:
            self.ai_models = get_ai_models()
        return self.ai_models

    def _get_nlp_model(self):
        """Lazy load NLP model only when needed"""
        if self.nlp is None:
            self.nlp = get_nlp_model()
        return self.nlp

    def _get_knowledge_data(self):
        """Get knowledge data from cache - FAST"""
        cache = get_knowledge_base_cache()
        return (cache['knowledge_data'], cache['document_texts'], 
                cache['knowledge_vectors'], cache.get('knowledge_embeddings'))

    def _enhanced_semantic_search_with_faiss(self, query, intent_info, top_k=5):
        """Enhanced semantic search with dynamic topic handling"""
        knowledge_data, document_texts, knowledge_vectors, knowledge_embeddings = self._get_knowledge_data()
        
        if not knowledge_data:
            return []
        
        corrected_query = self.process_query_with_correction(query)
        
        specific_results = self._find_specific_matches(corrected_query, knowledge_data)
        if specific_results:
            print(f"✅ Found {len(specific_results)} specific matches")
            return specific_results[:top_k]
        
        ai_models = self._get_ai_models()
        
        if not ai_models or not FAISS_AVAILABLE:
            return self._cosine_similarity_fallback(corrected_query, intent_info, top_k, knowledge_data, document_texts)
        
        try:
            enhanced_query = self._enhance_query_for_search(corrected_query, intent_info)
            
            if knowledge_embeddings is None:
                ai_cache = get_or_create_ai_cache()
                knowledge_embeddings = ai_cache.get('knowledge_embeddings')
            
            if knowledge_embeddings is None:
                return self._cosine_similarity_fallback(corrected_query, intent_info, top_k, knowledge_data, document_texts)
            
            query_embedding = ai_models['sentence_transformer'].encode([enhanced_query])
            scores, indices = faiss_similarity_search(query_embedding, top_k * 3)
            
            if len(scores) == 0:
                return self._cosine_similarity_fallback(corrected_query, intent_info, top_k, knowledge_data, document_texts)
            
            results = []
            
            for score, idx in zip(scores, indices):
                if idx < len(knowledge_data) and score > 0.2:
                    item = knowledge_data[idx]
                    
                    enhanced_score = self._calculate_enhanced_score(corrected_query, item, float(score), intent_info)
                    results.append({
                        'resource': item,
                        'similarity_score': enhanced_score,
                        'faiss_score': float(score),
                        'confidence': self._get_confidence_level(enhanced_score)
                    })
            
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            filtered_results = self._apply_diversity_filter(results, top_k)
            
            print(f"🔍 Found {len(results)} AI-powered results for query: '{query}'")
            return filtered_results[:top_k]
            
        except Exception as e:
            print(f"Enhanced semantic search error: {e}")
            return self._cosine_similarity_fallback(corrected_query, intent_info, top_k, knowledge_data, document_texts)

    def _find_specific_matches(self, query, knowledge_data):
        """Find specific/exact matches in knowledge base"""
        query_lower = query.lower()
        specific_matches = []
        
        for idx, item in enumerate(knowledge_data):
            score = 0
            

            title_lower = item['title'].lower()
            if query_lower in title_lower or title_lower in query_lower:
                score += 10
            
            query_words = set(query_lower.split())
            title_words = set(title_lower.split())
            word_overlap = query_words.intersection(title_words)
            if word_overlap:
                score += len(word_overlap) * 2

            desc_lower = item['description'].lower()
            if any(word in desc_lower for word in query_words if len(word) > 3):
                score += 1
            
            if score >= 5:
                specific_matches.append({
                    'resource': item,
                    'similarity_score': min(score / 15.0, 1.0),
                    'confidence': 'high',
                    'match_type': 'specific'
                })
        
        specific_matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        return specific_matches

    def _cosine_similarity_fallback(self, query, intent_info, top_k, knowledge_data, document_texts):
        """FAST fallback method using cosine similarity"""
        if not document_texts:
            return []
        
        try:
            if not hasattr(self, '_spell_corrected'):
                query = self.process_query_with_correction(query)

            vectorizer = get_vectorizer()

            if not hasattr(vectorizer, 'vocabulary_'):
                vectorizer.fit(document_texts)
            
            query_vector = vectorizer.transform([query])
            document_vectors = vectorizer.transform(document_texts)
            
            similarities = cosine_similarity(query_vector, document_vectors).flatten()
            
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1: 
                    results.append({
                        'resource': knowledge_data[idx],
                        'similarity_score': float(similarities[idx]),
                        'cosine_score': float(similarities[idx]),
                        'confidence': self._get_confidence_level(float(similarities[idx]))
                    })
            
            return results
            
        except Exception as e:
            print(f"❌ Cosine similarity fallback error: {e}")
            return []

    def _enhance_query_for_search(self, query, intent_info):
        """Enhance query with context for better search results using advanced fuzzy matching"""
        enhanced_parts = [query]
        
        if intent_info.get('main_topic'):
            enhanced_parts.append(intent_info['main_topic'])
        
        content_type = intent_info.get('content_type', 'general')
        domain_terms = {
            'agriculture': ['farming', 'crop', 'agriculture', 'cultivation'],
            'aquaculture': ['fish', 'aquaculture', 'fisheries', 'aquatic'],
            'technology': ['innovation', 'technology', 'tools', 'equipment'],
            'training': ['education', 'training', 'learning', 'seminar'],
            'cmi': ['office', 'location', 'contact', 'services']
        }
        
        if content_type in domain_terms:
            all_terms = []
            for category, terms in domain_terms.items():
                all_terms.extend(terms)
            
            # Find fuzzy matches for query terms
            fuzzy_matches = advanced_fuzzy_match(query, all_terms, threshold=75)
            related_terms = [match[0] for match in fuzzy_matches[:2]]  
            enhanced_parts.extend(related_terms)
        
        return ' '.join(enhanced_parts)

    def _calculate_enhanced_score(self, query, item, faiss_score, intent_info):
        """FAST enhanced scoring with multiple factors"""
        base_score = faiss_score
        

        title_score = self._fast_text_relevance(query, item['title']) * 0.4
        desc_score = self._fast_text_relevance(query, item['description']) * 0.2
        
        type_score = 0
        content_type = intent_info.get('content_type', 'general')
        if content_type != 'general' and item.get('type') == content_type:
            type_score = 0.1
        
        topic_score = 0
        main_topic = intent_info.get('main_topic')
        if main_topic and main_topic.lower() in item['title'].lower():
            topic_score = 0.2
        
        enhanced_score = base_score + title_score + desc_score + type_score + topic_score
        return min(enhanced_score, 1.0)

    def _fast_text_relevance(self, query, text):
        """FAST text relevance using word overlap only"""
        if not text:
            return 0
        
        query_words = set(preprocess_text(query).split()) - self.stopwords
        text_words = set(preprocess_text(text).split()) - self.stopwords
        
        if not query_words:
            return 0
        
        overlap = len(query_words.intersection(text_words))
        return overlap / len(query_words)

    def _apply_diversity_filter(self, results, target_count):
        """FAST diversity filter"""
        if len(results) <= target_count:
            return results
        
        filtered = [results[0]]
        
        for result in results[1:]:
            is_diverse = True
            for selected in filtered:
                # FAST similarity check - just title words
                title1_words = set(preprocess_text(result['resource']['title']).split())
                title2_words = set(preprocess_text(selected['resource']['title']).split())
                
                if title1_words and title2_words:
                    intersection = len(title1_words.intersection(title2_words))
                    union = len(title1_words.union(title2_words))
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity > 0.7:  # More lenient threshold for speed
                        is_diverse = False
                        break
            
            if is_diverse:
                filtered.append(result)
                if len(filtered) >= target_count:
                    break
        
        return filtered

    def _handle_topic_content_request_faiss(self, query, intent_info, top_k, knowledge_data):
        """Handle topic content requests with FAISS optimization"""
        main_topic = intent_info.get('main_topic')
        if not main_topic:
            return self._enhanced_semantic_search_with_faiss(query, intent_info, top_k)
        
        topic_query = f"{query} {main_topic}"
        enhanced_intent = intent_info.copy()
        enhanced_intent['intent'] = 'general_query'
        
        return self._enhanced_semantic_search_with_faiss(topic_query, enhanced_intent, top_k)

    def _handle_sample_request(self, query, top_k, knowledge_data):
        """Handle requests for samples/examples"""
        results = []
        query_lower = query.lower()
        
        target_type = None
        if 'faq' in query_lower:
            target_type = 'faq'
        elif 'forum' in query_lower:
            target_type = 'forum'
        elif 'resource' in query_lower:
            target_type = 'resource'
        elif 'product' in query_lower:
            target_type = 'product'
        
        numbers = re.findall(r'\d+', query)
        requested_count = int(numbers[0]) if numbers else top_k
        
        filtered_items = knowledge_data
        if target_type:
            filtered_items = [item for item in knowledge_data if item.get('type') == target_type]
        
        for i, item in enumerate(filtered_items[:requested_count]):
            results.append({
                'resource': item,
                'similarity_score': 1.0 - (i * 0.1),
                'confidence': 'high'
            })
        
        return results

    def _classify_user_intent(self, query):
        """FAST intent classification with caching"""
        basic_intent = self._check_basic_response(query)
        if basic_intent:
            basic_intent['skip_ai'] = True  # Flag to skip AI processing
            return basic_intent
        
        # Use basic classification by default for speed
        return self._classify_intent_basic(query)

    def _check_basic_response(self, query):
        """Check if query matches basic response patterns"""
        query_lower = query.lower()
        
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
        """Dynamic main topic extraction from knowledge base data"""
        if not query:
            return None
        
        cache = get_knowledge_base_cache()
        knowledge_data = cache['knowledge_data']
        
        if not knowledge_data:
            return None

        query_lower = query.lower()
        corrected_query = correct_spelling_dynamic(query_lower)
        
        processed_query = preprocess_text(corrected_query)
        print(f"🔍 Processed query after stopword removal: '{processed_query}'")
        
        # Look for compound terms first
        processed_words = processed_query.split()
        if len(processed_words) >= 2:
            for i in range(len(processed_words)):
                for j in range(i+1, len(processed_words)+1):
                    phrase = ' '.join(processed_words[i:j])
                    
                    for item in knowledge_data:
                        title_lower = item['title'].lower()
                        desc_lower = item['description'].lower()
                        
                        if phrase in title_lower or phrase in desc_lower:
                            print(f"🎯 Found compound topic: '{phrase}' in '{item['title']}'")
                            return phrase.upper()
        
        # Single word matching from processed words
        for word in processed_words:
            # Direct match in knowledge base
            for item in knowledge_data:
                title_lower = item['title'].lower()
                desc_lower = item['description'].lower()
                
                if word in title_lower or word in desc_lower:
                    print(f"🎯 Found single topic: '{word}' in '{item['title']}'")
                    return word.upper()
        
        return None

    def _extract_topics_from_knowledge_base(self, knowledge_data):
        """Extract topics dynamically from your knowledge base"""
        topics = {}
        
        for item in knowledge_data:
            item_type = item.get('type', 'general')
            title_words = [word.lower() for word in item['title'].split() if len(word) > 3]
            desc_words = [word.lower() for word in item['description'].split() if len(word) > 3]
            
            if item_type not in topics:
                topics[item_type] = set()

            for word in title_words + desc_words:
                if word not in self.stopwords and len(word) > 3:
                    topics[item_type].add(word)
    
        for topic in topics:
            topics[topic] = list(topics[topic])[:20] 
        
        print(f"🔄 Extracted {len(topics)} dynamic topics from knowledge base")
        return topics

    def _extract_content_type(self, query):
        """Dynamic content type extraction - no hardcoded priorities"""
        original_query_lower = query.lower()  
        
        content_types = {
            'faq': ['faq', 'faqs', 'question', 'answer', 'frequently', 'asked', 'questions'],  
            'forum': ['forum', 'discussion', 'community', 'post'],
            'resource': ['resource', 'document', 'publication', 'paper'],
            'training': ['training', 'seminar', 'course', 'workshop'],
            'event': ['event', 'conference', 'meeting'],
            'cmi': ['cmi', 'office', 'location', 'contact'],
            'news': ['news', 'announcement', 'update'],
            'technology': ['technology', 'innovation', 'tool', 'equipment'],
            'research': ['research', 'study', 'analysis', 'findings']
        }
        
        # Check ALL content types equally for exact matches
        for content_type, keywords in content_types.items():
            if any(keyword in original_query_lower for keyword in keywords):
                print(f"🎯 Content type detected: '{content_type}' from query: '{original_query_lower}'")
                return content_type
        
        # Fallback to fuzzy matching for ALL types equally
        all_keywords = []
        keyword_to_type = {}
        for content_type, keywords in content_types.items():
            for keyword in keywords:
                all_keywords.append(keyword)
                keyword_to_type[keyword] = content_type
        
        fuzzy_matches = advanced_fuzzy_match(original_query_lower, all_keywords, threshold=80)
        if fuzzy_matches:
            best_match = fuzzy_matches[0][0]  
            matched_type = keyword_to_type[best_match]
            print(f"🎯 Fuzzy matched content type: '{best_match}' → '{matched_type}'")
            return matched_type
        
        return 'general'

    def _classify_intent_basic(self, query):
        """FAST basic intent classification using patterns"""
        query_lower = query.lower()
        
        main_topic = self._extract_main_topic(query)
        content_type = self._extract_content_type(query)
        
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

    def process_query_with_correction(self, query):
        """Process query with spell correction applied"""
        if not query:
            return query
        
        # Apply spell correction
        corrected_query = correct_spelling_dynamic(query)
        
        # Log corrections for debugging
        if corrected_query != query:
            print(f"🔧 Query corrected: '{query}' → '{corrected_query}'")
        
        return corrected_query

    def find_similar_content(self, query, top_k=5):
        """Find similar content using FAISS-enhanced search (for views.py compatibility)"""
        intent_info = {
            'intent': 'general_query',
            'main_topic': self._extract_main_topic(query),
            'content_type': self._extract_content_type(query)
        }
        
        return self._enhanced_semantic_search_with_faiss(query, intent_info, top_k)

    def _generate_basic_response(self, intent_info):
        """Generate response from basic response patterns"""
        if 'response' in intent_info:
            response = intent_info['response']
        else:
            category_name = intent_info.get('category_name', 'greetings')
            category = intent_info.get('category', 'hello')
            
            category_data = self.basic_responses.get(category_name, {})
            response_data = category_data.get(category, {})
            responses = response_data.get('responses', [])
            
            if responses:
                response = random.choice(responses)
            else:
                response = "Hello! How can I help you today?"
        
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
        
        suggestion_map = {
            'greetings': {
                'hello': ['What can you help me with?', 'Show me farming resources', 'About KM Hub'],
                'goodbye': ['Ask another question', 'Browse available topics', 'Find more resources'],
                'thanks': ['Ask another question', 'Browse other topics', 'What else can you help with?']
            }
        }
        
        category_suggestions = suggestion_map.get(category_name, {})
        suggestions = category_suggestions.get(category, [])
        
        if not suggestions:
            suggestions = ['What can you help me with?', 'Show me farming resources', 'Browse available topics']
        
        return suggestions[:3]


    def _calculate_semantic_similarity(self, query, text):
        """Calculate semantic similarity between query and text with fuzzy matching"""
        if not query or not text:
            return 0
        
        query_words = set(preprocess_text(query).split()) - self.stopwords
        text_words = set(preprocess_text(text).split()) - self.stopwords
        
        if not query_words or not text_words:
            return 0
        
        # Calculate Jaccard similarity
        intersection = len(query_words.intersection(text_words))
        union = len(query_words.union(text_words))
        
        jaccard_sim = intersection / union if union > 0 else 0
        
        # Add fuzzy matching for partial word matches
        fuzzy_matches = 0
        for q_word in query_words:
            for t_word in text_words:
                if fuzz.ratio(q_word, t_word) >= 80:
                    fuzzy_matches += 1
                    break
        
        fuzzy_sim = fuzzy_matches / len(query_words) if query_words else 0
        
        # Combine both similarities
        return (jaccard_sim + fuzzy_sim) / 2
    
    def _handle_about_query(self, query, intent_info):
        """Handle ANY about queries with focused responses"""
        query_lower = query.lower()
        
        # Apply spell correction first
        corrected_query = correct_spelling_dynamic(query_lower)
        print(f"🔧 About query correction: '{query_lower}' → '{corrected_query}'")
        
        # Get about content from knowledge base
        cache = get_knowledge_base_cache()
        knowledge_data = cache['knowledge_data']
        
        about_items = [item for item in knowledge_data if item['type'] == 'about']
        
        if not about_items:
            return []
        
        # Enhanced keyword matching with fuzzy search
        about_keywords = [
            'mission', 'vision', 'goal', 'objective', 'feature', 'purpose',
            'history', 'background', 'overview', 'introduction', 'description',
            'what is', 'who are', 'how does', 'aanr', 'knowledge hub', 'km hub',
            'agriculture', 'aquaculture', 'fisheries', 'research', 'innovation'
        ]
        
        # Find fuzzy matches for keywords
        fuzzy_matched_keywords = fuzzy_match_keywords(corrected_query, about_keywords, threshold=75)
        print(f"🎯 Fuzzy matched keywords: {fuzzy_matched_keywords}")
        
        best_matches = []
        seen_titles = set()
        
        for item in about_items:
            if item['title'] in seen_titles:
                continue
            
            score = 0
            
            # Check direct keyword matches in corrected query
            for keyword in about_keywords:
                if keyword in corrected_query:
                    if keyword in item['title'].lower():
                        score += 2
                    
                    content_sample = item.get('content', item.get('description', ''))
                    if keyword in content_sample.lower():
                        score += 1
                    
                    if 'section' in item and keyword in item['section'].lower():
                        score += 3
            
            # Check fuzzy keyword matches
            for keyword, match_ratio in fuzzy_matched_keywords:
                if match_ratio >= 75:
                    # Apply fuzzy matching to content
                    content_sample = item.get('content', item.get('description', ''))
                    
                    if fuzz.partial_ratio(keyword, item['title'].lower()) >= 75:
                        score += 1.5
                    
                    if fuzz.partial_ratio(keyword, content_sample.lower()) >= 75:
                        score += 1
                    
                    if 'section' in item and fuzz.partial_ratio(keyword, item['section'].lower()) >= 75:
                        score += 2
            
            # Enhanced semantic similarity using word overlap
            item_text = f"{item['title']} {item.get('content', item.get('description', ''))}"
            similarity_score = self._calculate_semantic_similarity(corrected_query, item_text)
            score += similarity_score
            
            # General about queries with fuzzy matching
            about_triggers = ['about', 'what is', 'tell me about', 'describe', 'explain']
            for trigger in about_triggers:
                if fuzz.partial_ratio(trigger, corrected_query) >= 80:
                    score += 1
                    break
            
            if score > 0:
                full_content = item.get('content', item.get('description', ''))
                clean_content = re.sub(r'<[^>]+>', '', full_content)
                clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                
                cleaned_item = {
                    **item,
                    'description': clean_content
                }
                
                best_matches.append({
                    'resource': cleaned_item,
                    'similarity_score': min(score / 6.0, 1.0),
                    'confidence': 'high' if score >= 4 else 'medium' if score >= 2 else 'low'
                })
                
                seen_titles.add(item['title'])
        
        best_matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return best_matches[:1] if best_matches else [{
            'resource': {
                **about_items[0],
                'description': re.sub(r'<[^>]+>', '', about_items[0].get('content', about_items[0].get('description', '')))
            },
            'similarity_score': 0.5,
            'confidence': 'medium'
        }]

    def generate_intelligent_response(self, query):
        """Main method for generating intelligent responses"""
        query = query.strip()
        original_query_lower = query.lower()
        
        corrected_query = self.process_query_with_correction(query)
        
        basic_intent = self._check_basic_response(corrected_query)
        if basic_intent:
            return self._generate_basic_response(basic_intent)

        about_triggers = [
            'about', 'tell me about', 'mission', 'vision', 
            'goal', 'objective', 'purpose', 'aanr', 'knowledge hub', 
            'km hub', 'who are', 'how does', 'background', 'overview'
        ]
        
        hub_specific_terms = ['aanr', 'knowledge hub', 'km hub', 'knowledge management', 'system']
        
        about_query_detected = False
        corrected_lower = corrected_query.lower()
        
        for trigger in about_triggers:
            if fuzz.partial_ratio(trigger, corrected_lower) >= 80:
                about_query_detected = True
                break
        
        if not about_query_detected and corrected_lower.startswith('what is'):
            if any(term in corrected_lower for term in hub_specific_terms):
                about_query_detected = True
        
        if about_query_detected:
            matched_resources = self._handle_about_query(corrected_query, {'intent': 'about_query'})
            if matched_resources:
                return self._generate_about_response(corrected_query, matched_resources)

        if corrected_query.lower() in self._conversation_cache:
            return self._conversation_cache[corrected_query.lower()]
        
        intent_info = self._classify_user_intent(corrected_query)
        
        if intent_info.get('skip_ai') or intent_info.get('is_basic'):
            response = self._generate_basic_response(intent_info)
            self._conversation_cache[corrected_query.lower()] = response
            return response
        
        if intent_info['intent'] == 'sample_request':
            matched_resources = self._enhanced_semantic_search_with_faiss(corrected_query, intent_info, top_k=5)
            return self._generate_sample_response(corrected_query, matched_resources, intent_info)
        elif intent_info['intent'] == 'topic_content_request':
            matched_resources = self._enhanced_semantic_search_with_faiss(corrected_query, intent_info, top_k=8)
            return self._generate_topic_content_response(corrected_query, matched_resources, intent_info)
        else:
            matched_resources = self._enhanced_semantic_search_with_faiss(corrected_query, intent_info, top_k=5)
            
            if matched_resources:
                return self._generate_detailed_response(corrected_query, matched_resources)
            else:
                return self._generate_no_results_response(corrected_query)

    def _generate_sample_response(self, query, matched_resources, intent_info):
        """Generate response for sample requests"""
        if not matched_resources:
            return {
                'response': "I couldn't find any samples matching your request. Here are some available options:\n\n📚 Browse our knowledge base\n💬 Check forum discussions\n❓ View frequently asked questions\n🏢 Find CMI locations",
                'confidence': 'low',
                'suggestions': ['Find recent forum posts', 'Browse knowledge resources'],
                'matched_resources': []
            }
        
        response_parts = []
        query_lower = query.lower()
        
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

        sample_header = "📚 **Here are some examples from our knowledge base:**"
        for key, header in sample_type_map.items():
            if key in query_lower:
                sample_header = header
                break

        response_parts.append(sample_header)
        response_parts.append("")
        
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

    def debug_query_processing(self, query):
        """Debug method to understand query processing"""
        print(f"🔍 DEBUG: Original query: '{query}'")
        
        # Check spell correction
        corrected_query = self.process_query_with_correction(query)
        print(f"🔧 DEBUG: Corrected query: '{corrected_query}'")
        
        # Check intent classification
        intent_info = self._classify_user_intent(query)
        print(f"🎯 DEBUG: Intent info: {intent_info}")
        
        # Check topic extraction
        main_topic = self._extract_main_topic(query)
        print(f"📌 DEBUG: Main topic: {main_topic}")
        
        # Check content type
        content_type = self._extract_content_type(query)
        print(f"📂 DEBUG: Content type: {content_type}")
        
        # Check basic responses
        basic_intent = self._check_basic_response(query)
        print(f"💬 DEBUG: Basic response: {basic_intent}")
        
        return {
            'original_query': query,
            'corrected_query': corrected_query,
            'intent_info': intent_info,
            'main_topic': main_topic,
            'content_type': content_type,
            'basic_intent': basic_intent
        }
    
    def generate_source_response(self, source_id, source_title):
        """Generate detailed response for a specific source/resource"""
        try:
            # Get knowledge data from cache
            cache = get_knowledge_base_cache()
            knowledge_data = cache['knowledge_data']
            
            # Find the specific resource by ID or title
            target_resource = None
            for item in knowledge_data:
                # Try to match by ID first, then by title
                if (str(item.get('id')) == str(source_id) or 
                    item.get('title') == source_title or
                    item.get('title').lower() == source_title.lower()):
                    target_resource = item
                    break
            
            if not target_resource:
                return {
                    'response': f"❌ Sorry, I couldn't find the source: '{source_title}'. It might have been moved or updated.",
                    'confidence': 'low',
                    'suggestions': ['Search for similar content', 'Browse available resources', 'Ask a different question'],
                    'matched_resources': [],
                    'source_not_found': True
                }
            
            # Generate detailed response with full content
            response_parts = []
            
            # Add title
            response_parts.append(f"📄 **{target_resource['title']}**\n")
            
            # Add type/category if available
            if target_resource.get('type'):
                type_icon = {
                    'faq': '❓', 'forum': '💬', 'resource': '📄',
                    'publication': '📚', 'news': '📰', 'event': '📅',
                    'training': '🎓', 'technology': '💻', 'commodity': '🌾',
                    'cmi': '🏢', 'about': 'ℹ️'
                }.get(target_resource['type'], '📌')
                
                response_parts.append(f"{type_icon} **Type:** {target_resource['type'].title()}")
            
            # Add author if available
            if target_resource.get('author'):
                response_parts.append(f"👤 **Author:** {target_resource['author']}")
            
            # Add date if available
            if target_resource.get('date') or target_resource.get('created_at'):
                date_str = target_resource.get('date') or target_resource.get('created_at')
                response_parts.append(f"📅 **Date:** {date_str}")
            
            response_parts.append("")  # Empty line
            
            # Add full content/description
            full_content = target_resource.get('content', target_resource.get('description', ''))
            
            # Clean HTML tags if present
            import re
            clean_content = re.sub(r'<[^>]+>', '', full_content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            
            if clean_content:
                response_parts.append("📝 **Content:**")
                response_parts.append(clean_content)
            else:
                response_parts.append("📝 **Content:** No detailed content available for this resource.")
            
            # Add additional fields if available
            if target_resource.get('tags'):
                response_parts.append(f"\n🏷️ **Tags:** {', '.join(target_resource['tags'])}")
            
            if target_resource.get('category'):
                response_parts.append(f"📂 **Category:** {target_resource['category']}")
            
            # Add source link if available
            if target_resource.get('url') or target_resource.get('link'):
                link = target_resource.get('url') or target_resource.get('link')
                response_parts.append(f"\n🔗 **Source:** {link}")
            
            return {
                'response': '\n'.join(response_parts),
                'confidence': 'high',
                'suggestions': ['Ask about related topics', 'Find similar resources', 'What else can you help with?'],
                'matched_resources': [target_resource],
                'source_details': True,
                'ai_powered': True
            }
            
        except Exception as e:
            print(f"❌ Error in generate_source_response: {e}")
            return {
                'response': f"❌ Sorry, there was an error retrieving the source details. Please try again or ask about something else.",
                'confidence': 'low',
                'suggestions': ['Try a different search', 'Browse available topics', 'Ask for help'],
                'matched_resources': [],
                'error': True
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
        
        grouped_results = {}
        for match in matched_resources:
            resource_type = match['resource']['type']
            if resource_type not in grouped_results:
                grouped_results[resource_type] = []
            grouped_results[resource_type].append(match)
        
        response_parts = []
        response_parts.append(f"🎯 **{content_type.title()} about {main_topic}:**\n")
        
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
        
        description = resource.get('content', resource.get('description', ''))
        
        response_text = f"**{resource['title']}**\n\n{description}"
        response_text += f"\n\n📋 **Source:** {resource['type'].title()}"
        
        if resource.get('author'):
            response_text += f" by {resource['author']}"
        
        resources_to_show = []
        if len(matched_resources) > 1:
            resources_to_show = [resource]
            
        return {
            'response': response_text,
            'confidence': best_match['confidence'],
            'suggestions': self._generate_dynamic_suggestions(query, matched_resources),
            'matched_resources': resources_to_show, 
            'ai_powered': True,
            'local_ai': True,
            'faiss_enhanced': True
        }

    def _generate_dynamic_suggestions(self, query, matched_resources):
        """Generate contextual suggestions"""
        suggestions = []
        query_words = query.lower().split()
        
        if any(word in query_words for word in ['farm', 'crop', 'agriculture']):
            suggestions.extend(['Tell me about sustainable farming practices', 'Find crop disease management guides'])
        elif any(word in query_words for word in ['fish', 'aqua', 'tilapia']):
            suggestions.extend(['Show me fish farming techniques', 'What are common fish diseases?'])
        elif any(word in query_words for word in ['cmi', 'office', 'location']):
            suggestions.extend(['Find all CMI office locations', 'What services does CMI provide?'])
        
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
    
    def _generate_about_response(self, query, matched_resources):
        """Generate focused response for about queries"""
        if not matched_resources:
            return {
                'response': "I couldn't find specific information about that. However, I can tell you about the AANR Knowledge Hub - it's a comprehensive platform for agricultural, aquatic, and natural resources knowledge sharing.",
                'confidence': 'low',
                'suggestions': ['Tell me about AANR Knowledge Hub', 'What is the mission?', 'Show me key features'],
                'matched_resources': []
            }
        
        best_match = matched_resources[0]
        resource = best_match['resource']
        
        # Build focused response
        response_parts = []
        
        if resource.get('title'):
            title = resource['title']
            # Don't add redundant "About" prefix if title already contains it
            if not title.lower().startswith('about'):
                title = f"About {title}"
            response_parts.append(f"**{title}**\n")
        
        # Add section header if available and different from title
        if (resource.get('section') and resource['section'] and 
            resource['section'] not in resource.get('title', '')):
            response_parts.append(f"**{resource['section']}**\n")
        
        description = resource['description']
        if description:
            # Description is already cleaned in _handle_about_query, just use it directly
            response_parts.append(description)

        return {
            'response': '\n'.join(response_parts),
            'confidence': best_match['confidence'],
            'suggestions': self._generate_dynamic_suggestions(query, [best_match]),
            'matched_resources': [], 
            'ai_powered': True,
            'local_ai': True,
            'about_content': True
        }
    
def clear_knowledge_base_cache():
    """Clear the knowledge base cache to force reload"""
    global _knowledge_base_cache, _knowledge_base_last_updated, _faiss_index, _faiss_embeddings, _json_knowledge_cache
    
    _knowledge_base_cache = None
    _knowledge_base_last_updated = None
    _faiss_index = None
    _faiss_embeddings = None
    _json_knowledge_cache = None
    
    print("🔄 Knowledge base cache cleared - will reload on next request")

def force_reload_knowledge_base():
    """Force immediate reload of knowledge base"""
    clear_knowledge_base_cache()
    get_knowledge_base_cache()
    print("✅ Knowledge base forcefully reloaded")

def get_spell_correction_statistics(self):
    """Get spell correction performance statistics"""
    return get_spell_correction_stats()

# Global service instance with proper singleton pattern
_chatbot_service_instance = None
_service_lock = threading.Lock()

def get_chatbot_service():
    """Get or create the chatbot service instance with thread-safe singleton pattern"""
    global _chatbot_service_instance
    
    if _chatbot_service_instance is not None:
        return _chatbot_service_instance
    
    with _service_lock:
        if _chatbot_service_instance is not None:
            return _chatbot_service_instance
        
        print("🚀 Initializing ULTRA-FAST ChatbotService singleton...")
        _chatbot_service_instance = IntelligentChatbotService()
        print("✅ ULTRA-FAST ChatbotService singleton ready!")
        return _chatbot_service_instance

# SOLUTION #3: Start AI model loading in background during app startup
background_ai_warmup()

# Create the singleton instance
chatbot_service = get_chatbot_service()