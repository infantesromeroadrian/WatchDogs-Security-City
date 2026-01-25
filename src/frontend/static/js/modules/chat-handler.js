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
        console.log('🔍 DEBUG sendMessage:');
        console.log('   - isMultiFrameAnalysis:', this.apiClient.isMultiFrameAnalysis);
        console.log('   - currentROI:', this.apiClient.currentROI ? JSON.stringify(this.apiClient.currentROI) : 'null');
        console.log('   - currentFrame exists:', !!this.apiClient.currentFrame);
        console.log('   - window.roiSelector.getROI():', window.roiSelector?.getROI() ? JSON.stringify(window.roiSelector.getROI()) : 'null');
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear input
        this.chatInput.value = '';
        
        // Build context based on analysis type
        // NOTE: buildSingleFrameContext is now async due to ROI cropping
        // Use CURRENT ROI from selector (not the stored one from analysis time)
        // This allows user to draw a new ROI after analysis and query about that specific region
        const currentROI = window.roiSelector?.getROI() || this.apiClient.currentROI;
        console.log('   - Using ROI for chat:', currentROI ? JSON.stringify(currentROI) : 'null (full frame)');
        
        const context = (this.apiClient.isMultiFrameAnalysis && this.apiClient.frameCollection)
            ? this.buildMultiFrameContext(message)
            : await this.buildSingleFrameContext(message, currentROI);
        
        try {
            // Show loading in chat
            const loadingId = this.addMessage('assistant', '⏳ Pensando...');
            
            // Send request
            const response = await fetch(`${this.baseURL}/chat-query`, {
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
        // Build context string with analysis results and chat history
        let contextString = '';
        
        // Add analysis results if available
        if (this.apiClient.lastResults) {
            contextString += `Resultados del análisis multi-frame previo:\n${JSON.stringify(this.apiClient.lastResults, null, 2)}\n\n`;
        }
        
        // Add chat history if available
        if (this.chatHistory.length > 0) {
            contextString += `Historial de conversación:\n`;
            this.chatHistory.forEach(msg => {
                contextString += `${msg.role}: ${msg.content}\n`;
            });
            contextString += '\n';
        }
        
        return {
            frames: this.apiClient.frameCollection.map((f, idx) => ({
                frame: f.frame,
                description: f.description || `Frame ${idx + 1} - ${new Date(f.timestamp).toLocaleTimeString()}`
            })),
            message: userMessage,
            context: contextString
        };
    }
    
    async buildSingleFrameContext(userMessage, roi = null) {
        // Build context string that includes user message, analysis results, and chat history
        let contextString = `Pregunta del usuario: ${userMessage}\n\n`;
        
        // Add analysis results if available
        if (this.apiClient.lastResults) {
            contextString += `Resultados del análisis previo:\n${JSON.stringify(this.apiClient.lastResults, null, 2)}\n\n`;
        }
        
        // Add chat history if available
        if (this.chatHistory.length > 0) {
            contextString += `Historial de conversación:\n`;
            this.chatHistory.forEach(msg => {
                contextString += `${msg.role}: ${msg.content}\n`;
            });
            contextString += '\n';
        }
        
        // DEBUG: Log the frame type and value
        const frameValue = this.apiClient.currentFrame;
        console.log('🔍 DEBUG buildSingleFrameContext:');
        console.log('   - currentFrame type:', typeof frameValue);
        console.log('   - currentFrame is string:', typeof frameValue === 'string');
        console.log('   - currentFrame is null:', frameValue === null);
        console.log('   - currentFrame length:', frameValue ? (typeof frameValue === 'string' ? frameValue.length : 'N/A (not string)') : 0);
        console.log('   - ROI provided:', roi ? JSON.stringify(roi) : 'null');
        
        // DEFENSIVE: Validate frame is a string before sending
        if (!frameValue || typeof frameValue !== 'string') {
            console.error('❌ CRITICAL: currentFrame is not a valid string!', {
                type: typeof frameValue,
                value: frameValue ? (typeof frameValue === 'object' ? JSON.stringify(frameValue).substring(0, 100) : frameValue) : 'null/undefined'
            });
            throw new Error('No hay frame capturado válido. Por favor, captura un frame e intenta de nuevo.');
        }
        
        let payload = {
            frame: frameValue,
            context: contextString
        };
        
        // If ROI is selected, crop the frame to ROI
        // NOTE: cropROI returns a Promise, so we must await it!
        if (roi && this.apiClient.currentFrame && window.imageUtils) {
            console.log('📐 ROI detected, cropping frame to ROI...');
            try {
                const croppedFrame = await window.imageUtils.cropROI(this.apiClient.currentFrame, roi);
                if (croppedFrame) {
                    console.log('✅ Frame cropped to ROI successfully');
                    console.log('   - Original frame length:', this.apiClient.currentFrame.length);
                    console.log('   - Cropped frame length:', croppedFrame.length);
                    payload.frame = croppedFrame;
                } else {
                    console.warn('⚠️ cropROI returned null, using full frame');
                }
            } catch (cropError) {
                console.error('❌ Error cropping ROI, using full frame:', cropError);
            }
        } else {
            console.log('📐 No ROI selected, using full frame');
        }
        
        return payload;
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
