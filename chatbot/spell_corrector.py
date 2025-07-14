import re
import os
import json
import nltk
import threading
from collections import defaultdict
from fuzzywuzzy import fuzz
from spellchecker import SpellChecker
from django.conf import settings
from django.core.cache import cache

try:
    nltk.data.find('corpora/words')
except LookupError:
    print("📥 Downloading NLTK words corpus...")
    nltk.download('words')

try:
    nltk.data.find('corpora/brown')
except LookupError:
    print("📥 Downloading NLTK brown corpus...")
    nltk.download('brown')

class DynamicSpellCorrector:
    """
    Dynamic spell corrector that learns from knowledge base content
    and user interactions without hardcoded vocabulary
    """
    
    def __init__(self):
        # Standard English dictionary       

        self.spell_checker = SpellChecker()
        
        # Dynamic patterns learned from data
        self.learned_patterns = {}
        self.word_cache = {}  
        self.knowledge_vocabulary = set()
        
        self.stopwords = self.load_stopwords()
        
        # Performance tracking
        self.correction_stats = {
            'total_corrections': 0,
            'pattern_corrections': 0,
            'algorithmic_corrections': 0,
            'cache_hits': 0
        }
        
        self.load_comprehensive_vocabulary()
        self.build_dynamic_vocabulary()
        self.learn_common_patterns()
        
        print(f"✅ DynamicSpellCorrector initialized with {len(self.knowledge_vocabulary)} domain words")
    
    def load_comprehensive_vocabulary(self):
        """Load comprehensive vocabulary from multiple sources"""
        try:
            from nltk.corpus import words, brown
            
            english_words = set(words.words())
            brown_words = set(word.lower() for word in brown.words() if word.isalpha())
            
            # Add domain-specific terms that should NOT be corrected
            domain_terms = {
                'faq', 'faqs', 'raise', 'aanr', 'cmi', 'aquaculture', 
                'fisheries', 'tilapia', 'bangus', 'palay', 'agri',
                'kmhub', 'webinar', 'seminar', 'doi', 'isbn',
                'pdf', 'api', 'cms', 'ui', 'ux', 'it', 'hr'
            }
            
            self.spell_checker.word_frequency.load_words(english_words | brown_words | domain_terms)
            
            print(f"✅ Loaded vocabulary with {len(domain_terms)} domain-specific terms")
            
        except ImportError:
            print("⚠️ NLTK not available, using basic spell checker")
    
    def build_dynamic_vocabulary(self):
        """Build vocabulary dynamically from knowledge base"""
        try:
            # Import here to avoid circular imports
            from chatbot.services import get_knowledge_base_cache
            
            cache = get_knowledge_base_cache()
            knowledge_data = cache.get('knowledge_data', [])
            
            # Extract all words from knowledge base
            for item in knowledge_data:
                # Extract from title
                if 'title' in item:
                    self.knowledge_vocabulary.update(self.extract_words(item['title']))
                
                # Extract from description/content
                if 'description' in item:
                    self.knowledge_vocabulary.update(self.extract_words(item['description']))
                
                if 'content' in item:
                    self.knowledge_vocabulary.update(self.extract_words(item['content']))
            
            # Add domain-specific vocabulary to spell checker
            self.spell_checker.word_frequency.load_words(self.knowledge_vocabulary)
            
            print(f"✅ Built vocabulary with {len(self.knowledge_vocabulary)} words from knowledge base")
            
        except Exception as e:
            print(f"⚠️ Could not load knowledge base vocabulary: {e}")
    
    def extract_words(self, text):
        """Extract meaningful words from text"""
        if not text:
            return set()
        
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        
        # Use self.stopwords instead of calling load_stopwords() again
        return set(word for word in words if word not in self.stopwords and len(word) > 2)

    def load_stopwords(self):
        """Load stopwords from the existing stopwords file"""
        try:
            stopwords_file = os.path.join(settings.BASE_DIR, 'utils', 'stopwords', 'stopwords.txt')
            
            if os.path.exists(stopwords_file):
                with open(stopwords_file, 'r', encoding='utf-8') as f:
                    stopwords = set(line.strip().lower() for line in f if line.strip())
                print(f"✅ Loaded {len(stopwords)} stopwords from utils/stopwords/stopwords.txt")
                return stopwords
            else:
                print(f"⚠️ Stopwords file not found at {stopwords_file}")
                # Fallback to basic stopwords
                return {
                    'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
                    'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 
                    'below', 'between', 'among', 'since', 'until', 'while', 'this', 'that', 'these', 
                    'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'any', 
                    'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own', 
                    'same', 'than', 'too', 'very', 'can', 'will', 'just', 'now', 'get', 'has', 
                    'had', 'have', 'his', 'her', 'its', 'our', 'out', 'off', 'over', 'under', 
                    'again', 'further', 'then', 'once'
                }
        except Exception as e:
            print(f"⚠️ Error loading stopwords: {e}")
            return set()
    
    def learn_common_patterns(self):
        """Learn common misspelling patterns from knowledge base content"""
        try:
            # Get frequently used words from knowledge base
            word_frequency = defaultdict(int)
            
            for word in self.knowledge_vocabulary:
                word_frequency[word] += 1
            
            # Get most common words (these are likely correct spellings)
            common_words = sorted(word_frequency.items(), key=lambda x: x[1], reverse=True)[:200]
            
            # Build phonetic and character-based patterns
            self.build_variant_patterns([word for word, _ in common_words])
            
            print(f"✅ Learned {len(self.learned_patterns)} dynamic spelling patterns")
            
        except Exception as e:
            print(f"⚠️ Could not learn patterns: {e}")
    
    def build_variant_patterns(self, common_words):
        """Build patterns based on common character substitutions and variations"""
        for word in common_words:
            if len(word) < 4:  # Skip very short words
                continue
                
            # Generate potential misspellings for each word
            variants = self.generate_word_variants(word)
            for variant in variants:
                if variant != word and len(variant) > 2:
                    self.learned_patterns[variant] = word
    
    def generate_word_variants(self, word):
        """Generate common misspelling variants of a word"""
        variants = set()
        
        for i in range(len(word) - 1):
            if word[i] == word[i + 1]:
                variant = word[:i] + word[i+1:]
                variants.add(variant)
        
        for i in range(len(word)):
            if i == 0 or word[i] != word[i-1]: 
                variant = word[:i] + word[i] + word[i:]
                variants.add(variant)

        swaps = {
            'ph': 'f', 'gh': 'f', 'tion': 'sion', 'c': 'k', 'qu': 'kw',
            'ei': 'ie', 'ie': 'ei', 'ough': 'uff', 'ight': 'ite'
        }
        for old, new in swaps.items():
            if old in word:
                variant = word.replace(old, new)
                variants.add(variant)
        
        for i in range(len(word) - 1):
            chars = list(word)
            chars[i], chars[i + 1] = chars[i + 1], chars[i]
            variant = ''.join(chars)
            variants.add(variant)
        
        if len(word) > 3:
            variants.add(word[1:])  
            variants.add(word[:-1]) 
        
        vowel_subs = {'a': 'e', 'e': 'a', 'i': 'e', 'o': 'a', 'u': 'o'}
        for i, char in enumerate(word):
            if char in vowel_subs:
                variant = word[:i] + vowel_subs[char] + word[i+1:]
                variants.add(variant)
        
        return variants
    
    def correct_spelling(self, text):
        """Main spell correction function"""
        if not text:
            return text
        
        # Check cache first
        if text in self.word_cache:
            self.correction_stats['cache_hits'] += 1
            return self.word_cache[text]
        
        words = text.split()
        corrected_words = []
        
        for word in words:
            corrected_word = self.correct_single_word(word)
            corrected_words.append(corrected_word)
        
        result = ' '.join(corrected_words)
        
        # Cache the result
        self.word_cache[text] = result
        
        return result
    
    def correct_single_word(self, word):
        """Correct a single word using multiple strategies"""
        original_word = word
        word_lower = word.lower()

        if word_lower in self.learned_patterns:
            corrected = self.learned_patterns[word_lower]
            self.correction_stats['pattern_corrections'] += 1
            self.correction_stats['total_corrections'] += 1
            print(f"🎯 Dynamic pattern: '{original_word}' → '{corrected}'")
            return corrected

        if word_lower in self.knowledge_vocabulary:
            return original_word
        
        if word_lower in self.spell_checker:
            return original_word
        
        candidates = self.spell_checker.candidates(word_lower)
        
        if not candidates:
            variants = self.generate_word_variants(word_lower)
            for variant in variants:
                if variant in self.knowledge_vocabulary or variant in self.spell_checker:
                    print(f"🔧 Dynamic variant: '{original_word}' → '{variant}'")
                    # Learn this pattern for future use
                    self.learned_patterns[word_lower] = variant
                    self.correction_stats['algorithmic_corrections'] += 1
                    self.correction_stats['total_corrections'] += 1
                    return variant
            return original_word
        
        best_candidate = self.find_best_candidate(word_lower, candidates)
        
        if best_candidate and best_candidate != word_lower:
            print(f"🔧 Spell correction: '{original_word}' → '{best_candidate}'")
            # Learn this pattern for future use
            self.learned_patterns[word_lower] = best_candidate
            self.correction_stats['algorithmic_corrections'] += 1
            self.correction_stats['total_corrections'] += 1
            return best_candidate
        
        return original_word
    
    def find_best_candidate(self, word, candidates):
        """Find the best correction candidate using multiple scoring criteria"""
        if not candidates:
            return None
        
        scored_candidates = []
        
        for candidate in candidates:
            score = 0
            
            edit_distance = self.edit_distance(word, candidate)
            score += (1.0 - edit_distance / max(len(word), len(candidate))) * 0.3
            
            fuzzy_score = fuzz.ratio(word, candidate) / 100.0
            score += fuzzy_score * 0.25
            
            if candidate in self.knowledge_vocabulary:
                score += 0.2
            
            try:
                frequency = self.spell_checker.word_frequency[candidate] if candidate in self.spell_checker.word_frequency else 0
            except (KeyError, AttributeError):
                frequency = 0
            score += min(frequency / 1000.0, 1.0) * 0.15

            length_diff = abs(len(word) - len(candidate))
            length_score = 1.0 - (length_diff / max(len(word), len(candidate)))
            score += length_score * 0.1
            
            scored_candidates.append((candidate, score))
        
        # Return best candidate
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[0][0] if scored_candidates else None
    
    def edit_distance(self, s1, s2):
        """Calculate edit distance between two strings"""
        if len(s1) < len(s2):
            return self.edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def update_patterns_from_feedback(self, original_query, corrected_query):
        """Learn from user interactions when they accept/modify corrections"""
        if original_query != corrected_query:
            original_words = original_query.lower().split()
            corrected_words = corrected_query.lower().split()
            
            # Align words and learn corrections
            min_len = min(len(original_words), len(corrected_words))
            for i in range(min_len):
                orig, corr = original_words[i], corrected_words[i]
                if orig != corr and len(orig) > 2 and len(corr) > 2:
                    self.learned_patterns[orig] = corr
                    print(f"📚 Learned from feedback: '{orig}' → '{corr}'")
    
    def get_correction_stats(self):
        """Get statistics about correction performance"""
        return {
            'total_corrections': self.correction_stats['total_corrections'],
            'pattern_corrections': self.correction_stats['pattern_corrections'],
            'algorithmic_corrections': self.correction_stats['algorithmic_corrections'],
            'cache_hits': self.correction_stats['cache_hits'],
            'learned_patterns_count': len(self.learned_patterns),
            'knowledge_vocabulary_size': len(self.knowledge_vocabulary),
            'pattern_efficiency': (
                self.correction_stats['pattern_corrections'] / 
                max(self.correction_stats['total_corrections'], 1)
            ) * 100
        }
    
    def save_learned_patterns(self):
        """Save learned patterns to file for persistence"""
        try:
            patterns_file = os.path.join(settings.BASE_DIR, 'chatbot', 'data', 'learned_patterns.json')
            os.makedirs(os.path.dirname(patterns_file), exist_ok=True)
            
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.learned_patterns, f, indent=2)
            
            print(f"💾 Saved {len(self.learned_patterns)} learned patterns")
            
        except Exception as e:
            print(f"⚠️ Could not save patterns: {e}")
    
    def load_learned_patterns(self):
        """Load previously learned patterns from file"""
        try:
            patterns_file = os.path.join(settings.BASE_DIR, 'chatbot', 'data', 'learned_patterns.json')
            
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    saved_patterns = json.load(f)
                
                self.learned_patterns.update(saved_patterns)
                print(f"📥 Loaded {len(saved_patterns)} previously learned patterns")
            
        except Exception as e:
            print(f"⚠️ Could not load saved patterns: {e}")

