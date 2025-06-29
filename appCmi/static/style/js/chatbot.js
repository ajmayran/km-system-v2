class Chatbot {
    constructor() {
        this.sessionId = null;
        this.isOpen = false;
        this.isMinimized = false;
        this.messageHistory = [];
        this.initializeElements();
        this.bindEvents();
        this.loadFromStorage();
        this.addWelcomeMessage();
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

    addWelcomeMessage() {
        const existingBotMessages = this.messages.querySelectorAll('.bot-message');
        if (existingBotMessages.length === 1) {
            const welcomeMessage = existingBotMessages[0];
            const messageContent = welcomeMessage.querySelector('.message-content p');
            if (messageContent) {
                messageContent.innerHTML = `
                    👋 Hello! I'm your AANR Knowledge Assistant.<br><br>
                    I can help you with:<br>
                    🌾 Agriculture & Farming<br>
                    🐟 Aquatic Resources<br>
                    🌲 Natural Resources<br><br>
                    What would you like to know?
                `;
            }
        }
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
                    timestamp: new Date()
                });

                // Add bot message with typing animation
                this.addBotMessageWithTyping(data.response, data, () => {
                    // After typing is complete, show other elements
                    
                    // Show suggestions first
                    if (data.suggestions && data.suggestions.length > 0) {
                        setTimeout(() => {
                            this.showSuggestions(data.suggestions);
                        }, 500);
                    }

                    // Show related resources as clickable cards (not links)
                    if (data.matched_resources && data.matched_resources.length > 0) {
                        setTimeout(() => {
                            this.addRelatedResourceCards(data.matched_resources);
                        }, 1000);
                    }
                });

            } else {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
                console.error('Chatbot API error:', data);
            }
        } catch (error) {
            console.error('Chatbot error:', error);
            this.hideTyping();
            this.addMessage('Sorry, I\'m having trouble connecting. Please check your internet connection and try again.', 'bot');
        }

        this.saveToStorage();
    }

    
    addMessage(text, sender, data = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;

        if (sender === 'bot' && data.confidence) {
            messageDiv.classList.add(`confidence-${data.confidence}`);
        }

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ?
            '<i class="fas fa-user"></i>' :
            '<i class="fas fa-robot"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';

        const p = document.createElement('p');
        if (text.includes('<br>') || text.includes('<strong>')) {
            p.innerHTML = text;
        } else {
            p.style.whiteSpace = 'pre-wrap';
            p.textContent = text;
        }
        content.appendChild(p);
        
        // REMOVED: NLP scores section - no more technical details
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);

        this.messages.appendChild(messageDiv);
        this.scrollToBottom();
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

    // Updated typing function to accept callback
    typeText(element, text, onComplete) {
        element.classList.add('typing');
        element.innerHTML = '';
        
        let index = 0;
        const speed = 30; // Typing speed in milliseconds

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

    // NEW: Typing animation function
    typeText(element, text, onComplete) {
        element.classList.add('typing');
        element.innerHTML = '';
        
        let index = 0;
        const speed = 30; // Typing speed in milliseconds

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
                'faq': '❓'
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
                    </div>
                </div>
            `;

            // Add hover effects
            card.addEventListener('mouseenter', () => {
                card.style.backgroundColor = '#e3f2fd';
                card.style.borderColor = '#1976d2';
                card.style.transform = 'translateY(-1px)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.backgroundColor = '#f8f9fa';
                card.style.borderColor = '#e9ecef';
                card.style.transform = 'translateY(0)';
            });

            // When clicked, make it a new chatbot response
            card.addEventListener('click', () => {
                // Create a detailed response for the clicked resource
                let detailedResponse = `**${resource.title}**\n\n${resource.description}`;
                
                // Add type-specific information
                if (resource.type === 'faq') {
                    detailedResponse = `**${resource.title}**\n\n${resource.description}`;
                } else if (resource.type === 'forum') {
                    detailedResponse += `\n\n💬 **Forum Discussion**`;
                    if (resource.author) {
                        detailedResponse += `\n👤 **Author:** ${resource.author}`;
                    }
                } else if (resource.type === 'cmi') {
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
                }

                // Add link if available
                if (resource.url && resource.url !== '#') {
                    detailedResponse += `\n\n🔗 [View Full Details](${resource.url})`;
                }

                // Add as new bot message
                this.addMessage(detailedResponse, 'bot', { confidence: 'high' });
                
                // Clear suggestions and scroll to bottom
                this.clearSuggestions();
                this.scrollToBottom();
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
            this.typing.style.display = 'flex';
            this.scrollToBottom();
        }
    }

    hideTyping() {
        if (this.typing) {
            this.typing.style.display = 'none';
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
                messageHistory: this.messageHistory.slice(-10)
            };
            localStorage.setItem('chatbot-state', JSON.stringify(state));
        } catch (e) {
            console.warn('Could not save chatbot state:', e);
        }
    }

    loadFromStorage() {
        try {
            const saved = localStorage.getItem('chatbot-state');
            if (saved) {
                const state = JSON.parse(saved);
                this.sessionId = state.sessionId;
                this.messageHistory = state.messageHistory || [];

                if (state.isOpen) {
                    this.openChatbot();
                    if (state.isMinimized) {
                        this.toggleMinimize();
                    }
                }
            }
        } catch (e) {
            console.warn('Could not load chatbot state:', e);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('chatbot-container')) {
        try {
            window.chatbot = new Chatbot();
            console.log('Chatbot initialized successfully with typing animation');
        } catch (e) {
            console.error('Failed to initialize chatbot:', e);
        }
    }
});