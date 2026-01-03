/**
 * Professional OSINT Features Module
 * Handles metadata extraction, PDF generation, and evidence packages
 */

class ProfessionalFeatures {
    constructor() {
        this.baseURL = window.location.origin + '/api';
        this.currentMetadata = null;
        this.currentEvidencePackage = null;
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        this.extractMetadataBtn = document.getElementById('extractMetadataBtn');
        this.generatePdfBtn = document.getElementById('generatePdfBtn');
        this.generateEvidenceBtn = document.getElementById('generateEvidenceBtn');
        this.metadataPanel = document.getElementById('metadataPanel');
        this.metadataContent = document.getElementById('metadataContent');
        this.evidencePanel = document.getElementById('evidencePanel');
        this.evidenceContent = document.getElementById('evidenceContent');
    }
    
    bindEvents() {
        this.extractMetadataBtn?.addEventListener('click', () => this.extractMetadata());
        this.generatePdfBtn?.addEventListener('click', () => this.generatePDF());
        this.generateEvidenceBtn?.addEventListener('click', () => this.generateEvidence());
    }
    
    enableButtons() {
        if (this.extractMetadataBtn) this.extractMetadataBtn.disabled = false;
        if (this.generatePdfBtn) this.generatePdfBtn.disabled = false;
        if (this.generateEvidenceBtn) this.generateEvidenceBtn.disabled = false;
        
        console.log('✅ Professional features enabled');
    }
    
    async extractMetadata() {
        try {
            // Get current frame from apiClient
            const frame = window.apiClient.currentFrame;
            
            if (!frame) {
                this.showToast('⚠️ No frame available. Analyze an image first.', 'warning');
                return;
            }
            
            console.log('📊 Extracting metadata...');
            this.extractMetadataBtn.disabled = true;
            this.extractMetadataBtn.textContent = '⏳ Extracting...';
            
            const response = await fetch(`${this.baseURL}/extract-metadata`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({frame: frame})
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Metadata extraction failed');
            }
            
            this.currentMetadata = data.metadata;
            this.displayMetadata(data.metadata);
            this.showToast('✅ Metadata extracted successfully!', 'success');
            
            console.log('✅ Metadata extracted:', data.metadata);
            
        } catch (error) {
            console.error('❌ Metadata extraction error:', error);
            this.showToast(`❌ Error: ${error.message}`, 'error');
        } finally {
            this.extractMetadataBtn.disabled = false;
            this.extractMetadataBtn.textContent = '📊 Extract Metadata';
        }
    }
    
    displayMetadata(metadata) {
        this.metadataPanel.style.display = 'block';
        
        let html = '';
        
        // Technical Info
        if (metadata.technical) {
            html += '<div style="margin-bottom: 15px;">';
            html += '<h5 style="color: #00d2ff; margin-bottom: 8px;">🖼️ Technical Specifications</h5>';
            html += this.createMetadataRow('Format', metadata.technical.format || 'N/A');
            html += this.createMetadataRow('Dimensions', metadata.technical.size || 'N/A');
            html += this.createMetadataRow('Color Mode', metadata.technical.mode || 'N/A');
            html += this.createMetadataRow('File Size', this.formatBytes(metadata.forensics?.size_bytes || 0));
            html += '</div>';
        }
        
        // GPS Coordinates
        if (metadata.gps && Object.keys(metadata.gps).length > 0) {
            html += '<div class="gps-coordinates">';
            html += '<h5 style="color: #00ff64; margin-bottom: 8px;">📍 GPS Coordinates</h5>';
            html += this.createMetadataRow('Latitude', metadata.gps.latitude?.toFixed(6) || 'N/A');
            html += this.createMetadataRow('Longitude', metadata.gps.longitude?.toFixed(6) || 'N/A');
            if (metadata.gps.altitude) {
                html += this.createMetadataRow('Altitude', `${metadata.gps.altitude.toFixed(2)} m`);
            }
            if (metadata.gps.date) {
                html += this.createMetadataRow('GPS Date', metadata.gps.date);
            }
            
            // Google Maps link
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
            html += '<h5 style="color: #00d2ff; margin-bottom: 8px;">📷 Camera Information</h5>';
            html += this.createMetadataRow('Make', metadata.exif.camera.make || 'N/A');
            html += this.createMetadataRow('Model', metadata.exif.camera.model || 'N/A');
            if (metadata.exif.camera.software) {
                html += this.createMetadataRow('Software', metadata.exif.camera.software);
            }
            html += '</div>';
        }
        
        // Datetime
        if (metadata.exif?.datetime && Object.keys(metadata.exif.datetime).length > 0) {
            html += '<div style="margin-bottom: 15px;">';
            html += '<h5 style="color: #00d2ff; margin-bottom: 8px;">🕐 Timestamps</h5>';
            if (metadata.exif.datetime.original) {
                html += this.createMetadataRow('Original', metadata.exif.datetime.original);
            }
            if (metadata.exif.datetime.digitized) {
                html += this.createMetadataRow('Digitized', metadata.exif.datetime.digitized);
            }
            html += '</div>';
        }
        
        // Forensic Hashes
        if (metadata.forensics) {
            html += '<div class="forensic-hash">';
            html += '<h5 style="color: #ff6464; margin-bottom: 8px;">🔒 Forensic Hashes</h5>';
            html += this.createMetadataRow('SHA-256', metadata.forensics.sha256 || 'N/A');
            html += this.createMetadataRow('MD5', metadata.forensics.md5 || 'N/A');
            html += '<p style="font-size: 0.85rem; color: #aaa; margin-top: 10px;">These hashes can be used to verify file integrity and authenticity.</p>';
            html += '</div>';
        }
        
        this.metadataContent.innerHTML = html;
        
        // Scroll to metadata panel
        this.metadataPanel.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }
    
