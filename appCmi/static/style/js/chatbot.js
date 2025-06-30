class IntelligentChatbot {
    constructor() {
        this.sessionId = null;
        this.sessionExpiresAt = null;
        this.sessionCreatedAt = null;
        this.isOpen = false;
        this.isMinimized = false;
        this.messageHistory = [];
        this.aiEnabled = true;
        this.initializeElements();
        this.bindEvents();
        this.loadFromStorage();
        this.addWelcomeMessage();
        this.loadSessionHistory();
    }

    initializeElements() {
        this.toggle = document.getElementById('chatbot-toggle');
        this.widget = document.getElementById('chatbot-widget');
        this.messages = document.getElementById('chatbot-messages');
        this.input = document.getElementById('chatbot-input');
        this.sendBtn = document.getElementById('chatbot-send');
        this.suggestions = document.getElementById('chatbot-suggestions');
        this.typing = document.getElementById('chatbot-typing');
        this.minimizeBtn = document.getElementById('chatbot-minimize');
        this.closeBtn = document.getElementById('chatbot-close');
    }

    async loadSessionHistory() {
        // Check if we have a stored session ID
        const savedState = this.getStoredState();
        if (savedState && savedState.sessionId) {
            try {
                const response = await fetch(`/chatbot/session-history/?session_id=${savedState.sessionId}`);
                const data = await response.json();

                if (response.ok && !data.session_expired) {
                    // Session is still valid, restore chat history
                    this.sessionId = data.session_id;
                    this.sessionExpiresAt = new Date(data.session_expires_at);
                    this.sessionCreatedAt = new Date(data.session_created_at);

                    // Clear existing messages and restore from server
                    this.messages.innerHTML = '';

                    // Add welcome message first
                    this.addWelcomeMessage();

                    // Restore all messages from session
                    for (const msg of data.messages) {
                        this.addMessage(msg.message, 'user', {}, false); // Don't save to storage
                        this.addMessage(msg.response, 'bot', {
                            confidence: msg.confidence_level,
                            ai_powered: true,
                            restored: true
                        }, false);
                    }

                    console.log(`🔄 Restored ${data.messages.length} messages from session ${this.sessionId}`);
                    console.log(`⏰ Session expires at: ${this.sessionExpiresAt.toLocaleString()}`);

                    // Start session expiry checker
                    this.startSessionExpiryChecker();

                } else {
                    // Session expired or not found, clear stored session
                    console.log('🕐 Previous session expired, starting fresh');
                    this.clearStoredSession();
                    this.addWelcomeMessage();
                }
            } catch (error) {
                console.error('Error loading session history:', error);
                this.addWelcomeMessage();
            }
        } else {
            // No previous session, add welcome message
            this.addWelcomeMessage();
        }
    }

    startSessionExpiryChecker() {
        // Check session expiry every minute
        if (this.sessionExpiryTimer) {
            clearInterval(this.sessionExpiryTimer);
        }

        this.sessionExpiryTimer = setInterval(() => {
            if (this.sessionExpiresAt && new Date() > this.sessionExpiresAt) {
                this.handleSessionExpiry();
            }
        }, 60000); // Check every minute
    }

    handleSessionExpiry() {
        console.log('🕐 Session expired, clearing chat');
        this.clearStoredSession();
        this.messages.innerHTML = '';
        this.addMessage(
            '⏰ Your chat session has expired (24 hours). Starting a fresh conversation!',
            'bot',
            { confidence: 'high', system_message: true }
        );
        setTimeout(() => {
            this.addWelcomeMessage();
        }, 1000);

        if (this.sessionExpiryTimer) {
            clearInterval(this.sessionExpiryTimer);
        }
    }

    addWelcomeMessage() {
        const existingBotMessages = this.messages.querySelectorAll('.bot-message');
        if (existingBotMessages.length === 0) {
            // Add initial welcome message with AI branding
            this.addMessage(`
                🤖 Hello! I'm your <strong>intelligent AI assistant</strong> for AANR Knowledge Hub.<br><br>
                <em>✨ Powered by local AI models - your data stays secure!</em><br><br>
                I can intelligently help you with:<br>
                🌾 Agriculture & Farming Resources<br>
                🐟 Aquatic & Natural Resources<br>
                💬 Forum Discussions & Expert Advice<br>
                🏢 CMI Locations & Services<br><br>
                Try asking me: <em>"Give me sample 1 FAQ"</em> or <em>"Show me farming resources"</em>
            `, 'bot', { ai_powered: true, local_ai: true });
        }
    }

    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;

        this.messageHistory.push({ type: 'user', content: message, timestamp: new Date() });

        this.input.value = '';
        this.sendBtn.disabled = true;
        this.clearSuggestions();

        this.addMessage(message, 'user');
        this.showTyping();

        try {
            const response = await fetch('/chatbot/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            const data = await response.json();
            this.hideTyping();

            if (response.ok) {
                // Update session information
                this.sessionId = data.session_id;
                if (data.session_expires_at) {
                    this.sessionExpiresAt = new Date(data.session_expires_at);
                }
                if (data.session_created_at) {
                    this.sessionCreatedAt = new Date(data.session_created_at);
                }

                // Start expiry checker if not already running
                if (!this.sessionExpiryTimer) {
                    this.startSessionExpiryChecker();
                }

                this.messageHistory.push({
                    type: 'bot',
                    content: data.response,
                    confidence: data.confidence,
                    ai_powered: data.ai_powered,
                    local_ai: data.local_ai,
                    timestamp: new Date()
                });

                // Add bot message with typing animation and AI indicators
                this.addBotMessageWithTyping(data.response, data, () => {
                    // Show AI status if available
                    if (data.ai_powered) {
                        this.addAIStatusIndicator(data);
                    }

                    // Show suggestions
                    if (data.suggestions && data.suggestions.length > 0) {
                        setTimeout(() => {
                            this.showSuggestions(data.suggestions);
                        }, 500);
                    }

                    // Show related resources
                    if (data.matched_resources && data.matched_resources.length > 0) {
                        setTimeout(() => {
                            this.addRelatedResourceCards(data.matched_resources);
                        }, 1000);
                    }
                });

            } else {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
                console.error('Intelligent Chatbot API error:', data);
            }
        } catch (error) {
            console.error('Intelligent Chatbot error:', error);
            this.hideTyping();
            this.addMessage('Sorry, I\'m having trouble connecting. Please check your internet connection and try again.', 'bot');
        }

        this.saveToStorage();
    }

    getStoredState() {
        try {
            const saved = localStorage.getItem('chatbot-state');
            return saved ? JSON.parse(saved) : null;
        } catch (e) {
            console.warn('Could not load chatbot state:', e);
            return null;
        }
    }

    clearStoredSession() {
        this.sessionId = null;
        this.sessionExpiresAt = null;
        this.sessionCreatedAt = null;
        this.messageHistory = [];

        if (this.sessionExpiryTimer) {
            clearInterval(this.sessionExpiryTimer);
        }

        localStorage.removeItem('chatbot-state');
    }



    bindEvents() {
        if (!this.toggle || !this.sendBtn || !this.input) {
            console.warn('Chatbot elements not found');
            return;
        }

        this.toggle.addEventListener('click', () => this.toggleChatbot());
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.input.addEventListener('input', () => {
            const hasText = this.input.value.trim().length > 0;
            this.sendBtn.disabled = !hasText;
        });

        document.addEventListener('click', (e) => {
            if (e.target.closest('.suggestion-chip')) {
                e.preventDefault();
                e.stopPropagation();

                const chip = e.target.closest('.suggestion-chip');
                const message = chip.dataset.message || chip.textContent.trim();

                if (message) {
                    this.clearSuggestions();
                    this.input.value = message;
                    this.sendBtn.disabled = false;
                    setTimeout(() => this.sendMessage(), 100);
                }
            }
        });

        if (this.minimizeBtn) {
            this.minimizeBtn.addEventListener('click', () => this.toggleMinimize());
        }
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.closeChatbot());
        }
    }

    toggleChatbot() {
        if (this.isOpen) {
            this.closeChatbot();
        } else {
            this.openChatbot();
        }
    }

    openChatbot() {
        this.widget.classList.add('show');
        this.widget.classList.remove('minimized');
        this.isOpen = true;
        this.isMinimized = false;

        setTimeout(() => {
            if (this.input) this.input.focus();
        }, 100);

        this.saveToStorage();
    }

    closeChatbot() {
        this.widget.classList.remove('show');
        this.isOpen = false;
        this.isMinimized = false;
        this.saveToStorage();
    }

    toggleMinimize() {
        if (this.isMinimized) {
            this.widget.classList.remove('minimized');
            this.isMinimized = false;
            setTimeout(() => {
                if (this.input) this.input.focus();
            }, 100);
        } else {
            this.widget.classList.add('minimized');
            this.isMinimized = true;
        }
        this.saveToStorage();
    }

    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;

        this.messageHistory.push({ type: 'user', content: message, timestamp: new Date() });

        this.input.value = '';
        this.sendBtn.disabled = true;
        this.clearSuggestions();

        this.addMessage(message, 'user');
        this.showTyping();

        try {
            const response = await fetch('/chatbot/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            const data = await response.json();
            this.hideTyping();

            if (response.ok) {
                this.sessionId = data.session_id;

                this.messageHistory.push({
                    type: 'bot',
                    content: data.response,
                    confidence: data.confidence,
                    ai_powered: data.ai_powered,
                    local_ai: data.local_ai,
                    timestamp: new Date()
                });

                // Add bot message with typing animation and AI indicators
                this.addBotMessageWithTyping(data.response, data, () => {
                    // Show AI status if available
                    if (data.ai_powered) {
                        this.addAIStatusIndicator(data);
                    }

                    // Show suggestions
                    if (data.suggestions && data.suggestions.length > 0) {
                        setTimeout(() => {
                            this.showSuggestions(data.suggestions);
                        }, 500);
                    }

                    // Show related resources
                    if (data.matched_resources && data.matched_resources.length > 0) {
                        setTimeout(() => {
                            this.addRelatedResourceCards(data.matched_resources);
                        }, 1000);
                    }
                });

            } else {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
                console.error('Intelligent Chatbot API error:', data);
            }
        } catch (error) {
            console.error('Intelligent Chatbot error:', error);
            this.hideTyping();
            this.addMessage('Sorry, I\'m having trouble connecting. Please check your internet connection and try again.', 'bot');
        }

        this.saveToStorage();
    }

    addMessage(text, sender, data = {}, saveToStorage = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;

        if (sender === 'bot' && data.confidence) {
            messageDiv.classList.add(`confidence-${data.confidence}`);
        }

        if (data.system_message) {
            messageDiv.classList.add('system-message');
        }

        if (data.restored) {
            messageDiv.classList.add('restored-message');
        }

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ?
            '<i class="fas fa-user"></i>' :
            '<i class="fas fa-robot"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';

        const p = document.createElement('p');
        if (text.includes('<br>') || text.includes('<strong>') || text.includes('<em>')) {
            p.innerHTML = text;
        } else {
            p.style.whiteSpace = 'pre-wrap';
            p.textContent = text;
        }
        content.appendChild(p);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);

        this.messages.appendChild(messageDiv);
        this.scrollToBottom();

        if (saveToStorage) {
            this.saveToStorage();
        }
    }

    addBotMessageWithTyping(text, data = {}, onComplete = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message bot-message`;

        if (data.confidence) {
            messageDiv.classList.add(`confidence-${data.confidence}`);
        }

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';

        const p = document.createElement('p');
        p.className = 'typing-text';
        content.appendChild(p);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        this.messages.appendChild(messageDiv);
        this.scrollToBottom();

        // Start typing animation with callback
        this.typeText(p, text, onComplete);
    }

    typeText(element, text, onComplete) {
        element.classList.add('typing');
        element.innerHTML = '';

        let index = 0;
        const speed = 20; // Faster typing for better UX

        const typeChar = () => {
            if (index < text.length) {
                const char = text.charAt(index);

                if (text.substr(index, 4) === '<br>') {
                    element.innerHTML += '<br>';
                    index += 4;
                } else if (text.substr(index, 8) === '<strong>') {
                    element.innerHTML += '<strong>';
                    index += 8;
                } else if (text.substr(index, 9) === '</strong>') {
                    element.innerHTML += '</strong>';
                    index += 9;
                } else if (text.substr(index, 4) === '<em>') {
                    element.innerHTML += '<em>';
                    index += 4;
                } else if (text.substr(index, 5) === '</em>') {
                    element.innerHTML += '</em>';
                    index += 5;
                } else {
                    element.innerHTML += char;
                    index++;
                }

                this.scrollToBottom();
                setTimeout(typeChar, speed);
            } else {
                element.classList.remove('typing');
                if (onComplete) onComplete();
            }
        };

        typeChar();
    }

    addRelatedResourceCards(resources) {
        if (!resources || resources.length === 0) return;

        // Filter out resources that don't have good relevance
        const relevantResources = resources.filter(resource =>
            resource.title && resource.description &&
            resource.title.length > 0 && resource.description.length > 0
        );

        if (relevantResources.length === 0) return;

        const resourceDiv = document.createElement('div');
        resourceDiv.className = 'chatbot-message bot-message';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';

        const header = document.createElement('p');
        header.innerHTML = '<strong>🔗 Related Resources:</strong>';
        header.style.marginBottom = '10px';
        content.appendChild(header);

        const cardsContainer = document.createElement('div');
        cardsContainer.className = 'related-resources-container';
        cardsContainer.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 8px;
        `;

        relevantResources.slice(0, 3).forEach((resource, index) => {
            const card = document.createElement('div');
            card.className = 'related-resource-card';
            card.style.cssText = `
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                animation: fadeInUp 0.3s ease ${index * 0.1}s both;
            `;

            const typeIcons = {
                'technology': '⚙️',
                'publication': '📄',
                'event': '📅',
                'training': '🎓',
                'webinar': '💻',
                'news': '📰',
                'policy': '📜',
                'project': '📊',
                'product': '🛠️',
                'media': '🎥',
                'forum': '💬',
                'cmi': '🏢',
                'faq': '❓',
                'commodity': '🌾',
                'category': '📚'
            };

            const icon = typeIcons[resource.type] || '📋';
            const truncatedDesc = resource.description.length > 100
                ? resource.description.substring(0, 100) + '...'
                : resource.description;

            card.innerHTML = `
                <div style="display: flex; align-items: flex-start; gap: 8px;">
                    <span style="font-size: 1.2em; flex-shrink: 0;">${icon}</span>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #2d3748; margin-bottom: 4px; font-size: 0.9em;">${resource.title}</div>
                        <div style="color: #666; font-size: 0.8em; line-height: 1.3;">${truncatedDesc}</div>
                        <div style="color: #999; font-size: 0.7em; margin-top: 4px; text-transform: capitalize;">
                            ${resource.type}${resource.resource_type ? ` • ${resource.resource_type}` : ''}
                        </div>
                    </div>
                </div>
            `;

            // Add hover effects
            card.addEventListener('mouseenter', () => {
                card.style.backgroundColor = '#e3f2fd';
                card.style.borderColor = '#1976d2';
                card.style.transform = 'translateY(-1px)';
                card.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.backgroundColor = '#f8f9fa';
                card.style.borderColor = '#e9ecef';
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = 'none';
            });

            // When clicked, make it a new chatbot response
            card.addEventListener('click', () => {
                // Create a detailed response for the clicked resource
                let detailedResponse = `**${resource.title}**\n\n${resource.description}`;

                // Add type-specific information
                if (resource.type === 'faq') {
                    detailedResponse = `❓ **FAQ: ${resource.title}**\n\n${resource.description}`;
                } else if (resource.type === 'forum') {
                    detailedResponse += `\n\n💬 **Forum Discussion**`;
                    if (resource.author) {
                        detailedResponse += `\n👤 **Author:** ${resource.author}`;
                    }
                } else if (resource.type === 'cmi') {
                    detailedResponse = `🏢 **CMI: ${resource.title}**\n\n${resource.description}`;
                    if (resource.location) {
                        detailedResponse += `\n\n📍 **Location:** ${resource.location}`;
                    }
                    if (resource.contact) {
                        detailedResponse += `\n📞 **Contact:** ${resource.contact}`;
                    }
                } else if (resource.type === 'resource') {
                    const typeLabels = {
                        'event': 'Event 📅',
                        'technology': 'Technology ⚙️',
                        'publication': 'Publication 📄',
                        'training': 'Training 🎓',
                        'news': 'News 📰',
                        'policy': 'Policy 📜',
                        'project': 'Project 📊',
                        'product': 'Product 🛠️',
                        'media': 'Media 🎥'
                    };
                    const resourceType = typeLabels[resource.resource_type] || resource.resource_type;
                    detailedResponse += `\n\n📋 **Type:** ${resourceType}`;
                } else if (resource.type === 'commodity') {
                    detailedResponse = `🌾 **Commodity: ${resource.title}**\n\n${resource.description}`;
                }

                // Add link if available
                if (resource.url && resource.url !== '#') {
                    detailedResponse += `\n\n🔗 [View Full Details](${resource.url})`;
                }

                // Add as new bot message with AI indicators
                this.addBotMessageWithTyping(detailedResponse, {
                    confidence: 'high',
                    ai_powered: true,
                    local_ai: true
                }, () => {
                    this.addAIStatusIndicator({
                        ai_powered: true,
                        local_ai: true,
                        intent_detected: true
                    });
                });

                // Clear suggestions and scroll to bottom
                this.clearSuggestions();
            });

            cardsContainer.appendChild(card);
        });

        content.appendChild(cardsContainer);
        resourceDiv.appendChild(avatar);
        resourceDiv.appendChild(content);

        this.messages.appendChild(resourceDiv);
        this.scrollToBottom();
    }

    showSuggestions(suggestions) {
        this.clearSuggestions();

        if (!suggestions || suggestions.length === 0) return;

        suggestions.forEach((suggestion, index) => {
            const chip = document.createElement('div');
            chip.className = 'suggestion-chip';
            chip.textContent = suggestion;
            chip.dataset.message = suggestion;
            chip.style.cursor = 'pointer';
            chip.style.animationDelay = `${index * 0.1}s`;

            // Add AI intelligence indicator to suggestions
            chip.title = 'AI-powered suggestion - Click to use';

            this.suggestions.appendChild(chip);
        });
    }

    clearSuggestions() {
        if (this.suggestions) {
            this.suggestions.innerHTML = '';
        }
    }

    showTyping() {
        if (this.typing) {
            // Clear any existing content
            this.typing.innerHTML = '';

            // Create proper structure matching bot messages
            const avatar = document.createElement('div');
            avatar.className = 'typing-avatar';
            avatar.innerHTML = '<i class="fas fa-robot"></i>';

            const content = document.createElement('div');
            content.className = 'typing-content';

            // Add typing dots
            for (let i = 0; i < 3; i++) {
                const dot = document.createElement('span');
                content.appendChild(dot);
            }

            this.typing.appendChild(avatar);
            this.typing.appendChild(content);
            this.typing.style.display = 'flex';

            this.scrollToBottom();
        }
    }

    hideTyping() {
        if (this.typing) {
            this.typing.style.display = 'none';
            this.typing.innerHTML = ''; 
        }
    }

    scrollToBottom() {
        if (this.messages) {
            this.messages.scrollTop = this.messages.scrollHeight;
        }
    }

    getCSRFToken() {
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenInput) return tokenInput.value;

        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) return metaToken.getAttribute('content');

        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }

        console.warn('CSRF token not found');
        return '';
    }

    saveToStorage() {
        try {
            const state = {
                isOpen: this.isOpen,
                isMinimized: this.isMinimized,
                sessionId: this.sessionId,
                sessionExpiresAt: this.sessionExpiresAt?.toISOString(),
                sessionCreatedAt: this.sessionCreatedAt?.toISOString(),
                messageHistory: this.messageHistory.slice(-10),
                aiEnabled: this.aiEnabled,
                persistentSession: true
            };
            localStorage.setItem('chatbot-state', JSON.stringify(state));
        } catch (e) {
            console.warn('Could not save chatbot state:', e);
        }
    }

    loadFromStorage() {
        try {
            const saved = this.getStoredState();
            if (saved) {
                this.sessionId = saved.sessionId;
                if (saved.sessionExpiresAt) {
                    this.sessionExpiresAt = new Date(saved.sessionExpiresAt);
                }
                if (saved.sessionCreatedAt) {
                    this.sessionCreatedAt = new Date(saved.sessionCreatedAt);
                }
                this.messageHistory = saved.messageHistory || [];
                this.aiEnabled = saved.aiEnabled !== false;

                if (saved.isOpen) {
                    this.openChatbot();
                    if (saved.isMinimized) {
                        this.toggleMinimize();
                    }
                }
            }
        } catch (e) {
            console.warn('Could not load chatbot state:', e);
        }
    }
}

// Initialize the intelligent chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('chatbot-container')) {
        try {
            window.chatbot = new IntelligentChatbot();
            console.log('🤖 Intelligent Chatbot initialized successfully with local AI capabilities');

            setTimeout(() => {
                fetch('/chatbot/debug-ai-status/')
                    .then(response => response.json())
                    .then(data => {
                        console.log('🧠 AI Status:', data);
                        if (data.ai_models_loaded) {
                            console.log('✅ Local AI models are active and running');
                        } else {
                            console.log('⚠️ AI models not loaded, using fallback processing');
                        }
                    })
                    .catch(e => console.log('Could not fetch AI status:', e));
            }, 1000);

        } catch (e) {
            console.error('Failed to initialize intelligent chatbot:', e);
        }
    }
});