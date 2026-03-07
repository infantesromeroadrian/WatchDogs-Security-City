/**
 * ROI (Region of Interest) Selector with Zoom & Pan
 * Allows user to draw rectangle on captured frame for focused analysis
 * 
 * Features:
 * - Zoom in/out with buttons or mouse wheel
 * - Pan (drag) to navigate zoomed image
 * - Draw ROI rectangle with precise coordinates
 * - Coordinates automatically adjusted to original image scale
 */

// IIFE to avoid global `const` collisions with other classic scripts
(function() {
'use strict';

// L-2: Use global logger (set by modules/logger.js via window.__wdLog)
const log = window.__wdLog || console;

class ROISelector {
    constructor() {
        // DOM elements
        this.canvas = document.getElementById('roiCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.clearRoiBtn = document.getElementById('clearRoiBtn');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.selectionInfo = document.getElementById('selectionInfo');
        
        // Zoom controls
        this.zoomControls = document.querySelector('.zoom-controls');
        this.zoomInBtn = document.getElementById('zoomInBtn');
        this.zoomOutBtn = document.getElementById('zoomOutBtn');
        this.zoomResetBtn = document.getElementById('zoomResetBtn');
        this.zoomLevelDisplay = document.getElementById('zoomLevel');
        
        // Drawing state
        this.isDrawing = false;
        this.startX = 0;
        this.startY = 0;
        this.currentROI = null;
        this.frameLoaded = false;
        
        // Zoom & Pan state
        this.scale = 1.0;
        this.minScale = 0.5;
        this.maxScale = 5.0;
        this.offsetX = 0;
        this.offsetY = 0;
        this.isPanning = false;
        this.panStartX = 0;
        this.panStartY = 0;
        
        // Frame image
        this.frameImage = null;
        
        this.init();
    }
    
    init() {
        // Initially hide canvas until frame is captured
        this.canvas.style.display = 'none';
        
        // Clear ROI button
        this.clearRoiBtn.addEventListener('click', () => this.clearROI());
        
        // Zoom controls
        this.zoomInBtn.addEventListener('click', () => this.zoomIn());
        this.zoomOutBtn.addEventListener('click', () => this.zoomOut());
        this.zoomResetBtn.addEventListener('click', () => this.resetZoom());
        
        // Mouse events for drawing ROI
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        // M-8: mouseleave should only cancel panning, not drop an in-progress ROI draw.
        // Drawing can be finalized when the user re-enters and releases, or via mouseup.
        this.canvas.addEventListener('mouseleave', () => {
            if (this.isPanning) {
                this.stopPan();
                this.canvas.style.cursor = this.scale > 1.0 ? 'grab' : 'crosshair';
            }
        });
        
        // Mouse wheel for zoom
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });
        
        // Touch events for mobile
        this.canvas.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        this.canvas.addEventListener('touchmove', (e) => this.handleTouchMove(e));
        this.canvas.addEventListener('touchend', (e) => this.handleTouchEnd(e));
        
        log.info('ROI Selector with Zoom initialized');
    }
    
    setFrame(frameBase64, width, height) {
        log.debug('Loading frame into ROI selector:', width, 'x', height);
        
        // Load image
        this.frameImage = new Image();
        this.frameImage.onload = () => {
            log.debug('Frame image loaded — canvas:', width, 'x', height);
            
            // Set canvas resolution to match video resolution
            this.canvas.width = width;
            this.canvas.height = height;
            
            // Reset zoom/pan
            this.resetZoom();
            
            // Draw initial frame
            this.redraw();
            
            // Make canvas visible and enable interactions
            this.canvas.style.display = 'block';
            this.canvas.classList.add('drawing');
            this.frameLoaded = true;
            
            // Show zoom controls
            this.zoomControls.style.display = 'block';
            
            // Enable buttons
            this.clearRoiBtn.disabled = false;
            this.analyzeBtn.disabled = false;
            
            log.debug('ROI selector ready — scale:', this.scale, 'offset:', this.offsetX, this.offsetY);
            
            this.updateSelectionInfo('🔍 Usa zoom para ver detalles. Dibuja un rectángulo sobre la región a analizar.');
        };
        
        this.frameImage.onerror = (e) => {
            log.error('Failed to load frame image:', e);
            this.updateSelectionInfo('❌ Error al cargar el frame');
        };
        
        this.frameImage.src = frameBase64;
    }
    
    // ========================================================================
    // ZOOM METHODS
    // ========================================================================
    
    zoomIn() {
        this.setZoom(this.scale * 1.25);
    }
    
    zoomOut() {
        this.setZoom(this.scale / 1.25);
    }
    
    resetZoom() {
        this.scale = 1.0;
        this.offsetX = 0;
        this.offsetY = 0;
        this.updateZoomDisplay();
        this.redraw();
    }
    
    setZoom(newScale, centerX, centerY) {
        const oldScale = this.scale;
        this.scale = Math.max(this.minScale, Math.min(this.maxScale, newScale));
        
        // If center point provided, zoom towards it
        if (centerX !== undefined && centerY !== undefined) {
            const scaleChange = this.scale / oldScale;
            this.offsetX = centerX - (centerX - this.offsetX) * scaleChange;
            this.offsetY = centerY - (centerY - this.offsetY) * scaleChange;
        }
        
        // Constrain pan to keep image visible
        this.constrainPan();
        
        this.updateZoomDisplay();
        this.redraw();
    }
    
    handleWheel(e) {
        e.preventDefault();
        
        if (!this.frameLoaded) return;
        
        // Get mouse position
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        // Zoom in/out
        const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
        this.setZoom(this.scale * zoomFactor, mouseX, mouseY);
    }
    
    updateZoomDisplay() {
        this.zoomLevelDisplay.textContent = `${Math.round(this.scale * 100)}%`;
    }
    
    // ========================================================================
    // PAN METHODS
    // ========================================================================
    
    startPan(x, y) {
        this.isPanning = true;
        this.panStartX = x - this.offsetX;
        this.panStartY = y - this.offsetY;
    }
    
    updatePan(x, y) {
        if (!this.isPanning) return;
        
        this.offsetX = x - this.panStartX;
        this.offsetY = y - this.panStartY;
        
        this.constrainPan();
        this.redraw();
    }
    
    stopPan() {
        this.isPanning = false;
    }
    
    constrainPan() {
        const scaledWidth = this.canvas.width * this.scale;
        const scaledHeight = this.canvas.height * this.scale;
        
        // Don't allow panning beyond image bounds
        const maxOffsetX = Math.max(0, scaledWidth - this.canvas.width);
        const maxOffsetY = Math.max(0, scaledHeight - this.canvas.height);
        
        this.offsetX = Math.max(-maxOffsetX, Math.min(0, this.offsetX));
        this.offsetY = Math.max(-maxOffsetY, Math.min(0, this.offsetY));
    }
    
    // ========================================================================
    // COORDINATE TRANSFORMATION
    // ========================================================================
    
    screenToCanvas(screenX, screenY) {
        const rect = this.canvas.getBoundingClientRect();
        // Calculate position relative to canvas element
        const x = screenX - rect.left;
        const y = screenY - rect.top;
        
        // Scale from CSS size to canvas resolution
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        
        const canvasX = x * scaleX;
        const canvasY = y * scaleY;
        
        return { x: canvasX, y: canvasY };
    }
    
    canvasToImage(canvasX, canvasY) {
        // Transform canvas coordinates to original image coordinates
        const imageX = (canvasX - this.offsetX) / this.scale;
        const imageY = (canvasY - this.offsetY) / this.scale;
        return { x: imageX, y: imageY };
    }
    
    imageToCanvas(imageX, imageY) {
        // Transform image coordinates to canvas coordinates
        const canvasX = imageX * this.scale + this.offsetX;
        const canvasY = imageY * this.scale + this.offsetY;
        return { x: canvasX, y: canvasY };
    }
    
    // ========================================================================
    // MOUSE/TOUCH EVENT HANDLERS
    // ========================================================================
    
    handleMouseDown(e) {
        if (!this.frameLoaded) return;
        
        const { x, y } = this.screenToCanvas(e.clientX, e.clientY);
        
        // H-2: Pan only on middle-click or Shift+click — left click draws ROI
        // even when zoomed (previously scale > 1.0 forced panning, blocking ROI)
        if (e.button === 1 || e.shiftKey) {
            this.startPan(x, y);
            this.canvas.style.cursor = 'grabbing';
        } else {
            // Start drawing ROI
            const imgCoords = this.canvasToImage(x, y);
            this.isDrawing = true;
            this.startX = imgCoords.x;
            this.startY = imgCoords.y;
            
            log.debug('Started drawing ROI at:', Math.round(this.startX), Math.round(this.startY));
            this.updateSelectionInfo('Dibujando ROI...');
        }
    }
    
    handleMouseMove(e) {
        if (!this.frameLoaded) return;
        
        const { x, y } = this.screenToCanvas(e.clientX, e.clientY);
        
        if (this.isPanning) {
            this.updatePan(x, y);
        } else if (this.isDrawing) {
            const imgCoords = this.canvasToImage(x, y);
            this.drawTemporaryROI(imgCoords.x, imgCoords.y);
        }
        
        // Update cursor
        if (this.scale > 1.0 && !this.isDrawing) {
            this.canvas.style.cursor = this.isPanning ? 'grabbing' : 'grab';
        } else {
            this.canvas.style.cursor = 'crosshair';
        }
    }
    
    handleMouseUp(e) {
        if (this.isPanning) {
            this.stopPan();
            this.canvas.style.cursor = this.scale > 1.0 ? 'grab' : 'crosshair';
            return;
        }
        
        if (!this.isDrawing) return;
        
        this.isDrawing = false;
        
        if (e && e.clientX !== undefined) {
            const { x, y } = this.screenToCanvas(e.clientX, e.clientY);
            const imgCoords = this.canvasToImage(x, y);
            this.finalizeROI(imgCoords.x, imgCoords.y);
        }
    }
    
    handleTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        this.handleMouseDown({ clientX: touch.clientX, clientY: touch.clientY, button: 0 });
    }
    
    handleTouchMove(e) {
        e.preventDefault();
        const touch = e.touches[0];
        this.handleMouseMove({ clientX: touch.clientX, clientY: touch.clientY });
    }
    
    handleTouchEnd(e) {
        e.preventDefault();
        // H-3: Use changedTouches to get final position (touches is empty on touchend)
        const touch = e.changedTouches?.[0];
        if (touch) {
            this.handleMouseUp({ clientX: touch.clientX, clientY: touch.clientY });
        } else {
            this.handleMouseUp();
        }
    }
    
    // ========================================================================
    // DRAWING METHODS
    // ========================================================================
    
    redraw() {
        if (!this.frameImage) return;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Save context state
        this.ctx.save();
        
        // Apply zoom and pan transformation
        this.ctx.translate(this.offsetX, this.offsetY);
        this.ctx.scale(this.scale, this.scale);
        
        // Draw the frame image
        this.ctx.drawImage(this.frameImage, 0, 0, this.canvas.width, this.canvas.height);
        
        // Draw current ROI if exists
        if (this.currentROI) {
            this.drawROI(this.currentROI.x, this.currentROI.y, this.currentROI.width, this.currentROI.height);
        }
        
        // Restore context state
        this.ctx.restore();
    }
    
    drawTemporaryROI(endX, endY) {
        const width = endX - this.startX;
        const height = endY - this.startY;
        
        // Redraw everything
        this.redraw();
        
        // Save context state
        this.ctx.save();
        this.ctx.translate(this.offsetX, this.offsetY);
        this.ctx.scale(this.scale, this.scale);
        
        // Draw temporary ROI with dashed line
        this.ctx.strokeStyle = '#00ff00';
        this.ctx.lineWidth = 4 / this.scale;  // Adjust line width for zoom
        this.ctx.setLineDash([5 / this.scale, 3 / this.scale]);
        this.ctx.strokeRect(this.startX, this.startY, width, height);
        this.ctx.setLineDash([]);
        
        this.ctx.fillStyle = 'rgba(0, 255, 0, 0.15)';
        this.ctx.fillRect(this.startX, this.startY, width, height);
        
        this.ctx.restore();
        
        // Show dimensions
        const absWidth = Math.abs(width);
        const absHeight = Math.abs(height);
        this.updateSelectionInfo(`Seleccionando: ${Math.round(absWidth)}x${Math.round(absHeight)}px`);
    }
    
    drawROI(x, y, width, height) {
        this.ctx.strokeStyle = '#00ff00';
        this.ctx.lineWidth = 4 / this.scale;
        this.ctx.strokeRect(x, y, width, height);
        
        this.ctx.fillStyle = 'rgba(0, 255, 0, 0.15)';
        this.ctx.fillRect(x, y, width, height);
        
        // Add corner markers
        const markerSize = 20 / this.scale;
        const lineWidth = 4 / this.scale;
        this.ctx.fillStyle = '#00ff00';
        
        // Top-left
        this.ctx.fillRect(x, y, markerSize, lineWidth);
        this.ctx.fillRect(x, y, lineWidth, markerSize);
        // Top-right
        this.ctx.fillRect(x + width - markerSize, y, markerSize, lineWidth);
        this.ctx.fillRect(x + width - lineWidth, y, lineWidth, markerSize);
        // Bottom-left
        this.ctx.fillRect(x, y + height - lineWidth, markerSize, lineWidth);
        this.ctx.fillRect(x, y + height - markerSize, lineWidth, markerSize);
        // Bottom-right
        this.ctx.fillRect(x + width - markerSize, y + height - lineWidth, markerSize, lineWidth);
        this.ctx.fillRect(x + width - lineWidth, y + height - markerSize, lineWidth, markerSize);
    }
    
    finalizeROI(endX, endY) {
        // Calculate ROI coordinates (in original image space)
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
            
            this.redraw();
            
            log.debug('ROI selected:', this.currentROI);
            this.updateSelectionInfo(
                `✅ ROI seleccionado: ${this.currentROI.width}x${this.currentROI.height}px ` +
                `en (${this.currentROI.x}, ${this.currentROI.y}) - Usa zoom para ver detalles`
            );
            
            // Automatically zoom and pan to the ROI for better viewing
            this.zoomToROI();
        } else {
            this.redraw();
            this.updateSelectionInfo('⚠️ Selección muy pequeña - intenta de nuevo');
        }
    }
    
    zoomToROI() {
        if (!this.currentROI) return;
        
        // Calculate the scale needed to fit ROI in the canvas with some padding
        const paddingFactor = 0.9; // Use 90% of canvas to leave some margin
        const scaleX = (this.canvas.width * paddingFactor) / this.currentROI.width;
        const scaleY = (this.canvas.height * paddingFactor) / this.currentROI.height;
        
        // Use the smaller scale to ensure entire ROI fits
        const targetScale = Math.min(scaleX, scaleY, this.maxScale);
        
        // Calculate center of ROI
        const roiCenterX = this.currentROI.x + this.currentROI.width / 2;
        const roiCenterY = this.currentROI.y + this.currentROI.height / 2;
        
        // Set scale
        this.scale = targetScale;
        
        // Calculate offset to center ROI
        this.offsetX = this.canvas.width / 2 - roiCenterX * this.scale;
        this.offsetY = this.canvas.height / 2 - roiCenterY * this.scale;
        
        this.constrainPan();
        this.updateZoomDisplay();
        this.redraw();
        
        log.debug(`Zoomed to ROI: scale=${this.scale.toFixed(2)}x, centered at (${roiCenterX}, ${roiCenterY})`);
    }
    
    clearROI() {
        this.currentROI = null;
        this.resetZoom(); // Also reset zoom when clearing ROI
        this.redraw();
        this.updateSelectionInfo('✨ ROI limpiado - Dibuja una nueva región o analiza el frame completo');
        log.debug('ROI cleared');
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

})(); // End IIFE