def advanced_fuzzy_match(query, text_items, threshold=70):
    """Advanced fuzzy matching with multiple algorithms"""
    matches = []
    
    for item in text_items:
        # Multiple matching strategies
        scores = []
        scores.append(fuzz.token_sort_ratio(query, item))
        scores.append(fuzz.token_set_ratio(query, item))
        scores.append(fuzz.partial_ratio(query, item))
        scores.append(fuzz.ratio(query, item))
        best_score = max(scores)
        
        if best_score >= threshold:
            matches.append((item, best_score))
    
    return sorted(matches, key=lambda x: x[1], reverse=True)

def fuzzy_match_keywords(query, keywords, threshold=75):
    """Match keywords using fuzzy matching"""
    query_lower = query.lower()
    matched_keywords = []
    
    for keyword in keywords:
        # Direct match
        if keyword in query_lower:
            matched_keywords.append((keyword, 100))
            continue
        
        # Fuzzy match
        ratio = fuzz.partial_ratio(keyword, query_lower)
        if ratio >= threshold:
            matched_keywords.append((keyword, ratio))
    
    return matched_keywords


_spell_corrector_instance = None
_corrector_lock = threading.Lock()

def get_spell_corrector():
    """Get or create the spell corrector instance with thread-safe singleton"""
    global _spell_corrector_instance
    
    if _spell_corrector_instance is not None: 
        return _spell_corrector_instance
    
    with _corrector_lock:
        if _spell_corrector_instance is not None:
            return _spell_corrector_instance
        
        print("🚀 Initializing DynamicSpellCorrector singleton...")
        _spell_corrector_instance = DynamicSpellCorrector()
        print("✅ DynamicSpellCorrector singleton ready!")
        return _spell_corrector_instance

def correct_spelling_dynamic(text):
    """Main function to correct spelling dynamically"""
    corrector = get_spell_corrector()
    return corrector.correct_spelling(text)

def get_spell_correction_stats():
    """Get spell correction statistics"""
    corrector = get_spell_corrector()
    return corrector.get_correction_stats()