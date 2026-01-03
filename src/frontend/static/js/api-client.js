/**
 * API Client
 * Handles communication with backend Flask API
 */

class APIClient {
    constructor() {
        // Dynamic base URL (works in Docker and local)
        this.baseURL = window.location.origin + '/api';
        this.timeout = 60000; // 60 seconds timeout for analysis
        
        // DOM elements
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.analysisSection = document.getElementById('analysisSection');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.textResults = document.getElementById('textResults');
        this.jsonResults = document.getElementById('jsonResults');
        this.previewCanvas = document.getElementById('previewCanvas');
        this.copyJsonBtn = document.getElementById('copyJsonBtn');
        this.downloadReportBtn = document.getElementById('downloadReportBtn');
        this.newAnalysisBtn = document.getElementById('newAnalysisBtn');
        
        // Chat elements
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendChat = document.getElementById('sendChat');
        
        // State
        this.lastResults = null;
        this.chatHistory = [];
        this.currentFrame = null;
        this.frameCollection = null;  // For multi-frame chat
        this.isMultiFrameAnalysis = false;  // Flag to know if last analysis was multi-frame
        
        this.init();
    }
    
    init() {
        // Check backend connection on load
        this.checkBackendConnection();
        
        // DEFENSIVE CHECK: Verify critical DOM elements
        console.log('🔍 DOM Elements Check:');
        console.log('   - sendChat:', !!this.sendChat, this.sendChat);
        console.log('   - chatInput:', !!this.chatInput, this.chatInput);
        console.log('   - chatMessages:', !!this.chatMessages, this.chatMessages);
        
        if (!this.sendChat) {
            console.error('❌ CRITICAL: sendChat button not found! Check HTML id="sendChat"');
        }
        if (!this.chatInput) {
            console.error('❌ CRITICAL: chatInput not found! Check HTML id="chatInput"');
        }
        
        // Analyze button
        this.analyzeBtn.addEventListener('click', () => {
            this.analyzeFrame();
        });
        
        // Tab switching
        const tabs = document.querySelectorAll('.tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchTab(tab.dataset.tab);
            });
        });
        
        // Copy JSON button
        this.copyJsonBtn.addEventListener('click', () => {
            this.copyJSON();
        });
        
        // Download report button
        this.downloadReportBtn.addEventListener('click', () => {
            this.downloadReport();
        });
        
        // New analysis button
        this.newAnalysisBtn.addEventListener('click', () => {
            this.resetAnalysis();
        });
        
        // Chat functionality (DEFENSIVE)
        if (this.sendChat) {
            this.sendChat.addEventListener('click', () => {
                console.log('🖱️ Chat send button clicked');
                this.sendChatMessage();
            });
            console.log('✅ Chat send button listener attached');
        } else {
            console.error('❌ Cannot attach listener to sendChat - element not found');
        }
        
        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    console.log('⌨️ Enter pressed in chat input');
                    this.sendChatMessage();
                }
            });
            console.log('✅ Chat input keypress listener attached');
        } else {
            console.error('❌ Cannot attach listener to chatInput - element not found');
        }
    }
    
    async checkBackendConnection() {
        const statusElement = document.getElementById('connectionStatus');
        if (!statusElement) return;
        
        try {
            statusElement.textContent = '🔍 Verificando conexión...';
            statusElement.className = 'connection-status checking';
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(`${this.baseURL.replace('/api', '')}`, {
                method: 'GET',
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                statusElement.textContent = '✅ Conectado al backend';
                statusElement.className = 'connection-status connected';
                console.log('✅ Backend connection successful');
            } else {
                throw new Error('Backend responded with error');
            }
        } catch (error) {
            statusElement.textContent = '❌ Backend desconectado';
            statusElement.className = 'connection-status disconnected';
            console.error('❌ Backend connection failed:', error);
            
            // Retry after 10 seconds
            setTimeout(() => this.checkBackendConnection(), 10000);
        }
    }
    
    async analyzeFrame() {
        try {
            // Get captured frame from video player
            const frame = window.videoPlayer.getCapturedFrame();
            if (!frame) {
                alert('⚠️ Por favor captura un frame primero');
                return;
            }
            
            // Get ROI if selected
            const roi = window.roiSelector.getROI();
            
            // Show loading
            this.showLoading();
            
            console.log('🚀 Sending frame for analysis...');
            if (roi) {
                console.log('📐 ROI Details:', JSON.stringify(roi, null, 2));
                console.log(`   - Position: (${roi.x}, ${roi.y})`);
                console.log(`   - Size: ${roi.width} x ${roi.height}`);
            } else {
                console.log('📐 ROI: Full frame (no ROI selected)');
            }
            
            // Prepare request payload
            const payload = {
                frame: frame,
                roi: roi || null,
                context: ''  // Optional context can be added later
            };
            
            // Send request to backend with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            try {
                const response = await fetch(`${this.baseURL}/analyze-frame`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
            
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error || 'Analysis failed');
                }
                
                console.log('✅ Analysis complete');
                this.displayResults(data.results);
                
            } catch (error) {
                clearTimeout(timeoutId);
                
                if (error.name === 'AbortError') {
                    throw new Error('Timeout: El análisis tomó demasiado tiempo (>60s). Intenta con una región más pequeña.');
                }
                throw error;
            }
            
        } catch (error) {
            console.error('❌ Analysis error:', error);
            this.showError(error.message);
        }
    }
    
    showLoading() {
        this.analysisSection.style.display = 'block';
        this.loadingIndicator.style.display = 'block';
        this.resultsContainer.style.display = 'none';
        
        // Scroll to analysis section
        this.analysisSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    displayResults(results) {
        this.lastResults = results;
        this.currentFrame = window.videoPlayer.getCapturedFrame();
        this.currentROI = window.roiSelector.getROI();  // Store ROI for chat
        this.isMultiFrameAnalysis = false;  // Single frame analysis
        this.frameCollection = null;  // Clear multi-frame collection
        
        // Hide loading
        this.loadingIndicator.style.display = 'none';
        this.resultsContainer.style.display = 'block';
        
        // Display text report
        this.textResults.textContent = results.text || 'No text report available';
        
        // Display JSON report
        this.jsonResults.textContent = JSON.stringify(results.json, null, 2);
        
        // Display preview (captured frame with ROI)
        this.displayPreview();
        
        // Enable chat after analysis (DEFENSIVE CHECK)
        console.log('🔍 Activating chat controls...');
        console.log('   - sendChat button exists:', !!this.sendChat);
        console.log('   - chatInput exists:', !!this.chatInput);
        console.log('   - currentFrame exists:', !!this.currentFrame);
        
        if (this.sendChat) {
            this.sendChat.disabled = false;
            console.log('✅ Chat send button ENABLED');
        } else {
            console.error('❌ sendChat button NOT FOUND in DOM!');
        }
        
        if (this.chatInput) {
            this.chatInput.disabled = false;
            console.log('✅ Chat input ENABLED');
        } else {
            console.error('❌ chatInput NOT FOUND in DOM!');
        }
        
        this.chatHistory = [];  // Reset chat history for new analysis
        this.chatMessages.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">El análisis está completo. Puedes hacer preguntas sobre la imagen.</p>';
        
        console.log('📊 Results displayed and chat controls activated');
    }
    
    displayBatchResults(results, frameCollection) {
        console.log('📊 Displaying multi-frame batch results');
        this.lastResults = results;
        this.frameCollection = frameCollection;  // Store all frames
        this.isMultiFrameAnalysis = true;  // Flag for chat
        this.currentFrame = null;  // No single frame
        this.currentROI = null;
        
        // Hide loading
        this.loadingIndicator.style.display = 'none';
        this.resultsContainer.style.display = 'block';
        
        // Display text report
        this.textResults.textContent = results.summary || results.text || 'No text report available';
        
        // Display JSON report
        this.jsonResults.textContent = JSON.stringify(results, null, 2);
        
        // No preview for multi-frame (could show grid in future)
        const previewTab = document.querySelector('.tab[data-tab="preview"]');
        if (previewTab) {
            previewTab.style.display = 'none';  // Hide preview tab for multi-frame
        }
        
        // Enable chat after analysis (DEFENSIVE CHECK)
        console.log('🔍 Activating chat controls for MULTI-FRAME...');
        console.log(`   - ${frameCollection.length} frames in collection`);
        
        if (this.sendChat) {
            this.sendChat.disabled = false;
            console.log('✅ Chat send button ENABLED (multi-frame mode)');
        }
        
        if (this.chatInput) {
            this.chatInput.disabled = false;
            console.log('✅ Chat input ENABLED (multi-frame mode)');
        }
        
        this.chatHistory = [];
        this.chatMessages.innerHTML = `<p style="color: var(--text-secondary); text-align: center;">
            📊 Análisis multi-frame completo (${frameCollection.length} frames). 
            Puedes hacer preguntas sobre cualquier frame o todos en conjunto.
        </p>`;
        
        // Switch to text tab
        this.switchTab('text');
        
        console.log('📊 Multi-frame results displayed and chat activated');
    }
    
    displayPreview() {
        const frame = window.videoPlayer.getCapturedFrame();
        const roi = window.roiSelector.getROI();
        
        const img = new Image();
        img.onload = () => {
            this.previewCanvas.width = img.width;
            this.previewCanvas.height = img.height;
            
            const ctx = this.previewCanvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            
            // Draw ROI rectangle if exists
            if (roi) {
                ctx.strokeStyle = '#00ff00';
                ctx.lineWidth = 4;
                ctx.strokeRect(roi.x, roi.y, roi.width, roi.height);
                
                ctx.fillStyle = 'rgba(0, 255, 0, 0.1)';
                ctx.fillRect(roi.x, roi.y, roi.width, roi.height);
                
                // Add label
                ctx.fillStyle = '#00ff00';
                ctx.font = 'bold 20px Arial';
                ctx.fillText('ROI', roi.x + 10, roi.y + 30);
            }
        };
        img.src = frame;
    }
    
    showError(message) {
        this.loadingIndicator.style.display = 'none';
        this.resultsContainer.style.display = 'block';
        
        // Determine error type for better messaging
        let errorType = '❌ Error General';
        let suggestion = 'Por favor intenta nuevamente.';
        
        if (message.includes('NetworkError') || message.includes('Failed to fetch')) {
            errorType = '🌐 Error de Conexión';
            suggestion = 'Verifica que el backend esté ejecutándose (docker compose up).';
        } else if (message.includes('HTTP error')) {
            errorType = '🚫 Error del Servidor';
            suggestion = 'El backend respondió con un error. Revisa los logs de Docker.';
        } else if (message.includes('timeout')) {
            errorType = '⏱️ Timeout';
            suggestion = 'El análisis tomó demasiado tiempo. Intenta con una región más pequeña.';
        }
        
        this.textResults.textContent = `${errorType}\n\n${message}\n\n💡 Sugerencia: ${suggestion}\n\nRevisa la consola del navegador para más detalles.`;
        this.jsonResults.textContent = JSON.stringify({ 
            error: message,
            timestamp: new Date().toISOString(),
            errorType: errorType
        }, null, 2);
        
        // Switch to text tab to show error immediately
        this.switchTab('text');
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}Tab`).classList.add('active');
    }
    
    copyJSON() {
        if (!this.lastResults) return;
        
        const jsonText = JSON.stringify(this.lastResults.json, null, 2);
        navigator.clipboard.writeText(jsonText).then(() => {
            this.copyJsonBtn.textContent = '✅ Copiado';
            setTimeout(() => {
                this.copyJsonBtn.textContent = '📋 Copiar JSON';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
            alert('Error al copiar al portapapeles');
        });
    }
    
    downloadReport() {
        if (!this.lastResults) return;
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `watchdogs_analysis_${timestamp}.txt`;
        
        const blob = new Blob([this.lastResults.text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        
        URL.revokeObjectURL(url);
        console.log('💾 Report downloaded:', filename);
    }
    
    resetAnalysis() {
        this.analysisSection.style.display = 'none';
        this.lastResults = null;
        this.currentFrame = null;
        this.chatHistory = [];
        this.chatMessages.innerHTML = '';
        this.chatInput.value = '';
        this.sendChat.disabled = true;
        this.chatInput.disabled = true;
        window.roiSelector.clearROI();
        console.log('🔄 Analysis reset');
    }
    
    async sendChatMessage() {
        console.log('💬 sendChatMessage() called');
        console.log('   - chatInput value:', this.chatInput?.value);
        console.log('   - isMultiFrameAnalysis:', this.isMultiFrameAnalysis);
        console.log('   - frameCollection:', this.frameCollection?.length || 0);
        console.log('   - currentFrame exists:', !!this.currentFrame);
        console.log('   - sendChat disabled:', this.sendChat?.disabled);
        
        const message = this.chatInput.value.trim();
        if (!message) {
            console.warn('⚠️ Chat message is empty');
            return;
        }
        
        // Check if we have frames to analyze
        if (!this.currentFrame && !this.frameCollection) {
            console.error('❌ No frames available for chat');
            alert('⚠️ Debes realizar un análisis primero antes de usar el chat');
            return;
        }
        
        // Add user message to chat
        this.addMessageToChat('user', message);
        this.chatInput.value = '';
        this.sendChat.disabled = true;
        
        try {
            let payload;
            
            // MULTI-FRAME MODE
            if (this.isMultiFrameAnalysis && this.frameCollection) {
                console.log(`📊 Multi-frame chat mode: ${this.frameCollection.length} frames`);
                
                // Send all frames with the question
                payload = {
                    frames: this.frameCollection,  // Send all frames
                    message: message,
                    context: this.buildMultiFrameChatContext(message)
                };
                
            } else {
                // SINGLE-FRAME MODE (original logic)
                console.log('📸 Single-frame chat mode');
                
                // Get ROI-cropped frame if ROI exists
                let frameToSend = this.currentFrame;
                const roi = this.currentROI || window.roiSelector.getROI();
                
                if (roi) {
                    // Crop ROI from frame (async operation)
                    frameToSend = await this.cropROIFromFrame(this.currentFrame, roi);
                    console.log('✂️ Using ROI-cropped frame for chat:', roi);
                } else {
                    console.log('📐 Using full frame for chat (no ROI)');
                }
                
                // Prepare payload with context
                payload = {
                    frame: frameToSend,
                    context: this.buildChatContext(message, roi)
                };
            }
            
            // Send to backend with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            try {
                const response = await fetch(`${this.baseURL}/chat-query`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Chat query failed');
            }
            
                // Add assistant response
                this.addMessageToChat('assistant', data.response);
                
                // Update chat history
                this.chatHistory.push({
                    role: 'user',
                    content: message
                });
                this.chatHistory.push({
                    role: 'assistant',
                    content: data.response
                });
                
            } catch (error) {
                clearTimeout(timeoutId);
                
                if (error.name === 'AbortError') {
                    throw new Error('Timeout: El chat no respondió a tiempo. Intenta de nuevo.');
                }
                throw error;
            }
            
        } catch (error) {
            console.error('❌ Chat error:', error);
            
            let errorMessage = '❌ Error en el chat: ';
            if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                errorMessage += 'No se pudo conectar al backend. Verifica que Docker esté ejecutándose.';
            } else if (error.message.includes('timeout') || error.message.includes('Timeout')) {
                errorMessage += 'El backend no respondió a tiempo. Intenta de nuevo.';
            } else {
                errorMessage += error.message;
            }
            
            this.addMessageToChat('assistant', errorMessage);
        } finally {
            this.sendChat.disabled = false;
            this.chatInput.disabled = false;
            this.chatInput.focus();
        }
    }
    
    cropROIFromFrame(frameBase64, roi) {
        // Create image from base64
        const img = new Image();
        return new Promise((resolve) => {
            img.onload = () => {
                // Create canvas for cropping
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                // Set canvas size to ROI dimensions
                canvas.width = roi.width;
                canvas.height = roi.height;
                
                // Draw cropped region
                ctx.drawImage(
                    img,
                    roi.x, roi.y, roi.width, roi.height,  // Source region
                    0, 0, roi.width, roi.height           // Destination
                );
                
                // Convert to base64
                const croppedBase64 = canvas.toDataURL('image/png');
                resolve(croppedBase64);
            };
            img.src = frameBase64;
        });
    }
    
    buildMultiFrameChatContext(userMessage) {
        let context = `ANÁLISIS MULTI-FRAME: El usuario ha analizado ${this.frameCollection.length} frames y hace una pregunta.\n\n`;
        context += `Pregunta: ${userMessage}\n\n`;
        context += `IMPORTANTE: Recibirás ${this.frameCollection.length} imágenes. Analiza TODAS y responde la pregunta considerando información de todos los frames.\n\n`;
        
        if (this.lastResults) {
            context += 'CONTEXTO DEL ANÁLISIS PREVIO:\n';
            if (this.lastResults.summary) {
                context += `Resumen: ${this.lastResults.summary.substring(0, 500)}\n\n`;
            }
            if (this.lastResults.combined_geolocation) {
                context += `Geolocalización: ${JSON.stringify(this.lastResults.combined_geolocation).substring(0, 300)}\n\n`;
            }
        }
        
        if (this.chatHistory.length > 0) {
            context += 'HISTORIAL DE CONVERSACIÓN:\n';
            this.chatHistory.slice(-4).forEach(msg => {
                context += `${msg.role === 'user' ? 'Usuario' : 'Asistente'}: ${msg.content}\n`;
            });
            context += '\n';
        }
        
        context += 'INSTRUCCIONES:\n';
        context += '- Analiza TODAS las imágenes que recibes\n';
        context += '- Si preguntan "qué ves en cada frame", describe cada frame por separado\n';
        context += '- Si preguntan algo específico (color, objeto, texto), búscalo en TODOS los frames\n';
        context += '- Numera tus respuestas si describes múltiples frames: "Frame 1: ..., Frame 2: ..."\n';
        context += '- Sé específico y conciso\n';
        
        return context;
    }
    
    buildChatContext(userMessage, roi = null) {
        // Build context with previous analysis and chat history
        let context = `Pregunta específica del usuario: ${userMessage}\n\n`;
        
        // Add ROI context if exists
        if (roi) {
            context += `⚠️ IMPORTANTE: El usuario está preguntando sobre una REGIÓN ESPECÍFICA (ROI) de la imagen que fue seleccionada.\n`;
            context += `Coordenadas ROI: x=${roi.x}, y=${roi.y}, width=${roi.width}, height=${roi.height}\n`;
            context += `La imagen que recibes es SOLO esa región recortada. Responde específicamente sobre lo que ves en esa región.\n\n`;
        } else {
            context += `La imagen es el frame completo. Responde sobre toda la escena.\n\n`;
        }
        
        if (this.lastResults && this.lastResults.json) {
            context += 'CONTEXTO DEL ANÁLISIS PREVIO:\n';
            const vision = this.lastResults.json.vision?.analysis || this.lastResults.json.vision || 'N/A';
            const ocr = this.lastResults.json.ocr?.analysis || this.lastResults.json.ocr || 'N/A';
            const detection = this.lastResults.json.detection?.analysis || this.lastResults.json.detection || 'N/A';
            context += `Vision: ${typeof vision === 'string' ? vision.substring(0, 200) : JSON.stringify(vision).substring(0, 200)}\n`;
            context += `OCR: ${typeof ocr === 'string' ? ocr.substring(0, 200) : JSON.stringify(ocr).substring(0, 200)}\n`;
            context += `Detection: ${typeof detection === 'string' ? detection.substring(0, 200) : JSON.stringify(detection).substring(0, 200)}\n\n`;
        }
        
        if (this.chatHistory.length > 0) {
            context += 'HISTORIAL DE CONVERSACIÓN RECIENTE:\n';
            this.chatHistory.slice(-4).forEach(msg => {  // Last 4 messages
                context += `${msg.role === 'user' ? 'Usuario' : 'Asistente'}: ${msg.content}\n`;
            });
            context += '\n';
        }
        
        context += 'INSTRUCCIONES:\n';
        context += '- Responde DIRECTAMENTE a la pregunta del usuario de forma concisa y específica.\n';
        context += '- Si preguntan sobre un color, objeto o detalle específico, identifícalo claramente.\n';
        context += '- Si la pregunta es sobre algo en el ROI, enfócate SOLO en esa región.\n';
        context += '- Sé preciso y evita respuestas genéricas o largas descripciones de toda la escena.\n';
        
        return context;
    }
    
    addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const label = document.createElement('strong');
        label.textContent = role === 'user' ? '👤 Tú:' : '🤖 Agente:';
        
        const text = document.createElement('span');
        text.textContent = content;
        
        messageDiv.appendChild(label);
        messageDiv.appendChild(document.createElement('br'));
        messageDiv.appendChild(text);
        
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize API client when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.apiClient = new APIClient();
});

