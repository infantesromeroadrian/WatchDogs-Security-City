/**
 * API Client - Main Orchestrator (Refactored)
 * Coordinates communication with backend and delegates to specialized modules
 */

import { ChatHandler } from './modules/chat-handler.js';
import { UIManager } from './modules/ui-manager.js';
import { ImageUtils } from './modules/image-utils.js';

class APIClient {
    constructor() {
        // Dynamic base URL (works in Docker and local)
        this.baseURL = window.location.origin + '/api';
        this.timeout = 60000; // 60 seconds timeout for analysis
        
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
        
        // Expose imageUtils globally for other modules
        window.imageUtils = this.imageUtils;
        
        this.init();
    }
    
    init() {
        // Check backend connection on load
        this.checkBackendConnection();
        
        // Analyze button
        this.analyzeBtn.addEventListener('click', () => {
            this.analyzeFrame();
        });
        
        console.log('✅ APIClient initialized with modular architecture');
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
            // DEFENSIVE: Verify videoPlayer exists
            if (!window.videoPlayer) {
                alert('❌ Error: Video player no inicializado. Recarga la página.');
                console.error('❌ CRITICAL: videoPlayer not initialized!');
                return;
            }
            
            // Get captured frame from video player
            const frame = window.videoPlayer.getCapturedFrame();
            if (!frame) {
                alert('⚠️ Por favor captura un frame primero usando el botón "📸 Capturar Frame"');
                console.warn('❌ No frame captured. User needs to capture frame first.');
                return;
            }
            
            console.log('✅ Frame obtained from videoPlayer');
            
            // Get ROI if selected
            const roi = window.roiSelector?.getROI();
            
            // Show loading via UIManager
            this.uiManager.showLoading();
            
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
            this.uiManager.showError(error.message);
        }
    }
    
    displayResults(results) {
        this.lastResults = results;
        
        // DEFENSIVE: Ensure frame is captured before storing
        const capturedFrame = window.videoPlayer?.getCapturedFrame();
        if (!capturedFrame) {
            console.error('❌ CRITICAL: No frame available from videoPlayer!');
            this.uiManager.showError('Error interno: No se pudo obtener el frame capturado. Intenta capturar el frame nuevamente.');
            return;
        }
        
        this.currentFrame = capturedFrame;
        this.currentROI = window.roiSelector?.getROI();  // Store ROI for chat
        this.isMultiFrameAnalysis = false;  // Single frame analysis
        this.frameCollection = null;  // Clear multi-frame collection
        
        console.log('✅ Frame stored in apiClient:', this.currentFrame ? 'YES' : 'NO');
        
        // Delegate UI updates to UIManager
        this.uiManager.displayResults(results);
        
        // Enable chat after analysis
        this.chatHandler.enable();
        this.chatHandler.reset();
        
        // Enable professional features
        if (window.professionalFeatures) {
            window.professionalFeatures.enableButtons();
        }
        
        console.log('📊 Results displayed and chat controls activated');
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
        
        console.log('📊 Multi-frame results displayed');
    }
}

// Initialize API Client when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.apiClient = new APIClient();
});
