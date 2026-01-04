/**
 * UI Manager Module
 * Handles all UI updates, displays, and user interactions
 */

export class UIManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        
        // DOM elements
        this.analysisSection = document.getElementById('analysisSection');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.textResults = document.getElementById('textResults');
        this.jsonResults = document.getElementById('jsonResults');
        this.previewCanvas = document.getElementById('previewCanvas');
        this.copyJsonBtn = document.getElementById('copyJsonBtn');
        this.downloadReportBtn = document.getElementById('downloadReportBtn');
        this.newAnalysisBtn = document.getElementById('newAnalysisBtn');
        
        this.init();
    }
    
    init() {
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
    }
    
    showLoading() {
        this.analysisSection.style.display = 'block';
        this.loadingIndicator.style.display = 'block';
        this.resultsContainer.style.display = 'none';
        
        // Scroll to analysis section
        this.analysisSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    displayResults(results) {
        // Hide loading
        this.loadingIndicator.style.display = 'none';
        this.resultsContainer.style.display = 'block';
        
        // Display text report
        this.textResults.textContent = results.text || 'No text report available';
        
        // Display JSON report
        this.jsonResults.textContent = JSON.stringify(results.json, null, 2);
        
        // Display preview (captured frame with ROI)
        this.displayPreview();
    }
    
    displayBatchResults(results, frameCollection) {
        // Hide loading
        this.loadingIndicator.style.display = 'none';
        this.resultsContainer.style.display = 'block';
        
        // Display multi-frame report
        this.textResults.textContent = results.text || 'No text report available';
        this.jsonResults.textContent = JSON.stringify(results.json, null, 2);
        
        // For multi-frame, show a collage or summary preview
        console.log('📊 Multi-frame results displayed:', frameCollection.length, 'frames');
    }
    
    displayPreview() {
        const frame = window.videoPlayer?.getCapturedFrame();
        const roi = window.roiSelector?.getROI();
        
        if (!frame) {
            console.warn('⚠️ No frame available for preview');
            return;
        }
        
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
        document.querySelector(`.tab[data-tab="${tabName}"]`)?.classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}Tab`)?.classList.add('active');
    }
    
    copyJSON() {
        if (!this.apiClient.lastResults) return;
        
        const jsonText = JSON.stringify(this.apiClient.lastResults.json, null, 2);
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
        if (!this.apiClient.lastResults) return;
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `watchdogs_analysis_${timestamp}.txt`;
        
        const blob = new Blob([this.apiClient.lastResults.text], { type: 'text/plain' });
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
        this.apiClient.lastResults = null;
        this.apiClient.currentFrame = null;
        this.apiClient.chatHistory = [];
        
        if (this.apiClient.chatHandler) {
            this.apiClient.chatHandler.reset();
        }
        
        if (this.apiClient.chatHandler?.sendChat) {
            this.apiClient.chatHandler.sendChat.disabled = true;
        }
        if (this.apiClient.chatHandler?.chatInput) {
            this.apiClient.chatHandler.chatInput.disabled = true;
        }
        
        window.roiSelector?.clearROI();
        console.log('🔄 Analysis reset');
    }
}
