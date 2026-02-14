/**
 * Video / Image Player Controller
 * Handles video & image upload, playback controls, and frame capture.
 *
 * Images are loaded directly as a captured frame — no manual capture step needed.
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
        /** @type {'video'|'image'|null} */
        this.mediaType = null;

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
                if (file.type.startsWith('image/')) {
                    this.loadImage(file);
                } else if (file.type.startsWith('video/')) {
                    this.loadVideo(file);
                } else {
                    this.showUploadStatus('❌ Formato no soportado. Usa video o imagen.', 'error');
                }
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

    // ========================================================================
    // Video loading (existing flow)
    // ========================================================================

    loadVideo(file) {
        // Validate file size (100MB limit)
        const maxSize = 100 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showUploadStatus('❌ El video es demasiado grande (máximo 100MB)', 'error');
            return;
        }

        this.mediaType = 'video';
        this.currentVideoFile = file;
        this.capturedFrame = null;

        // Restore video element & controls (may have been hidden by image mode)
        this.videoPlayer.style.display = 'block';
        this.playPauseBtn.style.display = '';
        this.captureBtn.style.display = '';
        this.captureBtn.disabled = true;

        // Restore ROI canvas to absolute overlay mode
        const roiCanvas = document.getElementById('roiCanvas');
        if (roiCanvas) {
            roiCanvas.style.position = 'absolute';
            roiCanvas.style.maxWidth = '';
            roiCanvas.style.height = '100%';
        }

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

    // ========================================================================
    // Image loading (new flow — image becomes the captured frame directly)
    // ========================================================================

    loadImage(file) {
        // Validate file size (20MB limit for images)
        const maxSize = 20 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showUploadStatus('❌ La imagen es demasiado grande (máximo 20MB)', 'error');
            return;
        }

        this.mediaType = 'image';
        this.currentVideoFile = file;

        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                // Draw onto a canvas to get a consistent base64 frame
                const canvas = document.createElement('canvas');
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);

                this.capturedFrame = canvas.toDataURL('image/png');

                console.log('🖼️ Image loaded as frame:', img.naturalWidth, 'x', img.naturalHeight);
                console.log('   - Frame size (base64):', (this.capturedFrame.length / 1024).toFixed(2), 'KB');

                // Show player section but adapt UI for image mode
                this.playerSection.style.display = 'block';

                // Hide video element & video-only controls
                this.videoPlayer.style.display = 'none';
                this.playPauseBtn.style.display = 'none';
                this.captureBtn.style.display = 'none';

                // Make the ROI canvas position:relative so it defines the
                // container height (normally it's position:absolute overlaying the <video>).
                const roiCanvas = document.getElementById('roiCanvas');
                if (roiCanvas) {
                    roiCanvas.style.position = 'relative';
                    roiCanvas.style.display = 'block';
                    roiCanvas.style.maxWidth = '100%';
                    roiCanvas.style.height = 'auto';
                }

                // Feed directly into the ROI selector (which displays the frame)
                if (window.roiSelector) {
                    window.roiSelector.setFrame(this.capturedFrame, img.naturalWidth, img.naturalHeight);
                    console.log('✅ ROI selector updated with image');
                }

                // Notify multi-frame analyzer
                if (window.multiFrameAnalyzer) {
                    window.multiFrameAnalyzer.setCurrentFrame(this.capturedFrame);
                }

                // Enable analyze button directly — no capture step needed
                if (this.analyzeBtn) {
                    this.analyzeBtn.disabled = false;
                }

                const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                this.showUploadStatus(`✅ Imagen cargada: ${file.name} (${sizeMB} MB) — lista para analizar`, 'success');
            };

            img.onerror = () => {
                this.showUploadStatus('❌ No se pudo cargar la imagen. Formato no soportado.', 'error');
            };

            img.src = e.target.result;
        };

        reader.readAsDataURL(file);
    }

    // ========================================================================
    // Playback & capture
    // ========================================================================

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
