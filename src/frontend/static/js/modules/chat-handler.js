/**
 * Chat Handler Module
 * Handles chat functionality and context building for analysis results
 */

export class ChatHandler {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.baseURL = apiClient.baseURL;
        this.chatHistory = [];
        
        // DOM elements
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendChat = document.getElementById('sendChat');
        
        this.init();
    }
    
    init() {
        // Verify critical DOM elements
        if (!this.sendChat) console.error('❌ sendChat button not found');
        if (!this.chatInput) console.error('❌ chatInput not found');
        
        // Chat functionality
        this.sendChat?.addEventListener('click', () => this.sendMessage());
        this.chatInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        console.log('✅ Chat handler initialized');
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        console.log('💬 Sending chat message:', message);
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear input
        this.chatInput.value = '';
        
        // Build context based on analysis type
        const context = (this.apiClient.isMultiFrameAnalysis && this.apiClient.frameCollection)
            ? this.buildMultiFrameContext(message)
            : this.buildSingleFrameContext(message, this.apiClient.currentROI);
        
        try {
            // Show loading in chat
            const loadingId = this.addMessage('assistant', '⏳ Pensando...');
            
            // Send request
            const response = await fetch(`${this.baseURL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(context)
            });
            
            // Remove loading message
            this.removeMessage(loadingId);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Chat failed');
            }
            
            // Add assistant response
            this.addMessage('assistant', data.response);
            
            // Update chat history
            this.chatHistory.push({
                role: 'user',
                content: message
            }, {
                role: 'assistant',
                content: data.response
            });
            
        } catch (error) {
            console.error('❌ Chat error:', error);
            this.addMessage('assistant', `⚠️ Error: ${error.message}. Por favor, intenta de nuevo.`);
        }
    }
    
    buildMultiFrameContext(userMessage) {
        return {
            frames: this.apiClient.frameCollection.map(f => ({
                frame: f.frame,
                timestamp: f.timestamp
            })),
            message: userMessage,
            analysis_results: this.apiClient.lastResults,
            chat_history: this.chatHistory
        };
    }
    
    buildSingleFrameContext(userMessage, roi = null) {
        let context = {
            frame: this.apiClient.currentFrame,
            message: userMessage,
            analysis_results: this.apiClient.lastResults,
            chat_history: this.chatHistory
        };
        
        // If ROI is selected, crop the frame to ROI
        if (roi && this.apiClient.currentFrame && window.imageUtils) {
            const croppedFrame = window.imageUtils.cropROI(this.apiClient.currentFrame, roi);
            if (croppedFrame) {
                context.frame = croppedFrame;
                context.roi = roi;
            }
        }
        
        return context;
    }
    
    addMessage(role, content) {
        const messageId = `msg-${Date.now()}-${Math.random()}`;
        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `chat-message ${role}-message`;
        
        const icon = role === 'user' ? '👤' : '🤖';
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-icon">${icon}</span>
                <span class="message-role">${role === 'user' ? 'Tú' : 'Asistente'}</span>
            </div>
            <div class="message-content">${this.formatMessage(content)}</div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        return messageId;
    }
    
    removeMessage(messageId) {
        const message = document.getElementById(messageId);
        if (message) {
            message.remove();
        }
    }
    
    formatMessage(content) {
        // Convert line breaks to <br>
        return content.replace(/\n/g, '<br>');
    }
    
    reset() {
        this.chatHistory = [];
        this.chatMessages.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">El análisis está completo. Puedes hacer preguntas sobre la imagen.</p>';
    }
    
    enable() {
        if (this.sendChat) this.sendChat.disabled = false;
        if (this.chatInput) this.chatInput.disabled = false;
        console.log('✅ Chat enabled');
    }
}
