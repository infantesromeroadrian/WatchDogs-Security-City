/**
 * Multi-Frame Analysis Module
 * Handles collection of multiple frames for enhanced OSINT analysis
 */

class MultiFrameAnalyzer {
    constructor() {
        this.frameCollection = [];
        this.maxFrames = 10;
        this.currentFrame = null;
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        this.addToCollectionBtn = document.getElementById('addToCollectionBtn');
        this.analyzeBatchBtn = document.getElementById('analyzeBatchBtn');
        this.clearCollectionBtn = document.getElementById('clearCollectionBtn');
        this.frameCollectionGrid = document.getElementById('frameCollectionGrid');
        this.frameCountSpan = document.getElementById('frameCount');
        this.captureBtn = document.getElementById('captureBtn');
    }
    
    bindEvents() {
        this.addToCollectionBtn.addEventListener('click', () => this.addCurrentFrameToCollection());
        this.analyzeBatchBtn.addEventListener('click', () => this.analyzeBatch());
        this.clearCollectionBtn.addEventListener('click', () => this.clearCollection());
    }
    
    /**
     * Set current captured frame
     */
    setCurrentFrame(frameBase64) {
        this.currentFrame = frameBase64;
        this.addToCollectionBtn.disabled = false;
    }
    
    /**
     * Add current frame to collection
     */
    addCurrentFrameToCollection() {
        if (!this.currentFrame) {
            alert('❌ No hay frame capturado. Primero captura un frame con el botón "📸 Capturar Frame"');
            return;
        }
        
        if (this.frameCollection.length >= this.maxFrames) {
            alert(`⚠️ Máximo ${this.maxFrames} frames en colección. Elimina algunos o analiza la colección actual.`);
            return;
        }
        
        const frameData = {
            frame: this.currentFrame,
            description: `Frame ${this.frameCollection.length + 1}`,
            timestamp: new Date().toISOString(),
            thumbnail: this.currentFrame  // For preview
        };
        
        this.frameCollection.push(frameData);
        this.updateUI();
        
        console.log(`✅ Frame ${this.frameCollection.length} añadido a colección`);
        
        // Show toast notification
        this.showToast(`✅ Frame ${this.frameCollection.length} añadido a la colección`);
    }
    
    /**
     * Remove frame from collection
     */
    removeFrame(index) {
        if (index >= 0 && index < this.frameCollection.length) {
            this.frameCollection.splice(index, 1);
            this.updateUI();
            console.log(`🗑️ Frame eliminado. Total: ${this.frameCollection.length}`);
        }
    }
    
    /**
     * Clear all frames
     */
    clearCollection() {
        if (this.frameCollection.length === 0) {
            return;
        }
        
        if (confirm(`¿Eliminar todos los ${this.frameCollection.length} frames de la colección?`)) {
            this.frameCollection = [];
            this.updateUI();
            console.log('🗑️ Colección limpiada');
        }
    }
    
    /**
     * Update UI with current collection
     */
    updateUI() {
        // Update frame count
        this.frameCountSpan.textContent = this.frameCollection.length;
        
        // Enable/disable buttons
        this.analyzeBatchBtn.disabled = this.frameCollection.length < 2;
        this.clearCollectionBtn.disabled = this.frameCollection.length === 0;
        
        // Update grid
        this.frameCollectionGrid.innerHTML = '';
        
        this.frameCollection.forEach((frameData, index) => {
            const thumbnail = this.createThumbnail(frameData, index);
            this.frameCollectionGrid.appendChild(thumbnail);
        });
    }
    
    /**
     * Create thumbnail element
     */
    createThumbnail(frameData, index) {
        const div = document.createElement('div');
        div.className = 'frame-thumbnail';
        div.title = `${frameData.description} - ${new Date(frameData.timestamp).toLocaleTimeString()}`;
        
        div.innerHTML = `
            <img src="${frameData.thumbnail}" alt="Frame ${index + 1}">
            <div class="frame-thumbnail-overlay">
                <span class="frame-thumbnail-number">#${index + 1}</span>
            </div>
            <button class="frame-thumbnail-remove" title="Eliminar frame">✕</button>
        `;
        
        // Remove button event
        const removeBtn = div.querySelector('.frame-thumbnail-remove');
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.removeFrame(index);
        });
        
        // Click to preview (optional)
        div.addEventListener('click', () => {
            console.log(`Preview frame ${index + 1}`);
            // Could show full preview in modal
        });
        
        return div;
    }
    
    /**
     * Analyze batch of frames
     */
    async analyzeBatch() {
        if (this.frameCollection.length < 2) {
            alert('⚠️ Necesitas al menos 2 frames para análisis multi-frame');
            return;
        }
        
        console.log(`🔍 Iniciando análisis de ${this.frameCollection.length} frames...`);
        
        // Show loading
        const loadingIndicator = document.getElementById('loadingIndicator');
        const analysisSection = document.getElementById('analysisSection');
        analysisSection.style.display = 'block';
        loadingIndicator.style.display = 'block';
        loadingIndicator.querySelector('p').textContent = `🤖 Analizando ${this.frameCollection.length} frames con contexto acumulado...`;
        
        try {
            const response = await fetch('/api/analyze-batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    frames: this.frameCollection.map(f => ({
                        frame: f.frame,
                        description: f.description
                    })),
                    enable_context_accumulation: true
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            
            const data = await response.json();
            console.log('✅ Análisis multi-frame completo:', data);
            
            // Hide loading
            loadingIndicator.style.display = 'none';
            
            // Show results
            this.displayBatchResults(data.results);
            
        } catch (error) {
            console.error('❌ Error en análisis multi-frame:', error);
            loadingIndicator.style.display = 'none';
            alert(`❌ Error en análisis: ${error.message}`);
        }
    }
    
    /**
     * Display batch analysis results
     */
    displayBatchResults(results) {
        // Delegate to apiClient's displayBatchResults with frame collection
        if (window.apiClient) {
            window.apiClient.displayBatchResults(results, this.frameCollection);
        } else {
            console.error('❌ apiClient not available');
            // Fallback to basic display
            const resultsContainer = document.getElementById('resultsContainer');
            const textResults = document.getElementById('textResults');
            const jsonResults = document.getElementById('jsonResults');
            
            resultsContainer.style.display = 'block';
            textResults.textContent = results.summary || 'No summary available';
            jsonResults.textContent = JSON.stringify(results, null, 2);
            
            document.querySelector('.tab[data-tab="text"]')?.click();
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    
    /**
     * Show toast notification
     */
    showToast(message) {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #00d2ff;
            color: #1a1a2e;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: bold;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.multiFrameAnalyzer = new MultiFrameAnalyzer();
    console.log('✅ Multi-Frame Analyzer initialized');
});

// Add CSS for toast animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);
