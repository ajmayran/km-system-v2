import re
import logging
import numpy as np
from django.db import models
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from spacy.lang.en.stop_words import STOP_WORDS

# Import your existing search functions
from utils.search_function import preprocess_text, find_similar_resources

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

class ChatbotService:
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
            print("Loaded spaCy model: en_core_web_md")
        except OSError:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("Loaded spaCy model: en_core_web_sm")
            except OSError:
                print("Warning: No spaCy model found. Using basic processing.")
                self.nlp = None
        
        # Create enhanced stopwords list
        self.custom_stopwords = self._load_custom_stopwords()
        
        self._load_knowledge_base()

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

    def _process_text_with_spacy(self, text):
        """Advanced text processing using spaCy"""
        if not self.nlp or not text:
            return preprocess_text(text)  # Fallback to your existing function
        
        # Process with spaCy
        doc = self.nlp(text.lower())
        
        # Extract meaningful tokens
        processed_tokens = []
        for token in doc:
            # Skip if token is:
            # - stopword, punctuation, space, or custom stopword
            # - too short or too long
            # - not alphabetic (numbers, symbols)
            if (token.is_stop or token.is_punct or token.is_space or 
                token.text in self.custom_stopwords or
                len(token.text) < 3 or len(token.text) > 20 or
                not token.text.isalpha()):
                continue
            
            # Use lemma for better semantic matching
            lemma = token.lemma_.strip()
            if lemma and lemma not in self.custom_stopwords:
                processed_tokens.append(lemma)
        
        # Extract named entities (locations, organizations, etc.)
        entities = [ent.text.lower() for ent in doc.ents 
                   if ent.label_ in ['GPE', 'ORG', 'PRODUCT', 'EVENT'] and len(ent.text) > 2]
        
        # Combine tokens and entities
        all_terms = processed_tokens + entities
        
        return ' '.join(set(all_terms))  # Remove duplicates

    def _extract_semantic_keywords(self, text):
        """Extract semantic keywords using spaCy"""
        if not self.nlp or not text:
            return self._extract_keywords(text)  # Fallback
        
        doc = self.nlp(text.lower())
        keywords = []
        
        # Extract important nouns and adjectives
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and 
                not token.is_stop and 
                not token.is_punct and
                len(token.text) > 2 and
                token.text.isalpha() and
                token.text not in self.custom_stopwords):
                keywords.append(token.lemma_)
        
        # Extract noun phrases
        noun_phrases = []
        for chunk in doc.noun_chunks:
            if len(chunk.text) > 3 and len(chunk.text.split()) <= 3:
                cleaned = ' '.join([token.lemma_ for token in chunk 
                                 if not token.is_stop and token.text.isalpha()])
                if cleaned:
                    noun_phrases.append(cleaned)
        
        # Extract named entities
        entities = [ent.lemma_ for ent in doc.ents 
                   if ent.label_ in ['GPE', 'ORG', 'PRODUCT', 'EVENT']]
        
        all_keywords = keywords + noun_phrases + entities
        return list(set(all_keywords))  # Remove duplicates

    def _calculate_spacy_similarity(self, query_doc, text_doc):
        """Calculate semantic similarity using spaCy word vectors"""
        if not self.nlp or not query_doc.has_vector or not text_doc.has_vector:
            return 0.0
        
        similarity = query_doc.similarity(text_doc)
        return float(similarity)

    def _load_knowledge_base(self):
        """Load comprehensive knowledge base with advanced NLP processing"""
        self.knowledge_data = []
        self.document_texts = []
        
        try:
            print("Loading knowledge base with advanced spaCy NLP processing...")
            
            # 1. Load Resource Metadata
            resources = ResourceMetadata.objects.filter(is_approved=True)
            print(f"Found {resources.count()} approved resources")
            
            for resource in resources:
                try:
                    tags = [tag.name for tag in resource.tags.all()]
                    commodities = [commodity.commodity_name for commodity in resource.commodities.all()]
                    
                    # Create combined text for NLP processing
                    combined_text = f"{resource.title} {resource.description} {' '.join(tags)} {' '.join(commodities)}"
                    processed_text = self._process_text_with_spacy(combined_text)
                    semantic_keywords = self._extract_semantic_keywords(combined_text)
                    
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
                        'processed_text': processed_text,
                        'semantic_keywords': semantic_keywords,
                        'raw_text': combined_text,
                        'spacy_doc': self.nlp(combined_text) if self.nlp else None
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(processed_text)
                    
                except Exception as e:
                    print(f"Error processing resource {resource.id}: {e}")
                    continue

            # 2. Load Knowledge Categories
            knowledge_categories = KnowledgeResources.objects.filter(status='active')
            print(f"Found {knowledge_categories.count()} knowledge categories")
            
            for category in knowledge_categories:
                combined_text = f"{category.knowledge_title} {category.knowledge_description}"
                processed_text = self._process_text_with_spacy(combined_text)
                semantic_keywords = self._extract_semantic_keywords(combined_text)
                
                knowledge_item = {
                    'id': f"category_{category.knowledge_id}",
                    'actual_id': category.knowledge_id,
                    'title': category.knowledge_title,
                    'description': category.knowledge_description,
                    'type': 'category',
                    'slug': category.slug,
                    'url': f'/cmis/knowledge-resources/?type={category.machine_name}',
                    'processed_text': processed_text,
                    'semantic_keywords': semantic_keywords,
                    'raw_text': combined_text,
                    'spacy_doc': self.nlp(combined_text) if self.nlp else None
                }
                
                self.knowledge_data.append(knowledge_item)
                self.document_texts.append(processed_text)

            # 3. Load Commodities
            commodities = Commodity.objects.filter(status='active')
            print(f"Found {commodities.count()} commodities")
            
            for commodity in commodities:
                combined_text = f"{commodity.commodity_name} {commodity.description}"
                processed_text = self._process_text_with_spacy(combined_text)
                semantic_keywords = self._extract_semantic_keywords(combined_text)
                
                knowledge_item = {
                    'id': f"commodity_{commodity.commodity_id}",
                    'actual_id': commodity.commodity_id,
                    'title': commodity.commodity_name,
                    'description': commodity.description,
                    'type': 'commodity',
                    'url': f'/cmis/commodities/{commodity.slug}',
                    'processed_text': processed_text,
                    'semantic_keywords': semantic_keywords,
                    'raw_text': combined_text,
                    'spacy_doc': self.nlp(combined_text) if self.nlp else None
                }
                
                self.knowledge_data.append(knowledge_item)
                self.document_texts.append(processed_text)

            # 4. Load Forum Discussions
            forums = Forum.objects.all()
            print(f"Found {forums.count()} forum discussions")
            
            for forum in forums:
                try:
                    forum_commodities = [commodity.commodity_name for commodity in forum.commodity_id.all()]
                    combined_text = f"{forum.forum_title} {forum.forum_question} {' '.join(forum_commodities)}"
                    processed_text = self._process_text_with_spacy(combined_text)
                    semantic_keywords = self._extract_semantic_keywords(combined_text)
                    
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
                        'processed_text': processed_text,
                        'semantic_keywords': semantic_keywords,
                        'raw_text': combined_text,
                        'spacy_doc': self.nlp(combined_text) if self.nlp else None
                    }
                    
                    self.knowledge_data.append(knowledge_item)
                    self.document_texts.append(processed_text)
                    
                except Exception as e:
                    print(f"Error processing forum {forum.forum_id}: {e}")
                    continue

            # 5. Load CMI Data
            cmis = CMI.objects.filter(status='active')
            print(f"Found {cmis.count()} CMI entries")
            
            for cmi in cmis:
                combined_text = f"{cmi.cmi_name} {cmi.cmi_meaning} {cmi.cmi_description} {cmi.address}"
                processed_text = self._process_text_with_spacy(combined_text)
                semantic_keywords = self._extract_semantic_keywords(combined_text)
                
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
                    'processed_text': processed_text,
                    'semantic_keywords': semantic_keywords,
                    'raw_text': combined_text,
                    'spacy_doc': self.nlp(combined_text) if self.nlp else None
                }
                
                self.knowledge_data.append(knowledge_item)
                self.document_texts.append(processed_text)

            # 6. Load FAQ Data
            faqs = FAQ.objects.filter(is_active=True)
            print(f"Found {faqs.count()} FAQ entries")
            
            for faq in faqs:
                question_text = faq.question
                answer_text = faq.answer
                combined_text = f"{faq.question} {faq.answer}"

                question_processed = self._process_text_with_spacy(question_text)
                answer_processed = self._process_text_with_spacy(answer_text)
                combined_processed = self._process_text_with_spacy(combined_text)

                question_keywords = self._extract_semantic_keywords(question_text)
                answer_keywords = self._extract_semantic_keywords(answer_text)
                all_keywords = list(set(question_keywords + answer_keywords))
                
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
                    'question_processed': question_processed,
                    'answer_processed': answer_processed,
                    'processed_text': combined_processed,
                    'question_keywords': question_keywords,
                    'answer_keywords': answer_keywords,
                    'semantic_keywords': all_keywords,
                    'raw_text': combined_text,
                    'spacy_doc': self.nlp(combined_text) if self.nlp else None,
                    'question_doc': self.nlp(question_text) if self.nlp else None,
                    'answer_doc': self.nlp(answer_text) if self.nlp else None
                }
                
                self.knowledge_data.append(knowledge_item)
                self.document_texts.append(f"{question_processed} {combined_processed}")

            # Create TF-IDF vectors for all documents
            if self.document_texts:
                print(f"Creating TF-IDF vectors for {len(self.document_texts)} documents...")
                self.knowledge_vectors = self.vectorizer.fit_transform(self.document_texts)
                print(f"Created vectors with shape: {self.knowledge_vectors.shape}")
            
            print(f"Successfully loaded {len(self.knowledge_data)} items with advanced spaCy NLP processing")
                
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            print(f"Error loading knowledge base: {e}")

    def _analyze_query_specificity(self, query):
            """Analyze if query is specific or general"""
            words = query.strip().split()
            word_count = len(words)
            
            # Very broad terms that indicate general queries
            general_terms = [
                'all', 'everything', 'anything', 'show', 'list', 'find', 'get', 'what',
                'tell', 'about', 'info', 'information', 'help', 'overview', 'general'
            ]
            
            # Specific indicators
            specific_terms = [
                'how to', 'step by step', 'procedure', 'when', 'where exactly', 
                'which one', 'specific', 'particular', 'detailed'
            ]
            
            query_lower = query.lower()
            
            # Check for general terms
            has_general_terms = any(term in query_lower for term in general_terms)
            
            # Check for specific terms
            has_specific_terms = any(term in query_lower for term in specific_terms)
            
            # Determine specificity
            if word_count <= 2 and not has_specific_terms:
                return 'very_general'
            elif has_general_terms and not has_specific_terms:
                return 'general'
            elif has_specific_terms:
                return 'specific'
            elif word_count <= 4:
                return 'somewhat_general'
            else:
                return 'specific'             



    def find_similar_content(self, query, threshold=0.05, top_k=5):
        """Enhanced version with better handling for general queries"""
        if not query or not self.knowledge_data:
            return []
        
        try:
            print(f"Searching for: '{query}' in {len(self.knowledge_data)} items")
            
            # Analyze query specificity
            specificity = self._analyze_query_specificity(query)
            print(f"Query specificity: {specificity}")
            
            # Adjust parameters based on specificity
            if specificity in ['very_general', 'general']:
                threshold = 0.01  # Lower threshold for general queries
                top_k = min(10, len(self.knowledge_data))  # More results
            elif specificity == 'somewhat_general':
                threshold = 0.02
                top_k = 7
            
            processed_query = self._process_text_with_spacy(query)
            query_lower = query.lower()
            query_doc = self.nlp(query.lower()) if self.nlp else None
            
            # Extract query keywords for better matching
            query_words = set(query_lower.split())
            query_keywords = set(self._extract_semantic_keywords(query))
            
            results = []
            
            # For very general queries, use keyword expansion
            if specificity == 'very_general':
                return self._handle_very_general_query(query, query_words, top_k)
            
            # Method 1: TF-IDF Similarity
            tfidf_scores = {}
            if self.knowledge_vectors is not None and processed_query.strip():
                query_vector = self.vectorizer.transform([processed_query])
                similarities = cosine_similarity(query_vector, self.knowledge_vectors).flatten()
                tfidf_scores = {i: similarities[i] for i in range(len(similarities))}
                
            # Method 2: spaCy Semantic Similarity
            spacy_scores = {}
            if self.nlp and query_doc and query_doc.has_vector:
                for i, item in enumerate(self.knowledge_data):
                    if item.get('spacy_doc') and item['spacy_doc'].has_vector:
                        semantic_sim = self._calculate_spacy_similarity(query_doc, item['spacy_doc'])
                        spacy_scores[i] = semantic_sim
            
            # Method 3: Enhanced Text Matching with category boosting
            text_match_scores = {}
            for i, item in enumerate(self.knowledge_data):
                text_score = self._calculate_enhanced_text_matching_v2(
                    query_words, query_keywords, item, specificity
                )
                text_match_scores[i] = text_score
            
            # Combine scores with adjusted weights
            weights = self._get_scoring_weights_v2(specificity)
            
            for i in range(len(self.knowledge_data)):
                tfidf_score = tfidf_scores.get(i, 0) * weights['tfidf']
                spacy_score = spacy_scores.get(i, 0) * weights['spacy']
                text_score = text_match_scores.get(i, 0) * weights['text']
                
                combined_score = tfidf_score + spacy_score + text_score
                
                # Adjust threshold based on specificity
                min_relevance = 0.01 if specificity in ['general', 'very_general'] else 0.05
                
                if combined_score >= threshold and text_score > min_relevance:
                    item = self.knowledge_data[i]
                    results.append({
                        'resource': item,
                        'similarity_score': float(combined_score),
                        'tfidf_score': float(tfidf_score),
                        'spacy_score': float(spacy_score),
                        'text_score': float(text_score),
                        'confidence': self._get_confidence_level_v2(combined_score, specificity)
                    })
            
            # Sort and diversify results for general queries
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            if specificity in ['general', 'very_general']:
                results = self._diversify_results(results, top_k)
            
            print(f"Found {len(results)} relevant results above threshold {threshold}")
            
            return results[:top_k]
        
        except Exception as e:
            print(f"Error in find_similar_content: {e}")
            return []
        
    def _handle_very_general_query(self, query, query_words, top_k):
        """Handle very general queries by showing diverse content"""
        results = []
        query_lower = query.lower()
        
        # Category mapping for general terms
        category_mappings = {
            'rice': ['rice', 'crop', 'grain'],
            'fish': ['fish', 'aquaculture', 'tilapia', 'aquatic'],
            'farming': ['farm', 'agriculture', 'crop', 'plant'],
            'cmi': ['cmi', 'office', 'location', 'contact'],
            'training': ['training', 'seminar', 'workshop', 'education'],
            'technology': ['technology', 'innovation', 'equipment'],
            'forum': ['forum', 'discussion', 'question', 'community']
        }
        
        # Score items based on general relevance
        for i, item in enumerate(self.knowledge_data):
            score = 0
            item_text = f"{item.get('title', '')} {item.get('description', '')}".lower()
            
            # Direct word matches
            for word in query_words:
                if word in item_text:
                    score += 0.5
            
            # Category matches
            for category, keywords in category_mappings.items():
                if any(word in query_words for word in [category]):
                    if any(keyword in item_text for keyword in keywords):
                        score += 0.7
            
            # Type diversity bonus
            type_bonus = {
                'faq': 0.2, 'forum': 0.15, 'resource': 0.1, 
                'commodity': 0.15, 'cmi': 0.1
            }
            score += type_bonus.get(item.get('type'), 0)
            
            if score > 0.1:
                results.append({
                    'resource': item,
                    'similarity_score': float(score),
                    'tfidf_score': 0.0,
                    'spacy_score': 0.0,
                    'text_score': float(score),
                    'confidence': 'medium' if score > 0.5 else 'low'
                })
        
        # Sort and diversify
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return self._diversify_results(results, top_k)
        
    def _diversify_results(self, results, max_results):
        """Ensure diverse content types in results"""
        if len(results) <= max_results:
            return results
        
        diversified = []
        type_counts = {}
        
        # First pass: ensure type diversity
        for result in results:
            resource_type = result['resource'].get('type', 'unknown')
            
            if type_counts.get(resource_type, 0) < 2:  # Max 2 per type initially
                diversified.append(result)
                type_counts[resource_type] = type_counts.get(resource_type, 0) + 1
                
            if len(diversified) >= max_results:
                break
        
        # Second pass: fill remaining slots with best scores
        if len(diversified) < max_results:
            for result in results:
                if result not in diversified:
                    diversified.append(result)
                    if len(diversified) >= max_results:
                        break
        
        return diversified
    
    def _calculate_enhanced_text_matching_v2(self, query_words, query_keywords, item, specificity):
        """Enhanced text matching with specificity awareness"""
        title = item.get('title', '').lower()
        description = item.get('description', '').lower()
        raw_text = item.get('raw_text', '').lower()
        
        score = 0
        
        # Adjust weights based on specificity
        if specificity in ['very_general', 'general']:
            title_weight = 0.6  # Higher weight for titles in general queries
            desc_weight = 0.3
            keyword_weight = 0.1
        else:
            title_weight = 0.4
            desc_weight = 0.4
            keyword_weight = 0.2
        
        # Title matching
        title_words = set(title.split())
        title_overlap = len(query_words & title_words) / max(len(query_words), 1)
        score += title_overlap * title_weight
        
        # Description matching
        desc_words = set(description.split())
        desc_overlap = len(query_words & desc_words) / max(len(query_words), 1)
        score += desc_overlap * desc_weight
        
        # Keyword matching
        item_keywords = set(item.get('semantic_keywords', []))
        keyword_overlap = len(query_keywords & item_keywords) / max(len(query_keywords), 1)
        score += keyword_overlap * keyword_weight
        
        # Exact phrase bonus for general queries
        if specificity in ['very_general', 'general']:
            for word in query_words:
                if len(word) > 2:
                    if word in title:
                        score += 0.2
                    elif word in description:
                        score += 0.1
        
        return score
    
    def _get_scoring_weights_v2(self, specificity):
        """Get scoring weights based on query specificity"""
        if specificity == 'very_general':
            return {'tfidf': 0.1, 'spacy': 0.2, 'text': 0.7}
        elif specificity == 'general':
            return {'tfidf': 0.2, 'spacy': 0.3, 'text': 0.5}
        elif specificity == 'somewhat_general':
            return {'tfidf': 0.25, 'spacy': 0.35, 'text': 0.4}
        else:  # specific
            return {'tfidf': 0.3, 'spacy': 0.4, 'text': 0.3}

    def _get_confidence_level_v2(self, similarity_score, specificity):
        """Enhanced confidence calculation considering specificity"""
        if specificity in ['very_general', 'general']:
            if similarity_score >= 0.3:
                return 'high'
            elif similarity_score >= 0.15:
                return 'medium'
            else:
                return 'low'
        else:
            if similarity_score >= 0.6:
                return 'high'
            elif similarity_score >= 0.3:
                return 'medium'
            else:
                return 'low'



    def _extract_keywords(self, text):
        """Fallback keyword extraction (your original method)"""
        if not text:
            return []
        
        text = text.lower()
        words = re.findall(r'\b\w{3,}\b', text)
        
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'can', 'may', 'might', 'must'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return list(set(keywords))
    
    def generate_response(self, query):
        """Enhanced response generation with better general query handling"""
        query = query.strip()
        query_lower = query.lower()
        
        # Handle greetings and common phrases (keep existing code)
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'howdy', 'greetings']
        farewells = ['bye', 'goodbye', 'see you', 'farewell', 'thanks', 'thank you']
        help_requests = ['help', 'assist', 'support', 'guide']
        
        if any(greeting in query_lower for greeting in greetings):
            return {
                'response': '👋 Hello! I\'m your AI assistant for the AANR Knowledge Management System!\n\nI can help you find information about:\n• 🌾 Agricultural resources, commodities & farming techniques\n• 🐟 Aquaculture & fisheries management\n• 🌲 Natural resources & environmental data\n• 💬 Community forum discussions & expert advice\n• 🏢 CMI locations, contacts & services\n• ❓ Frequently asked questions & answers\n• 📚 Research publications & technical documents\n• 🎓 Training programs & educational materials\n• 📰 Latest news & policy updates\n• 🛠️ Technologies & tools for agriculture\n\nJust ask me anything about the system - I\'ll search through all available resources to find what you need!',
                'confidence': 'high',
                'suggestions': [
                    'What can I find in this system?',
                    'Show me available resources',
                    'Find expert discussions',
                    'What training programs are available?'
                ],
                'matched_resources': []
            }
        
        # Analyze query specificity
        specificity = self._analyze_query_specificity(query)
        
        # Use advanced NLP similarity search with adjusted parameters
        similar_content = self.find_similar_content(query, threshold=0.02, top_k=8)
        
        if not similar_content:
            return {
                'response': f'I searched for "{query}" but couldn\'t find close matches 🤔\n\nTry being more specific or use these suggestions:',
                'confidence': 'low',
                'suggestions': [
                    'Show me popular topics',
                    'Find CMI locations',
                    'Browse forum discussions',
                    'What are common questions?'
                ],
                'matched_resources': []
            }
        
        # Handle different response types based on specificity and results
        if specificity in ['very_general', 'general'] and len(similar_content) > 3:
            return self._generate_multiple_results_response(query, similar_content, specificity)
        else:
            return self._generate_single_result_response(query, similar_content)


    def _generate_multiple_results_response(self, query, similar_content, specificity):
        """Generate response for general queries with multiple results"""
        response_parts = []
        
        if specificity == 'very_general':
            response_parts.append(f'🔍 Here are various resources related to "{query}":')
        else:
            response_parts.append(f'📚 I found several relevant resources for "{query}":')
        
        response_parts.append('')
        
        # Group results by type
        grouped_results = {}
        for match in similar_content[:6]:  # Show up to 6 results
            resource = match['resource']
            resource_type = resource.get('type', 'other')
            
            if resource_type not in grouped_results:
                grouped_results[resource_type] = []
            grouped_results[resource_type].append(match)
        
        # Present results by category
        type_icons = {
            'faq': '❓', 'forum': '💬', 'resource': '📄', 
            'commodity': '🌾', 'cmi': '🏢', 'category': '📚'
        }
        
        for resource_type, matches in grouped_results.items():
            icon = type_icons.get(resource_type, '📌')
            type_name = resource_type.replace('_', ' ').title()
            
            response_parts.append(f'{icon} **{type_name}s:**')
            
            for match in matches[:2]:  # Max 2 per type
                resource = match['resource']
                title = resource['title'][:50] + '...' if len(resource['title']) > 50 else resource['title']
                response_parts.append(f'• {title}')
            
            response_parts.append('')
        
        # Generate suggestions
        suggestions = []
        for match in similar_content[:3]:
            resource = match['resource']
            if resource['type'] == 'faq':
                suggestions.append(f"❓ {resource['title'][:30]}...")
            elif resource['type'] == 'forum':
                suggestions.append(f"💬 {resource['title'][:30]}...")
            else:
                suggestions.append(f"📄 {resource['title'][:30]}...")
        
        return {
            'response': '\n'.join(response_parts),
            'confidence': 'medium',
            'suggestions': suggestions,
            'matched_resources': [match['resource'] for match in similar_content[:6]]
        }

    def _generate_single_result_response(self, query, similar_content):
        """Generate response for specific queries with single best result"""
        best_match = similar_content[0]
        resource = best_match['resource']
        similarity_score = best_match['similarity_score']
        confidence = best_match['confidence']
        
        # Add type-specific information (keep existing logic)
        if resource['type'] == 'faq':
            response_parts = [f"**{resource['title']}**", "", resource['description']]
            
            # Add related FAQs as suggestions
            related_faqs = []
            for match in similar_content[1:4]:
                if match['resource']['type'] == 'faq':
                    related_faqs.append(f"FAQ: {match['resource']['question'][:40]}...")
            
            if not related_faqs:
                related_faqs = [
                    'More questions about RAISE',
                    'Find CMI locations',
                    'Browse forum discussions'
                ]
            
            return {
                'response': '\n'.join(response_parts),
                'confidence': 'high' if similarity_score > 0.3 else confidence,
                'suggestions': related_faqs,
                'matched_resources': [match['resource'] for match in similar_content[:3]]
            }
        
        else:
            # Handle other resource types (keep existing logic)
            if similarity_score >= 0.5:
                intro = f"✅ **{resource['title']}**"
            elif similarity_score >= 0.2:
                intro = f"📚 **{resource['title']}**"
            else:
                intro = f"💡 **{resource['title']}**"
            
            response_parts = [intro, "", resource['description']]
            
            # Add type-specific information
            if resource['type'] == 'resource':
                type_labels = {
                    'event': 'Event 📅',
                    'technology': 'Technology ⚙️',
                    'publication': 'Publication 📄',
                    'training': 'Training 🎓',
                    'news': 'News 📰',
                    'policy': 'Policy 📜',
                    'project': 'Project 📊',
                    'product': 'Product 🛠️',
                    'media': 'Media 🎥'
                }
                resource_type = type_labels.get(resource['resource_type'], resource['resource_type'].title())
                response_parts.append(f"\n📋 **Type:** {resource_type}")
            elif resource['type'] == 'forum':
                response_parts.append(f"\n💬 **Forum Discussion by:** {resource['author']}")
            elif resource['type'] == 'cmi':
                if resource.get('location'):
                    response_parts.append(f"\n📍 **Location:** {resource['location']}")
                if resource.get('contact'):
                    response_parts.append(f"\n📞 **Contact:** {resource['contact']}")
            
            # Generate contextual suggestions
            suggestions = []
            for match in similar_content[1:4]:
                res = match['resource']
                if res['type'] == 'faq':
                    suggestions.append(f"FAQ: {res['question'][:30]}...")
                elif res['type'] == 'forum':
                    suggestions.append(f"Discussion: {res['title'][:25]}...")
                else:
                    suggestions.append(f"{res['type'].title()}: {res['title'][:20]}...")
            
            return {
                'response': '\n'.join(response_parts),
                'confidence': confidence,
                'suggestions': suggestions[:3],
                'matched_resources': [match['resource'] for match in similar_content[:3]]
            }


# Global instance
chatbot_service = ChatbotService()