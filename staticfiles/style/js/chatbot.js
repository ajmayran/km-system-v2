class Chatbot {
    constructor() {
        this.sessionId = null;
        this.isOpen = false;
        this.isMinimized = false;
        this.initializeElements();
        this.bindEvents();
        this.loadFromStorage();
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

    bindEvents() {
        if (!this.toggle || !this.sendBtn || !this.input) return;

        // Toggle chatbot
        this.toggle.addEventListener('click', () => this.toggleChatbot());

        // Send message
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault(); // Prevent form submission
                this.sendMessage();
            }
        });

        // Input validation
        this.input.addEventListener('input', () => {
            this.sendBtn.disabled = !this.input.value.trim();
        });

        // Suggestions - Fixed click handling
        if (this.suggestions) {
            this.suggestions.addEventListener('click', (e) => {
                if (e.target.classList.contains('suggestion-chip')) {
                    e.preventDefault();
                    e.stopPropagation();

                    const message = e.target.dataset.message;
                    if (message) {
                        this.input.value = message;
                        // Clear suggestions immediately when clicked
                        this.clearSuggestions();
                        this.sendMessage();
                    }
                }
            });
        }

        // Window controls
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
        if (this.input) this.input.focus();
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
            if (this.input) this.input.focus();
        } else {
            this.widget.classList.add('minimized');
            this.isMinimized = true;
        }
        this.saveToStorage();
    }

    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;

        // Clear input and suggestions immediately
        this.input.value = '';
        this.sendBtn.disabled = true;
        this.clearSuggestions(); // Clear before sending

        // Add user message
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
                const cleanResponse = this.handleRTFContent(data.response);
                this.addMessage(cleanResponse, 'bot', data);

                // Show new suggestions
                if (data.suggestions && data.suggestions.length > 0) {
                    this.showSuggestions(data.suggestions);
                }

                // Add matched resources
                if (data.matched_resources && data.matched_resources.length > 0) {
                    this.addResourceLinks(data.matched_resources);
                }
            } else {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }
        } catch (error) {
            console.error('Chatbot error:', error);
            this.hideTyping();
            this.addMessage('Sorry, I\'m having trouble connecting. Please try again later.', 'bot');
        }

        this.saveToStorage();
    }

    addMessage(text, sender, data = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;

        // Add confidence class if available
        if (data.confidence) {
            messageDiv.classList.add(`confidence-${data.confidence}`);
        }

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';

        const p = document.createElement('p');
        p.style.whiteSpace = 'pre-wrap';

        const cleanText = this.stripRTF(text);
        p.textContent = cleanText;

        content.appendChild(p);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);

        this.messages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    stripRTF(text) {
        // Remove RTF formatting tags
        if (!text) return '';
        return text
            .replace(/<\/?(h1|h2|h3|h4|h5|h6|p|div|span|strong|em|b|i|u)[^>]*>/gi, '')
            .replace(/\{\\[^}]+\}/g, '')
            .replace(/\\[a-z]+\s?/g, '')
            .replace(/\\cf\d+/g, '')
            .replace(/\\highlight\d+/g, '')
            .replace(/\s+/g, ' ')
            .replace(/&nbsp;/g, ' ')
            .replace(/<br\s*\/?>/gi, '\n')
            .trim();
    }

    handleRTFContent(text) {
        if (text.startsWith('{\\rtf1') || text.includes('\\par') || text.includes('\\pard')) {
            return this.stripRTF(text);
        }

        if (text.includes('<') && text.includes('>')) {
            return this.stripHTML(text);
        }   

        return text;
    }

    stripHTML(text) {
        const div = document.createElement('div');
        div.innerHTML = text;
        return div.textContent || div.innerText || '';
    } 

    addResourceLinks(resources) {
        const resourceDiv = document.createElement('div');
        resourceDiv.className = 'chatbot-message bot-message';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';

        const p = document.createElement('p');
        p.textContent = 'Here are some related resources:';
        content.appendChild(p);

        resources.forEach(resource => {
            const link = document.createElement('a');
            link.href = resource.url;
            link.className = 'resource-link';
            link.style.display = 'block';
            link.style.marginTop = '8px';
            link.style.padding = '6px 12px';
            link.style.background = 'rgba(44, 110, 73, 0.1)';
            link.style.color = '#2c6e49';
            link.style.textDecoration = 'none';
            link.style.borderRadius = '8px';
            link.style.fontSize = '12px';
            link.style.border = '1px solid rgba(44, 110, 73, 0.2)';
            link.textContent = `📄 ${resource.title}`;
            link.target = '_blank';
            content.appendChild(link);
        });

        resourceDiv.appendChild(avatar);
        resourceDiv.appendChild(content);

        this.messages.appendChild(resourceDiv);
        this.scrollToBottom();
    }

    showSuggestions(suggestions) {
        this.clearSuggestions(); // Clear existing suggestions first

        if (!suggestions || suggestions.length === 0) return;

        suggestions.forEach(suggestion => {
            const chip = document.createElement('div');
            chip.className = 'suggestion-chip';
            chip.textContent = suggestion;
            chip.dataset.message = suggestion;
            chip.style.cursor = 'pointer'; // Make it obvious it's clickable
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
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (token) return token.value;

        // Try to get from meta tag
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) return metaToken.getAttribute('content');

        // Try to get from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }

        return '';
    }

    saveToStorage() {
        try {
            const state = {
                isOpen: this.isOpen,
                isMinimized: this.isMinimized,
                sessionId: this.sessionId
            };
            localStorage.setItem('chatbot-state', JSON.stringify(state));
        } catch (e) {
            console.warn('Could not save chatbot state to localStorage:', e);
        }
    }

    loadFromStorage() {
        try {
            const saved = localStorage.getItem('chatbot-state');
            if (saved) {
                const state = JSON.parse(saved);
                this.sessionId = state.sessionId;

                if (state.isOpen) {
                    this.openChatbot();
                    if (state.isMinimized) {
                        this.toggleMinimize();
                    }
                }
            }
        } catch (e) {
            console.warn('Could not load chatbot state from localStorage:', e);
        }
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    // Only initialize if chatbot container exists
    if (document.getElementById('chatbot-container')) {
        try {
            window.chatbot = new Chatbot();
        } catch (e) {
            console.error('Failed to initialize chatbot:', e);
        }
    }
});