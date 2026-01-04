/**
 * Metadata Handler Module
 * Handles metadata extraction and display
 */

export class MetadataHandler {
    constructor(baseURL, showToast) {
        this.baseURL = baseURL;
        this.showToast = showToast;
        this.currentMetadata = null;
        
        this.extractMetadataBtn = document.getElementById('extractMetadataBtn');
        this.metadataPanel = document.getElementById('metadataPanel');
        this.metadataContent = document.getElementById('metadataContent');
        
        this.bindEvents();
    }
    
    bindEvents() {
        this.extractMetadataBtn?.addEventListener('click', () => this.extract());
    }
    
    async extract() {
        try {
            const frame = window.apiClient?.currentFrame;
            
            if (!frame) {
                this.showToast(
                    '⚠️ No hay frame disponible. Por favor:\n' +
                    '1️⃣ Captura un frame del video (📸 Capturar Frame)\n' +
                    '2️⃣ Analiza el frame (🔍 Analizar Frame)\n' +
                    '3️⃣ Luego extrae metadata',
                    'warning'
                );
                return;
            }
            
            this.extractMetadataBtn.disabled = true;
            this.extractMetadataBtn.textContent = '⏳ Extracting...';
            
            const response = await fetch(`${this.baseURL}/extract-metadata`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({frame: frame})
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            if (!data.success) throw new Error(data.error || 'Metadata extraction failed');
            
            this.currentMetadata = data.metadata;
            this.display(data.metadata);
            this.showToast('✅ Metadata extracted successfully!', 'success');
            
        } catch (error) {
            console.error('❌ Metadata extraction error:', error);
            this.showToast(`❌ Error: ${error.message}`, 'error');
        } finally {
            this.extractMetadataBtn.disabled = false;
            this.extractMetadataBtn.textContent = '📊 Extract Metadata';
        }
    }
    
    display(metadata) {
        this.metadataPanel.style.display = 'block';
        let html = '';
        
        // Technical Info
        if (metadata.technical) {
            html += '<div style="margin-bottom: 15px;">';
            html += '<h5 style="color: #00d2ff; margin-bottom: 8px;">🖼️ Technical Specifications</h5>';
            html += this.createRow('Format', metadata.technical.format || 'N/A');
            html += this.createRow('Dimensions', metadata.technical.size || 'N/A');
            html += this.createRow('Color Mode', metadata.technical.mode || 'N/A');
            html += this.createRow('File Size', this.formatBytes(metadata.forensics?.size_bytes || 0));
            html += '</div>';
        }
        
        // GPS Coordinates
        if (metadata.gps && Object.keys(metadata.gps).length > 0) {
            html += '<div class="gps-coordinates">';
            html += '<h5 style="color: #00ff64; margin-bottom: 8px;">📍 GPS Coordinates</h5>';
            html += this.createRow('Latitude', metadata.gps.latitude?.toFixed(6) || 'N/A');
            html += this.createRow('Longitude', metadata.gps.longitude?.toFixed(6) || 'N/A');
            if (metadata.gps.altitude) {
                html += this.createRow('Altitude', `${metadata.gps.altitude.toFixed(2)} m`);
            }
            if (metadata.gps.date) {
                html += this.createRow('GPS Date', metadata.gps.date);
            }
            
            if (metadata.gps.latitude && metadata.gps.longitude) {
                const mapsUrl = `https://www.google.com/maps?q=${metadata.gps.latitude},${metadata.gps.longitude}`;
                html += `<div style="margin-top: 10px;">`;
                html += `<a href="${mapsUrl}" target="_blank" style="color: #00ff64; text-decoration: underline;">📍 Open in Google Maps</a>`;
                html += `</div>`;
            }
            html += '</div>';
        }
        
        // Camera Info
        if (metadata.exif?.camera && Object.keys(metadata.exif.camera).length > 0) {
            html += '<div style="margin-bottom: 15px;">';
            html += '<h5 style="color: #ffcc00; margin-bottom: 8px;">📷 Camera Information</h5>';
            const cam = metadata.exif.camera;
            if (cam.make) html += this.createRow('Make', cam.make);
            if (cam.model) html += this.createRow('Model', cam.model);
            if (cam.software) html += this.createRow('Software', cam.software);
            html += '</div>';
        }
        
        // Photo Settings
        if (metadata.exif?.photo && Object.keys(metadata.exif.photo).length > 0) {
            html += '<div style="margin-bottom: 15px;">';
            html += '<h5 style="color: #ff6b6b; margin-bottom: 8px;">⚙️ Photo Settings</h5>';
            const photo = metadata.exif.photo;
            if (photo.datetime) html += this.createRow('Date/Time', photo.datetime);
            if (photo.exposure_time) html += this.createRow('Exposure', photo.exposure_time);
            if (photo.f_number) html += this.createRow('F-Number', `f/${photo.f_number}`);
            if (photo.iso) html += this.createRow('ISO', photo.iso);
            if (photo.focal_length) html += this.createRow('Focal Length', `${photo.focal_length} mm`);
            html += '</div>';
        }
        
        // Forensics
        if (metadata.forensics) {
            html += '<div style="margin-bottom: 15px;">';
            html += '<h5 style="color: #ff4444; margin-bottom: 8px;">🔬 Forensic Analysis</h5>';
            const foren = metadata.forensics;
            if (foren.md5) html += this.createRow('MD5 Hash', `<code>${foren.md5}</code>`);
            if (foren.sha256) html += this.createRow('SHA256 Hash', `<code style="font-size: 10px;">${foren.sha256}</code>`);
            html += '</div>';
        }
        
        this.metadataContent.innerHTML = html;
        this.metadataPanel.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }
    
    createRow(label, value) {
        return `
            <div class="metadata-row">
                <div class="metadata-label">${label}:</div>
                <div class="metadata-value">${value}</div>
            </div>
        `;
    }
    
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }
    
    enable() {
        if (this.extractMetadataBtn) this.extractMetadataBtn.disabled = false;
    }
}
