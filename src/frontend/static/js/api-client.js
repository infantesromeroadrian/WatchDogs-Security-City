/**
 * API Client - Main Orchestrator (Refactored)
 * Coordinates communication with backend and delegates to specialized modules
 */

import { log } from './modules/logger.js';
import { ChatHandler } from './modules/chat-handler.js';
import { MapHandler } from './modules/map-handler.js';
import { UIManager } from './modules/ui-manager.js';
import { ImageUtils } from './modules/image-utils.js';

class APIClient {
    constructor() {
        // Dynamic base URL (works in Docker and local)
        this.baseURL = window.location.origin + '/api';
        this.timeout = 120000; // 2 minutes — generous for Groq cloud API with 7 agents
        
        // DOM elements
        this.analyzeBtn = document.getElementById('analyzeBtn');
        
        // State
        this.lastResults = null;
        this.chatHistory = [];
        this.currentFrame = null;
        this.currentROI = null;
        this.frameCollection = null;  // For multi-frame chat
        this.isMultiFrameAnalysis = false;  // Flag to know if last analysis was multi-frame
        
        // Initialize modules
        this.chatHandler = new ChatHandler(this);
        this.uiManager = new UIManager(this);
        this.imageUtils = new ImageUtils();
        this.mapHandler = new MapHandler();
        
        // Expose imageUtils globally for other modules
        window.imageUtils = this.imageUtils;
        
        this.init();
    }
    
