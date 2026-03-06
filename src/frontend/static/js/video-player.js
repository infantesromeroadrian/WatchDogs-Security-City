/**
 * Video / Image Player Controller
 * Handles video & image upload, playback controls, and frame capture.
 *
 * Images are loaded directly as a captured frame — no manual capture step needed.
 */

// L-2: Use global logger (set by modules/logger.js via window.__wdLog)
const log = window.__wdLog || console;

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
        /** @type {string|null} H-9: Track Object URL for proper revocation */
        this._currentObjectURL = null;
        /** @type {boolean} Prevent infinite transcode loop on repeated errors */
        this._transcodeAttempted = false;
        /** @type {boolean} Suppress error handler while swapping video source */
        this._isSwappingSource = false;

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
            log.info('Video loaded successfully');
        });

        // Handle unsupported codecs / corrupt files — auto-transcode to H.264
        this.videoPlayer.addEventListener('error', () => {
            // Ignore transient errors while swapping source (e.g. during transcodeAndReload)
            if (this._isSwappingSource) {
                log.debug('Ignoring transient video error during source swap');
                return;
            }
            const err = this.videoPlayer.error;
            const code = err ? err.code : 0;
            // MediaError codes: 1=ABORTED, 2=NETWORK, 3=DECODE, 4=SRC_NOT_SUPPORTED
            if ((code === 4 || code === 3) && this.currentVideoFile && !this._transcodeAttempted) {
                log.warn('Video codec not supported by browser (code:', code, ') — requesting server transcode');
                this._transcodeAttempted = true;
                this.transcodeAndReload(this.currentVideoFile);
            } else if (code === 4 || code === 3) {
                // Already attempted transcoding or no file available
                log.error('Video still unplayable after transcode attempt, code:', code);
                this.showUploadStatus(
                    '❌ No se pudo reproducir el video. Prueba con otro archivo o sube una imagen.',
                    'error'
                );
            } else {
                log.error('Video player error, code:', code, err?.message);
                this.showUploadStatus('❌ Error al cargar el video.', 'error');
            }
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
        this._transcodeAttempted = false; // Reset for each new video

        // Restore video element & controls (may have been hidden by image mode)
        this.videoPlayer.style.display = 'block';
        this.playPauseBtn.style.display = '';
        this.captureBtn.style.display = '';
        this.captureBtn.disabled = true;
        if (this.analyzeBtn) this.analyzeBtn.disabled = true;

        // Restore ROI canvas to absolute overlay mode
        const roiCanvas = document.getElementById('roiCanvas');
        if (roiCanvas) {
            roiCanvas.style.position = 'absolute';
            roiCanvas.style.maxWidth = '';
            roiCanvas.style.height = '100%';
        }

        // H-9: Revoke previous Object URL before creating a new one (prevent memory leak)
        if (this._currentObjectURL) {
            URL.revokeObjectURL(this._currentObjectURL);
            this._currentObjectURL = null;
        }

        // Create object URL for video
        const videoURL = URL.createObjectURL(file);
        this._currentObjectURL = videoURL;
        this.videoPlayer.src = videoURL;

        // Show player section
        this.playerSection.style.display = 'block';

        // Update status
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        this.showUploadStatus(`✅ Video cargado: ${file.name} (${sizeMB} MB)`, 'success');
        log.debug('Video loaded:', file.name);
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

        // H-9: Revoke previous Object URL when switching to image mode
        if (this._currentObjectURL) {
            URL.revokeObjectURL(this._currentObjectURL);
            this._currentObjectURL = null;
        }

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

                log.debug('Image loaded as frame:', img.naturalWidth, 'x', img.naturalHeight, '— base64:', (this.capturedFrame.length / 1024).toFixed(2), 'KB');

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
                    log.debug('ROI selector updated with image');
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
    // Server-side transcoding (H.265/VP9 → H.264)
    // ========================================================================

    /**
     * Upload the video to the server for transcoding to H.264 and reload it.
     * Uses XMLHttpRequest for upload progress feedback.
     * @param {File} file - The original video file the browser can't decode
     */
    transcodeAndReload(file) {
        // Hide the video element so the ugly native error message is not visible
        // while uploading + transcoding. It will be shown again on success.
        this.videoPlayer.style.display = 'none';
        this.showUploadStatus('⏳ Codec incompatible detectado. Subiendo para transcodificar...', 'info');

        const formData = new FormData();
        formData.append('video', file);

        const xhr = new XMLHttpRequest();

        // --- Upload progress ---
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const pct = Math.round((e.loaded / e.total) * 100);
                this.showUploadStatus(`⏳ Subiendo video: ${pct}%`, 'info');
            }
        });

        // --- Upload complete → now server is transcoding ---
        xhr.upload.addEventListener('load', () => {
            this.showUploadStatus('⏳ Transcodificando a H.264 (puede tardar 1-2 min)...', 'info');
        });

        // --- Server response ---
        xhr.addEventListener('load', () => {
            try {
                const data = JSON.parse(xhr.responseText);

                if (xhr.status === 200 && data.success && data.video_url) {
                    // Revoke the old Object URL
                    if (this._currentObjectURL) {
                        URL.revokeObjectURL(this._currentObjectURL);
                        this._currentObjectURL = null;
                    }

                    // Suppress error handler while swapping to transcoded source
                    this._isSwappingSource = true;

                    // Listen for metadata on the transcoded video (one-time)
                    this.videoPlayer.addEventListener('loadedmetadata', () => {
                        this._isSwappingSource = false;
                        this.captureBtn.disabled = false;
                        log.info(
                            'Transcoded video ready:',
                            this.videoPlayer.videoWidth, 'x', this.videoPlayer.videoHeight
                        );
                    }, { once: true });

                    // Also clear the flag on error so we don't stay stuck
                    this.videoPlayer.addEventListener('error', () => {
                        this._isSwappingSource = false;
                    }, { once: true });

                    // Load the transcoded video from the server
                    this.videoPlayer.src = data.video_url;
                    this.videoPlayer.load();

                    // Make sure player section and controls are visible
                    this.playerSection.style.display = 'block';
                    this.videoPlayer.style.display = 'block';
                    this.playPauseBtn.style.display = '';
                    this.captureBtn.style.display = '';

                    // Restore ROI canvas to absolute overlay mode
                    const roiCanvas = document.getElementById('roiCanvas');
                    if (roiCanvas) {
                        roiCanvas.style.position = 'absolute';
                        roiCanvas.style.maxWidth = '';
                        roiCanvas.style.height = '100%';
                    }

                    const codec = data.original_codec || 'desconocido';
                    this.showUploadStatus(
                        `✅ Video transcodificado (${codec} → H.264). Listo para capturar y analizar.`,
                        'success'
                    );
                    log.info('Transcode complete:', data);
                } else {
                    const errMsg = data.error || 'Error desconocido';
                    log.error('Transcode response error:', errMsg);
                    this.showUploadStatus(`❌ Transcodificacion fallida: ${errMsg}`, 'error');
                }
            } catch (parseErr) {
                log.error('Failed to parse transcode response:', parseErr);
                this.showUploadStatus('❌ Respuesta inesperada del servidor.', 'error');
            }
        });

        // --- Network error ---
        xhr.addEventListener('error', () => {
            log.error('Transcode XHR network error');
            this.showUploadStatus(
                '❌ Error de red al transcodificar. Prueba con un video H.264 MP4 o sube una imagen.',
                'error'
            );
        });

        // --- Timeout ---
        xhr.addEventListener('timeout', () => {
            log.error('Transcode XHR timed out');
            this.showUploadStatus(
                '❌ Timeout al transcodificar. El video puede ser demasiado grande.',
                'error'
            );
        });

        xhr.open('POST', '/api/transcode-video');
        xhr.timeout = 360000; // 6 min client-side (> server's 5 min ffmpeg timeout)
        xhr.send(formData);
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
            log.error('CRITICAL: Frame capture failed!');
            alert('❌ Error al capturar el frame. Intenta nuevamente.');
            return;
        }

        log.debug('Frame captured:', canvas.width, 'x', canvas.height, '— base64:', (this.capturedFrame.length / 1024).toFixed(2), 'KB');

        // Initialize ROI selector with captured frame
        if (window.roiSelector) {
            window.roiSelector.setFrame(this.capturedFrame, canvas.width, canvas.height);
            log.debug('ROI selector updated with frame');
        }

        // Notify multi-frame analyzer
        if (window.multiFrameAnalyzer) {
            window.multiFrameAnalyzer.setCurrentFrame(this.capturedFrame);
            log.debug('Multi-frame analyzer updated with frame');
        }

        // Show success feedback
        this.captureBtn.textContent = '✅ Frame Capturado';
        setTimeout(() => {
            this.captureBtn.textContent = '📸 Capturar Frame';
        }, 2000);
    }

    getCapturedFrame() {
        if (!this.capturedFrame) {
            log.warn('getCapturedFrame called but no frame captured');
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
