/**
 * Evidence Handler Module
 * Handles evidence package generation and display
 */

import { log } from '../logger.js';

export class EvidenceHandler {
    constructor(baseURL, showToast, createMetadataRow) {
        this.baseURL = baseURL;
        this.showToast = showToast;
        this.createMetadataRow = createMetadataRow;
        this.currentEvidencePackage = null;
        
        this.generateEvidenceBtn = document.getElementById('generateEvidenceBtn');
        this.evidencePanel = document.getElementById('evidencePanel');
        this.evidenceContent = document.getElementById('evidenceContent');
        
        this.bindEvents();
    }
    
    bindEvents() {
        this.generateEvidenceBtn?.addEventListener('click', () => this.generate());
    }
    
    async generate() {
        try {
            const frame = window.apiClient?.currentFrame;
            const analysisResults = window.apiClient?.lastResults;
            
            if (!frame || !analysisResults) {
                this.showToast(
                    '⚠️ No hay frame o resultados de análisis disponibles. Por favor:\n' +
                    '1️⃣ Captura un frame del video (📸 Capturar Frame)\n' +
                    '2️⃣ Analiza el frame (🔍 Analizar Frame)\n' +
                    '3️⃣ Luego genera el paquete de evidencia',
                    'warning'
                );
                return;
            }
            
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
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            if (!data.success) throw new Error(data.error || 'Evidence package generation failed');
            
            this.currentEvidencePackage = data.evidence_package;
            this.display(data.evidence_package);
            this.showToast('✅ Evidence package generated!', 'success');
            
        } catch (error) {
            log.error('Evidence package error:', error);
            this.showToast(`❌ Error: ${error.message}`, 'error');
        } finally {
            this.generateEvidenceBtn.disabled = false;
            this.generateEvidenceBtn.textContent = '📦 Evidence Package';
        }
    }
    
    display(evidence) {
        this.evidencePanel.style.display = 'block';
        let html = '';
        
        html += `<div class="evidence-id">Evidence ID: ${evidence.evidence_id}</div>`;
        
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
        
        html += '<div style="margin-top: 15px;">';
        html += `<button class="btn btn-secondary" onclick="professionalFeatures.downloadEvidenceJSON()" style="width: 100%;">💾 Download Evidence Package (JSON)</button>`;
        html += '</div>';
        
        this.evidenceContent.innerHTML = html;
        this.evidencePanel.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }
    
    downloadJSON() {
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
    
    getEvidenceId() {
        return this.currentEvidencePackage?.evidence_id || null;
    }
    
    enable() {
        if (this.generateEvidenceBtn) this.generateEvidenceBtn.disabled = false;
    }
}
