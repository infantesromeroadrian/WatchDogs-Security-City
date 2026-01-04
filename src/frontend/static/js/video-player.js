/**
 * Video Player Controller
 * Handles video upload, playback controls, and frame capture
 */

class VideoPlayer {
    constructor() {
        // DOM elements
        this.videoInput = document.getElementById('videoInput');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.uploadStatus = document.getElementById('uploadStatus');
        this.playerSection = document.getElementById('playerSection');
        this.videoPlayer = document.getElementById('videoPlayer');
        this.playPauseBtn = document.getElementById('playPauseBtn');
        this.captureBtn = document.getElementById('captureBtn');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        
        // State
        this.currentVideoFile = null;
        this.capturedFrame = null;
        
        this.init();
    }
    
    init() {
        // Upload button triggers file input
        this.uploadBtn.addEventListener('click', () => {
            this.videoInput.click();
        });
        
        // Handle file selection
        this.videoInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.loadVideo(file);
            }
        });
        
        // Play/Pause control
        this.playPauseBtn.addEventListener('click', () => {
            this.togglePlayPause();
        });
        
        // Capture frame
        this.captureBtn.addEventListener('click', () => {
            this.captureFrame();
        });
        
        // Video player events
        this.videoPlayer.addEventListener('play', () => {
            this.playPauseBtn.textContent = '⏸️ Pause';
        });
        
        this.videoPlayer.addEventListener('pause', () => {
            this.playPauseBtn.textContent = '▶️ Play';
        });
        
        this.videoPlayer.addEventListener('loadedmetadata', () => {
            this.captureBtn.disabled = false;
            console.log('✅ Video loaded successfully');
        });
    }
    
    loadVideo(file) {
        // Validate file type
        if (!file.type.startsWith('video/')) {
            this.showUploadStatus('❌ Por favor selecciona un archivo de video válido', 'error');
            return;
        }
        
        // Validate file size (100MB limit)
        const maxSize = 100 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showUploadStatus('❌ El video es demasiado grande (máximo 100MB)', 'error');
            return;
        }
        
        this.currentVideoFile = file;
        
        // Create object URL for video
        const videoURL = URL.createObjectURL(file);
        this.videoPlayer.src = videoURL;
        
        // Show player section
        this.playerSection.style.display = 'block';
        
        // Update status
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        this.showUploadStatus(`✅ Video cargado: ${file.name} (${sizeMB} MB)`, 'success');
        
        console.log('📹 Video loaded:', file.name);
    }
    
    togglePlayPause() {
        if (this.videoPlayer.paused) {
            this.videoPlayer.play();
        } else {
            this.videoPlayer.pause();
        }
    }
    
    captureFrame() {
        // Pause video if playing
        if (!this.videoPlayer.paused) {
            this.videoPlayer.pause();
        }
        
        // Create canvas to capture frame
        const canvas = document.createElement('canvas');
        canvas.width = this.videoPlayer.videoWidth;
        canvas.height = this.videoPlayer.videoHeight;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(this.videoPlayer, 0, 0, canvas.width, canvas.height);
        
        // Store captured frame as base64
        this.capturedFrame = canvas.toDataURL('image/png');
        
        // DEFENSIVE: Verify frame was captured
        if (!this.capturedFrame || this.capturedFrame.length === 0) {
            console.error('❌ CRITICAL: Frame capture failed!');
            alert('❌ Error al capturar el frame. Intenta nuevamente.');
            return;
        }
        
        console.log('📸 Frame captured successfully:', canvas.width, 'x', canvas.height);
        console.log('   - Frame size (base64):', (this.capturedFrame.length / 1024).toFixed(2), 'KB');
        
        // Initialize ROI selector with captured frame
        if (window.roiSelector) {
            window.roiSelector.setFrame(this.capturedFrame, canvas.width, canvas.height);
            console.log('✅ ROI selector updated with frame');
        }
        
        // Notify multi-frame analyzer
        if (window.multiFrameAnalyzer) {
            window.multiFrameAnalyzer.setCurrentFrame(this.capturedFrame);
            console.log('✅ Multi-frame analyzer updated with frame');
        }
        
        // Show success feedback
        this.captureBtn.textContent = '✅ Frame Capturado';
        setTimeout(() => {
            this.captureBtn.textContent = '📸 Capturar Frame';
        }, 2000);
    }
    
    getCapturedFrame() {
        if (!this.capturedFrame) {
            console.warn('⚠️ getCapturedFrame called but no frame captured');
        }
        return this.capturedFrame;
    }
    
    showUploadStatus(message, type = 'info') {
        this.uploadStatus.textContent = message;
        this.uploadStatus.style.color = type === 'error' ? '#dc3545' : 
                                        type === 'success' ? '#28a745' : '#666';
    }
}

// Initialize video player when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.videoPlayer = new VideoPlayer();
});

