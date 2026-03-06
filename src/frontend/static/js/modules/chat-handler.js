/**
 * Chat Handler Module
 * Handles chat functionality and context building for analysis results
 */

import { log } from './logger.js';

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
        if (!this.sendChat) log.error('sendChat button not found');
        if (!this.chatInput) log.error('chatInput not found');
        
        // Chat functionality
        this.sendChat?.addEventListener('click', () => this.sendMessage());
        this.chatInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        log.info('Chat handler initialized');
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        log.debug('Sending chat message:', message);
        log.debug('sendMessage state:', {
            isMultiFrameAnalysis: this.apiClient.isMultiFrameAnalysis,
            currentROI: this.apiClient.currentROI,
            currentFrameExists: !!this.apiClient.currentFrame,
            roiSelectorROI: window.roiSelector?.getROI() || null,
        });
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear input
        this.chatInput.value = '';
        
        // Build context based on analysis type
        // NOTE: buildSingleFrameContext is now async due to ROI cropping
        // Use CURRENT ROI from selector (not the stored one from analysis time)
        // This allows user to draw a new ROI after analysis and query about that specific region
        const currentROI = window.roiSelector?.getROI() || this.apiClient.currentROI;
        log.debug('Using ROI for chat:', currentROI || 'full frame');
        
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
            
            // Emit location events for any extracted coordinates
            if (data.extracted_locations && data.extracted_locations.length > 0) {
                data.extracted_locations.forEach(loc => {
                    window.dispatchEvent(new CustomEvent('watchdogs:location-found', {
                        detail: {
                            lat: loc.lat,
                            lon: loc.lon,
                            label: loc.label || `${loc.lat.toFixed(4)}, ${loc.lon.toFixed(4)}`,
                            confidence_radius: loc.confidence_radius_meters,
                            source: 'chat'
                        }
                    }));
                });
            }
            
            // Update chat history
            this.chatHistory.push({
                role: 'user',
                content: message
            }, {
                role: 'assistant',
                content: data.response
            });
            
        } catch (error) {
            log.error('Chat error:', error);
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
        // SESSION-BASED MODE with LangGraph MessagesState
        // The server maintains conversation history via LangGraph checkpointer.
        // We only send the user's message — no need to rebuild context client-side.
        // Image is stored server-side and not re-transmitted.
        if (this.apiClient.currentSessionId && !roi) {
            log.debug('Using LangGraph session chat (no image, no context rebuild)', {
                sessionId: this.apiClient.currentSessionId.slice(0, 8),
            });
            return {
                session_id: this.apiClient.currentSessionId,
                message: userMessage
            };
        }
        
        // LEGACY/ROI MODE: Build full context string for non-session chat
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
        
        // LEGACY/ROI MODE: Send full frame (needed when ROI changes between messages)
        const frameValue = this.apiClient.currentFrame;
        log.debug('buildSingleFrameContext (legacy mode):', {
            frameType: typeof frameValue,
            isString: typeof frameValue === 'string',
            frameLength: frameValue ? (typeof frameValue === 'string' ? frameValue.length : 'N/A') : 0,
            roi: roi || null,
            hasSessionId: !!this.apiClient.currentSessionId,
        });
        
        // DEFENSIVE: Validate frame is a string before sending
        if (!frameValue || typeof frameValue !== 'string') {
            log.error('CRITICAL: currentFrame is not a valid string!', {
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
            log.debug('ROI detected, cropping frame to ROI...');
            try {
                const croppedFrame = await window.imageUtils.cropROI(this.apiClient.currentFrame, roi);
                if (croppedFrame) {
                    log.debug('Frame cropped to ROI:', { original: this.apiClient.currentFrame.length, cropped: croppedFrame.length });
                    payload.frame = croppedFrame;
                } else {
                    log.warn('cropROI returned null, using full frame');
                }
            } catch (cropError) {
                log.error('Error cropping ROI, using full frame:', cropError);
            }
        } else {
            log.debug('No ROI selected, using full frame');
        }
        
        return payload;
    }
    
    addMessage(role, content) {
        const messageId = `msg-${Date.now()}-${Math.random()}`;
        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `chat-message ${role}-message`;
        
        const icon = role === 'user' ? '👤' : '🤖';
        
        // Build DOM safely — no innerHTML with user/LLM content (XSS prevention)
        const header = document.createElement('div');
        header.className = 'message-header';
        header.innerHTML = `<span class="message-icon">${icon}</span><span class="message-role">${role === 'user' ? 'Tú' : 'Asistente'}</span>`;
        
        const body = document.createElement('div');
        body.className = 'message-content';
        body.style.whiteSpace = 'pre-wrap';
        body.textContent = content;  // Safe: textContent never executes HTML
        
        messageDiv.appendChild(header);
        messageDiv.appendChild(body);
        
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
    
    reset() {
        this.chatHistory = [];
        this.chatMessages.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">El análisis está completo. Puedes hacer preguntas sobre la imagen.</p>';
    }
    
    enable() {
        if (this.sendChat) this.sendChat.disabled = false;
        if (this.chatInput) this.chatInput.disabled = false;
        log.info('Chat enabled');
    }
}