    init() {
        // Check backend connection on load
        this.checkBackendConnection();
        
        // Init map (async, non-blocking)
        this.mapHandler.init();
        
        // Analyze button
        this.analyzeBtn.addEventListener('click', () => {
            this.analyzeFrame();
        });
        
        log.info('APIClient initialized with modular architecture');
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
                log.info('Backend connection successful');
            } else {
                throw new Error('Backend responded with error');
            }
        } catch (error) {
            statusElement.textContent = '❌ Backend desconectado';
            statusElement.className = 'connection-status disconnected';
            log.error('Backend connection failed:', error);
            
            // Retry after 10 seconds
            setTimeout(() => this.checkBackendConnection(), 10000);
        }
    }
    
    async analyzeFrame() {
        try {
            // DEFENSIVE: Verify videoPlayer exists
            if (!window.videoPlayer) {
                alert('Error: Video player no inicializado. Recarga la pagina.');
                log.error('CRITICAL: videoPlayer not initialized!');
                return;
            }

            // Get captured frame from video player
            const frame = window.videoPlayer.getCapturedFrame();
            if (!frame) {
                alert('Por favor captura un frame primero usando el boton "Capturar Frame"');
                log.warn('No frame captured. User needs to capture frame first.');
                return;
            }

            log.debug('Frame obtained from videoPlayer');

            // Get ROI if selected
            const roi = window.roiSelector?.getROI();

            // Show loading via UIManager
            this.uiManager.showLoading();

            log.debug('Sending frame for streaming analysis...', roi ? { roi } : 'full frame');

            // Prepare request payload
            const payload = {
                frame: frame,
                roi: roi || null,
                context: ''
            };

            // Send request to SSE streaming endpoint
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            try {
                const response = await fetch(`${this.baseURL}/analyze-frame-stream`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload),
                    signal: controller.signal
                });

                // H-8: Don't clear timeout after headers — restart it for the stream phase.
                // Each chunk resets the timer so we only abort on true stalls.
                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                if (!response.body) {
                    throw new Error('Streaming response body is not available');
                }

                // Parse SSE stream
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let finalReport = null;
                let agentsCompleted = 0;

                // H-8: Per-chunk stall timeout — if no data arrives for 60s, abort.
                const STALL_TIMEOUT_MS = 60000;
                let stallTimer = setTimeout(() => controller.abort(), STALL_TIMEOUT_MS);

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    // Reset stall timer on every received chunk
                    clearTimeout(stallTimer);
                    stallTimer = setTimeout(() => controller.abort(), STALL_TIMEOUT_MS);

                    buffer += decoder.decode(value, { stream: true });

                    // Parse SSE events from buffer
                    // SSE format: "event: type\ndata: json\n\n"
                    const events = buffer.split('\n\n');
                    // Keep the last potentially incomplete event in the buffer
                    buffer = events.pop() || '';

                    for (const eventStr of events) {
                        if (!eventStr.trim()) continue;

                        const lines = eventStr.split('\n');
                        let eventType = '';
                        let eventData = '';

                        for (const line of lines) {
                            if (line.startsWith('event: ')) {
                                eventType = line.slice(7);
                            } else if (line.startsWith('data: ')) {
                                eventData = line.slice(6);
                            }
                        }

                        if (!eventData) continue;

                        try {
                            const parsed = JSON.parse(eventData);

                            if (eventType === 'agent_update') {
                                agentsCompleted++;
                                log.info(`Agent completed (${agentsCompleted}): ${parsed.agent}`);
                                this.uiManager.updateAgentCard(parsed.agent, parsed.result);
                            } else if (eventType === 'complete') {
                                log.info('Analysis complete - all agents finished');
                                finalReport = parsed.final_report;
                            } else if (eventType === 'error') {
                                log.error('Stream error:', parsed.error);
                                throw new Error(parsed.error || 'Analysis failed');
                            }
                        } catch (parseError) {
                            if (parseError.message && !parseError.message.includes('JSON')) {
                                throw parseError;
                            }
                            log.warn('Failed to parse SSE event:', eventStr);
                        }
                    }
                }

                // H-8: Stream finished — clear stall timer
                clearTimeout(stallTimer);

                // Display final complete results
                if (finalReport) {
                    this.displayResults(finalReport);
                } else {
                    throw new Error('Stream ended without complete event');
                }

            } catch (error) {
                clearTimeout(timeoutId);

                if (error.name === 'AbortError') {
                    throw new Error('Timeout: El analisis tomo demasiado tiempo (>2min). Verifica la conexion con el servidor LLM.');
                }
                throw error;
            }

        } catch (error) {
            log.error('Analysis error:', error);
            this.uiManager.showError(error.message);
        }
    }
    
    displayResults(results) {
        this.lastResults = results;
        
        // DEFENSIVE: Ensure frame is captured before storing
        const capturedFrame = window.videoPlayer?.getCapturedFrame();
        if (!capturedFrame) {
            log.error('CRITICAL: No frame available from videoPlayer!');
            this.uiManager.showError('Error interno: No se pudo obtener el frame capturado. Intenta capturar el frame nuevamente.');
            return;
        }
        
        this.currentFrame = capturedFrame;
        this.currentROI = window.roiSelector?.getROI();  // Store ROI for chat
        this.isMultiFrameAnalysis = false;  // Single frame analysis
        this.frameCollection = null;  // Clear multi-frame collection
        
        log.debug('Frame stored in apiClient:', this.currentFrame ? 'YES' : 'NO');
        
        // Delegate UI updates to UIManager
        this.uiManager.displayResults(results);
        
        // Enable chat after analysis
        this.chatHandler.enable();
        this.chatHandler.reset();
        
        // Enable professional features
        if (window.professionalFeatures) {
            window.professionalFeatures.enableButtons();
        }
        
        log.info('Results displayed and chat controls activated');
    }
    
    displayBatchResults(results, frameCollection) {
        this.lastResults = results;
        this.frameCollection = frameCollection;
        this.isMultiFrameAnalysis = true;
        this.currentFrame = null;  // No single frame in multi-frame analysis
        this.currentROI = null;
        
        // Delegate to UIManager
        this.uiManager.displayBatchResults(results, frameCollection);
        
        // Enable chat for multi-frame context
        this.chatHandler.enable();
        this.chatHandler.reset();
        
        // Enable professional features
        if (window.professionalFeatures) {
            window.professionalFeatures.enableButtons();
        }
        
        log.info('Multi-frame results displayed');
    }
}

// Initialize API Client when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.apiClient = new APIClient();
});