    createMetadataRow(label, value) {
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
    
    async generatePDF() {
        try {
            // Get analysis results from apiClient
            const analysisResults = window.apiClient.lastResults;
            
            if (!analysisResults) {
                this.showToast('⚠️ No analysis results. Analyze an image first.', 'warning');
                return;
            }
            
            console.log('📄 Generating PDF report...');
            this.generatePdfBtn.disabled = true;
            this.generatePdfBtn.textContent = '⏳ Generating PDF...';
            
            const payload = {
                analysis_results: analysisResults,
                metadata: this.currentMetadata,
                evidence_id: this.currentEvidencePackage?.evidence_id
            };
            
            const response = await fetch(`${this.baseURL}/generate-pdf-report`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            // Download PDF
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
            a.download = `watchdogs_report_${timestamp}.pdf`;
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showToast('✅ PDF report downloaded!', 'success');
            console.log('✅ PDF generated and downloaded');
            
        } catch (error) {
            console.error('❌ PDF generation error:', error);
            this.showToast(`❌ Error: ${error.message}`, 'error');
        } finally {
            this.generatePdfBtn.disabled = false;
            this.generatePdfBtn.textContent = '📄 Generate PDF Report';
        }
    }
    
    async generateEvidence() {
        try {
            // Get frame and analysis results
            const frame = window.apiClient.currentFrame;
            const analysisResults = window.apiClient.lastResults;
            
            if (!frame || !analysisResults) {
                this.showToast('⚠️ No frame or analysis results available.', 'warning');
                return;
            }
            
            console.log('📦 Generating evidence package...');
            this.generateEvidenceBtn.disabled = true;
            this.generateEvidenceBtn.textContent = '⏳ Generating...';
            
            const response = await fetch(`${this.baseURL}/generate-evidence-package`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    frame: frame,
                    analysis_results: analysisResults
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Evidence package generation failed');
            }
            
            this.currentEvidencePackage = data.evidence_package;
            this.displayEvidencePackage(data.evidence_package);
            this.showToast('✅ Evidence package generated!', 'success');
            
            console.log('✅ Evidence package created:', data.evidence_package.evidence_id);
            
        } catch (error) {
            console.error('❌ Evidence package error:', error);
            this.showToast(`❌ Error: ${error.message}`, 'error');
        } finally {
            this.generateEvidenceBtn.disabled = false;
            this.generateEvidenceBtn.textContent = '📦 Evidence Package';
        }
    }
    
    displayEvidencePackage(evidence) {
        this.evidencePanel.style.display = 'block';
        
        let html = '';
        
        // Evidence ID
        html += `<div class="evidence-id">Evidence ID: ${evidence.evidence_id}</div>`;
        
        // Timestamp
        html += '<div style="margin-bottom: 15px;">';
        html += this.createMetadataRow('Generated', new Date(evidence.timestamp).toLocaleString());
        html += '</div>';
        
        // Chain of Custody
        if (evidence.chain_of_custody) {
            html += '<div style="margin-bottom: 15px;">';
            html += '<h5 style="color: #ff6464; margin-bottom: 8px;">🔗 Chain of Custody</h5>';
            evidence.chain_of_custody.forEach((entry, i) => {
                html += `<div style="padding: 8px; background: rgba(255,255,255,0.05); margin-bottom: 5px; border-radius: 3px;">`;
                html += `<strong>${i + 1}. ${entry.action.toUpperCase()}</strong><br/>`;
                html += `<small>Timestamp: ${new Date(entry.timestamp).toLocaleString()}</small><br/>`;
                if (entry.system) html += `<small>System: ${entry.system}</small><br/>`;
                if (entry.hash) html += `<small>Hash: ${entry.hash.substring(0, 16)}...</small>`;
                html += `</div>`;
            });
            html += '</div>';
        }
        
        // Integrity
        if (evidence.integrity) {
            html += '<div style="margin-bottom: 15px;">';
            html += '<h5 style="color: #ff6464; margin-bottom: 8px;">✓ Integrity Verification</h5>';
            html += this.createMetadataRow('SHA-256', evidence.integrity.sha256);
            html += this.createMetadataRow('Verified', evidence.integrity.verified ? '✅ Yes' : '❌ No');
            html += '</div>';
        }
        
        // Download JSON button
        html += '<div style="margin-top: 15px;">';
        html += `<button class="btn btn-secondary" onclick="professionalFeatures.downloadEvidenceJSON()" style="width: 100%;">💾 Download Evidence Package (JSON)</button>`;
        html += '</div>';
        
        this.evidenceContent.innerHTML = html;
        
        // Scroll to evidence panel
        this.evidencePanel.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }
    
    downloadEvidenceJSON() {
        if (!this.currentEvidencePackage) return;
        
        const json = JSON.stringify(this.currentEvidencePackage, null, 2);
        const blob = new Blob([json], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `evidence_${this.currentEvidencePackage.evidence_id}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showToast('✅ Evidence package downloaded!', 'success');
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        
        // Color based on type
        if (type === 'error') {
            toast.style.background = 'linear-gradient(45deg, #ff6b6b, #ee5a6f)';
        } else if (type === 'warning') {
            toast.style.background = 'linear-gradient(45deg, #ffa500, #ff8c00)';
        } else if (type === 'success') {
            toast.style.background = 'linear-gradient(45deg, #00ff64, #00d9ff)';
        }
        
        document.body.appendChild(toast);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.professionalFeatures = new ProfessionalFeatures();
    console.log('✅ Professional features module loaded');
});
