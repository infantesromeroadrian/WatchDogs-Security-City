/**
 * PDF Generator Module
 * Handles PDF report generation
 */

export class PDFGenerator {
    constructor(baseURL, showToast, metadataHandler) {
        this.baseURL = baseURL;
        this.showToast = showToast;
        this.metadataHandler = metadataHandler;
        
        this.generatePdfBtn = document.getElementById('generatePdfBtn');
        this.bindEvents();
    }
    
    bindEvents() {
        this.generatePdfBtn?.addEventListener('click', () => this.generate());
    }
    
    async generate(evidenceId = null) {
        try {
            const analysisResults = window.apiClient?.lastResults;
            
            if (!analysisResults) {
                this.showToast(
                    '⚠️ No hay resultados de análisis disponibles. Por favor:\n' +
                    '1️⃣ Captura un frame del video (📸 Capturar Frame)\n' +
                    '2️⃣ Analiza el frame (🔍 Analizar Frame)\n' +
                    '3️⃣ Luego genera el reporte PDF',
                    'warning'
                );
                return;
            }
            
            this.generatePdfBtn.disabled = true;
            this.generatePdfBtn.textContent = '⏳ Generating PDF...';
            
            const payload = {
                analysis_results: analysisResults,
                metadata: this.metadataHandler.currentMetadata,
                evidence_id: evidenceId
            };
            
            const response = await fetch(`${this.baseURL}/generate-pdf-report`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
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
            
        } catch (error) {
            console.error('❌ PDF generation error:', error);
            this.showToast(`❌ Error: ${error.message}`, 'error');
        } finally {
            this.generatePdfBtn.disabled = false;
            this.generatePdfBtn.textContent = '📄 Generate PDF Report';
        }
    }
    
    enable() {
        if (this.generatePdfBtn) this.generatePdfBtn.disabled = false;
    }
}
