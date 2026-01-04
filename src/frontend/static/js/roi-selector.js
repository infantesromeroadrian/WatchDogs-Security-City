/**
 * ROI (Region of Interest) Selector
 * Allows user to draw rectangle on captured frame for focused analysis
 */

class ROISelector {
    constructor() {
        // DOM elements
        this.canvas = document.getElementById('roiCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.clearRoiBtn = document.getElementById('clearRoiBtn');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.selectionInfo = document.getElementById('selectionInfo');
        
        // State
        this.isDrawing = false;
        this.startX = 0;
        this.startY = 0;
        this.currentROI = null;
        this.frameLoaded = false;
        
        this.init();
    }
    
    init() {
        this.clearRoiBtn.addEventListener('click', () => this.clearROI());
        
        // Canvas events
        this.canvas.addEventListener('mousedown', (e) => this.startDrawing(e));
        this.canvas.addEventListener('mousemove', (e) => this.draw(e));
        this.canvas.addEventListener('mouseup', (e) => this.stopDrawing(e));
        this.canvas.addEventListener('mouseleave', () => this.stopDrawing());
        
        // Touch events for mobile (convert to mouse events)
        const touchToMouse = (e, type) => {
            e.preventDefault();
            const touch = e.touches?.[0];
            this.canvas.dispatchEvent(new MouseEvent(type, {
                clientX: touch?.clientX,
                clientY: touch?.clientY
            }));
        };
        this.canvas.addEventListener('touchstart', (e) => touchToMouse(e, 'mousedown'));
        this.canvas.addEventListener('touchmove', (e) => touchToMouse(e, 'mousemove'));
        this.canvas.addEventListener('touchend', (e) => { e.preventDefault(); this.stopDrawing(); });
    }
    
    setFrame(frameBase64, width, height) {
        // Set canvas size to match video
        this.canvas.width = width;
        this.canvas.height = height;
        
        // Enable drawing
        this.canvas.classList.add('drawing');
        this.frameLoaded = true;
        
        // Enable buttons
        this.clearRoiBtn.disabled = false;
        this.analyzeBtn.disabled = false;
        
        console.log('🎯 ROI selector ready');
        this.updateSelectionInfo('Dibuja un rectángulo sobre la región a analizar (o analiza el frame completo)');
    }
    
    startDrawing(e) {
        if (!this.frameLoaded) return;
        
        this.isDrawing = true;
        const rect = this.canvas.getBoundingClientRect();
        this.startX = (e.clientX - rect.left) * (this.canvas.width / rect.width);
        this.startY = (e.clientY - rect.top) * (this.canvas.height / rect.height);
        
        console.log('🖱️ Started drawing ROI at:', Math.round(this.startX), Math.round(this.startY));
        this.updateSelectionInfo('Dibujando ROI...');
    }
    
    draw(e) {
        if (!this.isDrawing || !this.frameLoaded) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const currentX = (e.clientX - rect.left) * (this.canvas.width / rect.width);
        const currentY = (e.clientY - rect.top) * (this.canvas.height / rect.height);
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw rectangle
        const width = currentX - this.startX;
        const height = currentY - this.startY;
        
        // Bright green stroke for visibility
        this.ctx.strokeStyle = '#00ff00';
        this.ctx.lineWidth = 4;
        this.ctx.setLineDash([5, 3]); // Dashed line while drawing
        this.ctx.strokeRect(this.startX, this.startY, width, height);
        this.ctx.setLineDash([]); // Reset dash
        
        // Fill with semi-transparent color
        this.ctx.fillStyle = 'rgba(0, 255, 0, 0.15)';
        this.ctx.fillRect(this.startX, this.startY, width, height);
        
        // Show dimensions while drawing
        const absWidth = Math.abs(width);
        const absHeight = Math.abs(height);
        this.updateSelectionInfo(`Seleccionando: ${Math.round(absWidth)}x${Math.round(absHeight)}px`);
    }
    
    stopDrawing(e) {
        if (!this.isDrawing) return;
        
        this.isDrawing = false;
        
        if (e && e.clientX !== undefined) {
            const rect = this.canvas.getBoundingClientRect();
            const endX = (e.clientX - rect.left) * (this.canvas.width / rect.width);
            const endY = (e.clientY - rect.top) * (this.canvas.height / rect.height);
            
            // Calculate ROI coordinates
            const x = Math.min(this.startX, endX);
            const y = Math.min(this.startY, endY);
            const width = Math.abs(endX - this.startX);
            const height = Math.abs(endY - this.startY);
            
            // Only save if selection has meaningful size
            if (width > 10 && height > 10) {
                this.currentROI = {
                    x: Math.round(x),
                    y: Math.round(y),
                    width: Math.round(width),
                    height: Math.round(height)
                };
                
                // Redraw final ROI with solid line
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                this.ctx.strokeStyle = '#00ff00';
                this.ctx.lineWidth = 4;
                this.ctx.strokeRect(x, y, width, height);
                this.ctx.fillStyle = 'rgba(0, 255, 0, 0.15)';
                this.ctx.fillRect(x, y, width, height);
                
                // Add corner markers for better visibility
                const markerSize = 20;
                this.ctx.fillStyle = '#00ff00';
                // Top-left
                this.ctx.fillRect(x, y, markerSize, 4);
                this.ctx.fillRect(x, y, 4, markerSize);
                // Top-right
                this.ctx.fillRect(x + width - markerSize, y, markerSize, 4);
                this.ctx.fillRect(x + width - 4, y, 4, markerSize);
                // Bottom-left
                this.ctx.fillRect(x, y + height - 4, markerSize, 4);
                this.ctx.fillRect(x, y + height - markerSize, 4, markerSize);
                // Bottom-right
                this.ctx.fillRect(x + width - markerSize, y + height - 4, markerSize, 4);
                this.ctx.fillRect(x + width - 4, y + height - markerSize, 4, markerSize);
                
                console.log('✅ ROI selected:', this.currentROI);
                this.updateSelectionInfo(
                    `ROI seleccionado: ${this.currentROI.width}x${this.currentROI.height}px ` +
                    `en (${this.currentROI.x}, ${this.currentROI.y})`
                );
            } else {
                this.clearROI();
                this.updateSelectionInfo('Selección muy pequeña - intenta de nuevo');
            }
        }
    }
    
    clearROI() {
        this.currentROI = null;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.updateSelectionInfo('✨ ROI limpiado - Dibuja una nueva región o analiza el frame completo');
        console.log('🗑️ ROI cleared');
    }
    
    getROI() {
        return this.currentROI;
    }
    
    updateSelectionInfo(message) {
        this.selectionInfo.textContent = message;
    }
}

// Initialize ROI selector when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.roiSelector = new ROISelector();
});

