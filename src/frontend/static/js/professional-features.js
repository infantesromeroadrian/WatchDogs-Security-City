/**
 * Professional OSINT Features - Main Orchestrator (Refactored)
 * Coordinates metadata extraction, PDF generation, and evidence packages
 */

import { MetadataHandler } from './modules/professional/metadata-handler.js';
import { PDFGenerator } from './modules/professional/pdf-generator.js';
import { EvidenceHandler } from './modules/professional/evidence-handler.js';

class ProfessionalFeatures {
    constructor() {
        this.baseURL = window.location.origin + '/api';
        
        // Initialize specialized modules
        this.metadataHandler = new MetadataHandler(
            this.baseURL,
            this.showToast.bind(this)
        );
        
        this.pdfGenerator = new PDFGenerator(
            this.baseURL,
            this.showToast.bind(this),
            this.metadataHandler
        );
        
        this.evidenceHandler = new EvidenceHandler(
            this.baseURL,
            this.showToast.bind(this),
            this.createMetadataRow.bind(this)
        );
        
        console.log('✅ Professional features initialized (modular)');
    }
    
    enableButtons() {
        this.metadataHandler.enable();
        this.pdfGenerator.enable();
        this.evidenceHandler.enable();
        console.log('✅ Professional features enabled');
    }
    
    // Shared utility: create metadata row HTML
    createMetadataRow(label, value) {
        return `
            <div class="metadata-row">
                <div class="metadata-label">${label}:</div>
                <div class="metadata-value">${value}</div>
            </div>
        `;
    }
    
    // Shared utility: show toast notification
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.whiteSpace = 'pre-line'; // Support multiline messages
        
        toastContainer.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Auto-remove after delay
        const duration = type === 'error' ? 5000 : 3000;
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(container);
        return container;
    }
    
    // Public method to download evidence JSON (called from HTML onclick)
    downloadEvidenceJSON() {
        this.evidenceHandler.downloadJSON();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.professionalFeatures = new ProfessionalFeatures();
    console.log('✅ Professional features module loaded');
});
