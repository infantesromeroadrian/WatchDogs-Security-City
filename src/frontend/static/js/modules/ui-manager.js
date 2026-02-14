/**
 * UI Manager Module
 * Handles all UI updates, displays, and user interactions
 * Updated for CIA-Level 7-Agent Dashboard
 */

export class UIManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        
        // DOM elements
        this.analysisSection = document.getElementById('analysisSection');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.textResults = document.getElementById('textResults');
        this.jsonResults = document.getElementById('jsonResults');
        this.previewCanvas = document.getElementById('previewCanvas');
        this.copyJsonBtn = document.getElementById('copyJsonBtn');
        this.downloadReportBtn = document.getElementById('downloadReportBtn');
        this.newAnalysisBtn = document.getElementById('newAnalysisBtn');
        
        // CIA Intel Dashboard elements
        this.intelSummary = document.getElementById('intelSummary');
        this.analysisStatus = document.getElementById('analysisStatus');
        this.summaryText = document.getElementById('summaryText');
        this.keyInferencesPanel = document.getElementById('keyInferencesPanel');
        this.inferencesList = document.getElementById('inferencesList');
        
        // Privacy elements
        this.privacyWarning = document.getElementById('privacyWarning');
        this.dismissPrivacyBtn = document.getElementById('dismissPrivacyWarning');
        this.privacyLearnMore = document.getElementById('privacyLearnMore');
        
        this.init();
    }
    
    init() {
        // Tab switching
        const tabs = document.querySelectorAll('.tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchTab(tab.dataset.tab);
            });
        });
        
        // Copy JSON button
        this.copyJsonBtn.addEventListener('click', () => {
            this.copyJSON();
        });
        
        // Download report button
        this.downloadReportBtn.addEventListener('click', () => {
            this.downloadReport();
        });
        
        // New analysis button
        this.newAnalysisBtn.addEventListener('click', () => {
            this.resetAnalysis();
        });
        
        // Privacy warning handlers
        if (this.dismissPrivacyBtn) {
            this.dismissPrivacyBtn.addEventListener('click', () => {
                this.dismissPrivacyWarning();
            });
        }
        
        if (this.privacyLearnMore) {
            this.privacyLearnMore.addEventListener('click', (e) => {
                e.preventDefault();
                this.showPrivacyInfo();
            });
        }
        
        // Check if user has previously dismissed the warning
        if (localStorage.getItem('watchdogs_privacy_warning_dismissed') === 'true') {
            this.privacyWarning?.classList.add('dismissed');
        }
    }
    
    dismissPrivacyWarning() {
        if (this.privacyWarning) {
            this.privacyWarning.classList.add('dismissed');
            localStorage.setItem('watchdogs_privacy_warning_dismissed', 'true');
        }
    }
    
    showPrivacyInfo() {
        const message = `
WatchDogs OSINT Privacy Information
====================================

This system performs CIA-level analysis that includes:

🔸 FACE ANALYSIS (GDPR Art. 9 - Special Category Data)
   - Analyzes facial features, demographics, distinctive marks
   - This constitutes biometric data processing
   - Requires explicit consent or legal basis

🔸 FORENSIC ANALYSIS
   - Analyzes image authenticity and manipulation
   - May reveal information about image editing history

🔸 CONTEXT INTELLIGENCE  
   - Infers temporal, cultural, socioeconomic information
   - May reveal sensitive contextual details

LEGAL REQUIREMENTS:
• Obtain explicit consent before analyzing images with identifiable persons
• Document your legal basis for processing (GDPR Art. 6)
• Implement appropriate data retention policies
• Provide subjects with access to their data upon request

To disable sensitive agents, set environment variables:
  FACE_ANALYSIS_ENABLED=False
  FORENSIC_ANALYSIS_ENABLED=False
  CONTEXT_INTEL_ENABLED=False
  PRIVACY_MODE=True (disables all)

For more information, consult your organization's Data Protection Officer.
        `.trim();
        
        alert(message);
    }
    
    showLoading() {
        this.analysisSection.style.display = 'block';
        this.loadingIndicator.style.display = 'block';
        this.resultsContainer.style.display = 'block';
        
        // Reset CIA Intel dashboard
        this.resetIntelDashboard();
        
        // Scroll to analysis section
        this.analysisSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    displayResults(results) {
        // Hide loading
        this.loadingIndicator.style.display = 'none';
        this.resultsContainer.style.display = 'block';
        
        // Display text report
        this.textResults.textContent = results.text || 'No text report available';
        
        // Display JSON report
        this.jsonResults.textContent = JSON.stringify(results.json, null, 2);
        
        // Display preview (captured frame with ROI)
        this.displayPreview();
        
        // Render CIA Intel Dashboard
        this.renderIntelDashboard(results.json);
    }
    
    // =========================================================================
    // CIA INTEL DASHBOARD RENDERING
    // =========================================================================
    
    resetIntelDashboard() {
        // Reset status
        if (this.analysisStatus) {
            this.analysisStatus.className = 'status-indicator processing';
            this.analysisStatus.textContent = '●';
        }
        if (this.summaryText) {
            this.summaryText.textContent = 'Analyzing with 7 CIA-level agents...';
        }
        
        // Reset all agent cards
        const agentIds = ['vision', 'ocr', 'detection', 'geolocation', 'faceAnalysis', 'forensicAnalysis', 'contextIntel'];
        agentIds.forEach(id => {
            const content = document.getElementById(`${id}Content`);
            if (content) {
                content.innerHTML = '<p class="placeholder">Awaiting analysis...</p>';
            }
        });
        
        // Hide key inferences
        if (this.keyInferencesPanel) {
            this.keyInferencesPanel.style.display = 'none';
        }
    }
    
    renderIntelDashboard(jsonData) {
        if (!jsonData || !jsonData.agents) {
            console.warn('No agent data in results');
            return;
        }
        
        const agents = jsonData.agents;
        
        // Update summary status
        this.updateSummaryStatus(agents);
        
        // Render each agent card
        this.renderVisionCard(agents.vision);
        this.renderOCRCard(agents.ocr);
        this.renderDetectionCard(agents.detection);
        this.renderGeolocationCard(agents.geolocation);
        this.renderFaceAnalysisCard(agents.face_analysis);
        this.renderForensicAnalysisCard(agents.forensic_analysis);
        this.renderContextIntelCard(agents.context_intel);
        
        // Render key inferences from context_intel
        this.renderKeyInferences(agents.context_intel);
        
        console.log('📊 CIA Intel Dashboard rendered with 7 agents');
    }

    updateAgentCard(agentName, result) {
        /**
         * Update a single agent card when its SSE event arrives.
         * Called progressively as each agent completes.
         */
        if (!result) return;

        // Map agent names to render methods
        const renderMap = {
            vision: data => this.renderVisionCard(data),
            ocr: data => this.renderOCRCard(data),
            detection: data => this.renderDetectionCard(data),
            geolocation: data => this.renderGeolocationCard(data),
            face_analysis: data => this.renderFaceAnalysisCard(data),
            forensic_analysis: data => this.renderForensicAnalysisCard(data),
            context_intel: data => this.renderContextIntelCard(data)
        };

        const renderer = renderMap[agentName];
        if (renderer) {
            renderer(result);
            console.log(`Agent card updated: ${agentName}`);
        } else {
            console.warn(`Unknown agent: ${agentName}`);
        }

        // Update key inferences if context_intel just completed
        if (agentName === 'context_intel') {
            this.renderKeyInferences(result);
        }

        const agentIds = [
            'visionContent',
            'ocrContent',
            'detectionContent',
            'geolocationContent',
            'faceAnalysisContent',
            'forensicAnalysisContent',
            'contextIntelContent'
        ];
        const totalCount = agentIds.length;
        const completedCount = agentIds.filter(id => {
            const content = document.getElementById(id);
            if (!content) return false;
            return !(content.innerHTML || '').includes('Awaiting analysis...');
        }).length;

        if (this.analysisStatus) {
            this.analysisStatus.className = completedCount === totalCount
                ? 'status-indicator success'
                : 'status-indicator processing';
        }

        if (this.summaryText) {
            this.summaryText.textContent = `Analysis in progress: ${completedCount}/${totalCount} agents completed`;
        }
    }
    
    updateSummaryStatus(agents) {
        const successCount = Object.values(agents).filter(a => a && a.status === 'success').length;
        const totalCount = Object.keys(agents).length;
        
        if (this.analysisStatus) {
            this.analysisStatus.className = successCount === totalCount 
                ? 'status-indicator success' 
                : 'status-indicator warning';
        }
        
        if (this.summaryText) {
            this.summaryText.textContent = `Analysis complete: ${successCount}/${totalCount} agents successful`;
        }
    }
    
    renderVisionCard(data) {
        const content = document.getElementById('visionContent');
        const badge = document.getElementById('visionConfidence');
        if (!content || !data) return;
        
        if (data.status === 'success') {
            content.innerHTML = `<p>${this.truncateText(data.analysis, 300)}</p>`;
            if (badge && data.confidence) {
                badge.textContent = data.confidence;
                badge.className = `confidence-badge ${this.getConfidenceClass(data.confidence)}`;
            }
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${data.error || 'Unknown error'}</p>`;
        }
    }
    
    renderOCRCard(data) {
        const content = document.getElementById('ocrContent');
        const badge = document.getElementById('ocrTextBadge');
        if (!content || !data) return;
        
        if (data.status === 'success') {
            const hasText = data.has_text;
            if (badge) {
                badge.textContent = hasText ? 'Text found' : 'No text';
                badge.className = `text-badge ${hasText ? 'has-text' : ''}`;
            }
            content.innerHTML = `<p>${this.truncateText(data.analysis, 300)}</p>`;
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${data.error || 'Unknown error'}</p>`;
        }
    }
    
    renderDetectionCard(data) {
        const content = document.getElementById('detectionContent');
        const badge = document.getElementById('detectionConfidence');
        if (!content || !data) return;
        
        if (data.status === 'success') {
            content.innerHTML = `<p>${this.truncateText(data.analysis, 300)}</p>`;
            if (badge && data.confidence) {
                badge.textContent = data.confidence;
                badge.className = `confidence-badge ${this.getConfidenceClass(data.confidence)}`;
            }
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${data.error || 'Unknown error'}</p>`;
        }
    }
    
    renderGeolocationCard(data) {
        const content = document.getElementById('geolocationContent');
        const badge = document.getElementById('geoConfidence');
        if (!content || !data) return;
        
        if (data.status === 'success') {
            const location = data.location || {};
            const city = location.city || 'Unknown';
            const country = location.country || 'Unknown';
            const region = location.region || '';
            
            let html = `
                <div class="location-display">
                    <div class="location-main">📍 ${city}, ${country}</div>
                    ${region ? `<div class="location-detail">${region}</div>` : ''}
                </div>
            `;
            
            // Add key clues
            const clues = data.key_clues || data.evidence_chain || [];
            if (clues.length > 0) {
                html += '<p><strong>Key Clues:</strong></p><ul>';
                clues.slice(0, 4).forEach(clue => {
                    const clueText = typeof clue === 'string' ? clue : clue.evidence || clue;
                    html += `<li>${this.truncateText(clueText, 80)}</li>`;
                });
                html += '</ul>';
            }
            
            content.innerHTML = html;
            
            if (badge && data.confidence) {
                badge.textContent = data.confidence;
                badge.className = `confidence-badge ${this.getConfidenceClass(data.confidence)}`;
            }
            
            // Emit location event for interactive map
            const coords = data.coordinates;
            if (coords && coords.lat != null && coords.lon != null) {
                window.dispatchEvent(new CustomEvent('watchdogs:location-found', {
                    detail: {
                        lat: coords.lat,
                        lon: coords.lon,
                        label: `${city}, ${country}`,
                        confidence_radius: coords.confidence_radius_meters,
                        source: 'analysis'
                    }
                }));
            }
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${data.error || 'Unknown error'}</p>`;
        }
    }
    
    renderFaceAnalysisCard(data) {
        const content = document.getElementById('faceAnalysisContent');
        const badge = document.getElementById('personCount');
        if (!content) return;
        
        if (!data || data.status === 'skipped') {
            content.innerHTML = '<p class="placeholder">Agent not executed</p>';
            return;
        }
        
        if (data.status === 'success') {
            const personCount = data.person_count || 0;
            const detection = data.detection_summary || {};
            
            if (badge) {
                badge.textContent = `${personCount} persons`;
            }
            
            let html = `
                <p><strong>Detected:</strong> ${personCount} person(s)</p>
                <p><strong>Faces visible:</strong> ${detection.faces_visible || 'N/A'}</p>
                <p><strong>ID Quality:</strong> ${detection.identification_quality || 'N/A'}</p>
            `;
            
            // Person summary chips
            const persons = data.persons || [];
            if (persons.length > 0) {
                html += '<div class="person-summary">';
                persons.slice(0, 4).forEach(person => {
                    const demo = person.demographics || {};
                    const age = demo.age_range || '?';
                    const gender = demo.gender || '?';
                    html += `<span class="person-chip">P${person.person_id}: ${age}, ${gender}</span>`;
                });
                html += '</div>';
            }
            
            // Distinctive features
            const features = data.most_distinctive_features || [];
            if (features.length > 0) {
                html += '<p><strong>Distinctive:</strong></p><ul>';
                features.slice(0, 3).forEach(f => {
                    html += `<li>${this.truncateText(f, 60)}</li>`;
                });
                html += '</ul>';
            }
            
            content.innerHTML = html;
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${data.error || 'Unknown error'}</p>`;
        }
    }
    
    renderForensicAnalysisCard(data) {
        const content = document.getElementById('forensicAnalysisContent');
        const badge = document.getElementById('integrityScore');
        if (!content) return;
        
        if (!data || data.status === 'skipped') {
            content.innerHTML = '<p class="placeholder">Agent not executed</p>';
            return;
        }
        
        if (data.status === 'success') {
            const verdict = data.verdict || {};
            const classification = verdict.classification || 'unknown';
            const integrity = data.integrity_score;
            
            // Determine verdict class
            const verdictClass = this.getVerdictClass(classification);
            
            if (badge) {
                badge.textContent = integrity !== null ? `${integrity}/100` : '-';
                badge.className = `integrity-badge ${verdictClass}`;
            }
            
            let html = `
                <div class="verdict-display ${verdictClass}">
                    <div class="verdict-text">${classification.toUpperCase()}</div>
                    ${integrity !== null ? `<div class="verdict-score">Integrity: ${integrity}/100</div>` : ''}
                </div>
            `;
            
            // Justification
            if (verdict.justification) {
                html += `<p><em>${this.truncateText(verdict.justification, 150)}</em></p>`;
            }
            
            // Anomalies summary
            const anomalies = data.anomalies || {};
            const anomalyCount = this.countAnomalies(anomalies);
            if (anomalyCount > 0) {
                html += `<p><strong>Anomalies detected:</strong> ${anomalyCount}</p>`;
            }
            
            // Recommendations
            const recs = data.recommendations || [];
            if (recs.length > 0) {
                html += '<p><strong>Recommendations:</strong></p><ul>';
                recs.slice(0, 2).forEach(r => {
                    html += `<li>${this.truncateText(r, 50)}</li>`;
                });
                html += '</ul>';
            }
            
            content.innerHTML = html;
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${data.error || 'Unknown error'}</p>`;
        }
    }
    
    renderContextIntelCard(data) {
        const content = document.getElementById('contextIntelContent');
        if (!content) return;
        
        if (!data || data.status === 'skipped') {
            content.innerHTML = '<p class="placeholder">Agent not executed</p>';
            return;
        }
        
        if (data.status === 'success') {
            let html = '';
            
            // Executive summary
            if (data.executive_summary) {
                html += `<p><em>${this.truncateText(data.executive_summary, 200)}</em></p>`;
            }
            
            // Temporal analysis grid
            const temporal = data.temporal_analysis || {};
            const temporalItems = [];
            
            if (temporal.time_of_day?.value) temporalItems.push({ label: 'Time', value: temporal.time_of_day.value });
            if (temporal.day_type?.value) temporalItems.push({ label: 'Day', value: temporal.day_type.value });
            if (temporal.season?.value) temporalItems.push({ label: 'Season', value: temporal.season.value });
            if (temporal.era?.value) temporalItems.push({ label: 'Era', value: temporal.era.value });
            
            if (temporalItems.length > 0) {
                html += '<div class="temporal-grid">';
                temporalItems.forEach(item => {
                    html += `
                        <div class="temporal-item">
                            <div class="temporal-label">${item.label}</div>
                            <div class="temporal-value">${item.value}</div>
                        </div>
                    `;
                });
                html += '</div>';
            }
            
            // Sociocultural
            const socio = data.sociocultural_analysis || {};
            if (socio.socioeconomic_level) {
                html += `<p><strong>Socioeconomic:</strong> ${socio.socioeconomic_level}</p>`;
            }
            if (socio.cultural_context) {
                html += `<p><strong>Cultural:</strong> ${this.truncateText(socio.cultural_context, 80)}</p>`;
            }
            
            // Event classification
            const event = data.event_classification || {};
            if (event.event_type) {
                html += `<p><strong>Event Type:</strong> ${event.event_type}</p>`;
            }
            
            content.innerHTML = html || '<p class="placeholder">No context data available</p>';
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${data.error || 'Unknown error'}</p>`;
        }
    }
    
    renderKeyInferences(contextData) {
        if (!this.keyInferencesPanel || !this.inferencesList) return;
        
        const inferences = contextData?.key_inferences || [];
        if (inferences.length === 0) {
            this.keyInferencesPanel.style.display = 'none';
            return;
        }
        
        this.keyInferencesPanel.style.display = 'block';
        
        let html = '';
        inferences.slice(0, 5).forEach(inf => {
            const confidence = inf.confidence_percent || 0;
            const confClass = confidence >= 75 ? 'high' : confidence >= 50 ? 'medium' : 'low';
            
            html += `
                <div class="inference-item">
                    <span class="inference-order">${inf.order || '?'}</span>
                    <span class="inference-text">${inf.inference || 'N/A'}</span>
                    <span class="inference-confidence ${confClass}">${confidence}%</span>
                </div>
            `;
        });
        
        this.inferencesList.innerHTML = html;
    }
    
    // =========================================================================
    // HELPER METHODS
    // =========================================================================
    
    truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    getConfidenceClass(confidence) {
        if (!confidence) return '';
        const lower = confidence.toLowerCase();
        if (lower.includes('high') || lower.includes('alto') || lower.includes('muy alto')) return 'high';
        if (lower.includes('medium') || lower.includes('medio')) return 'medium';
        if (lower.includes('low') || lower.includes('bajo')) return 'low';
        return '';
    }
    
    getVerdictClass(classification) {
        if (!classification) return '';
        const lower = classification.toLowerCase();
        if (lower.includes('auténtica') || lower.includes('authentic') || lower.includes('probablemente auténtica')) {
            return 'authentic';
        }
        if (lower.includes('manipulada') || lower.includes('manipulated') || lower.includes('generada')) {
            return 'manipulated';
        }
        return 'suspicious';
    }
    
    countAnomalies(anomalies) {
        let count = 0;
        for (const key in anomalies) {
            const val = anomalies[key];
            if (Array.isArray(val)) {
                count += val.length;
            } else if (typeof val === 'object' && val !== null) {
                // Check manipulation_specific
                for (const subKey in val) {
                    if (val[subKey]?.detected) count++;
                }
            }
        }
        return count;
    }
    
    displayBatchResults(results, frameCollection) {
        // Hide loading
        this.loadingIndicator.style.display = 'none';
        this.resultsContainer.style.display = 'block';
        
        // Display multi-frame report
        this.textResults.textContent = results.text || 'No text report available';
        this.jsonResults.textContent = JSON.stringify(results.json, null, 2);
        
        // For multi-frame, show a collage or summary preview
        console.log('📊 Multi-frame results displayed:', frameCollection.length, 'frames');
    }
    
    displayPreview() {
        const frame = window.videoPlayer?.getCapturedFrame();
        const roi = window.roiSelector?.getROI();
        
        if (!frame) {
            console.warn('⚠️ No frame available for preview');
            return;
        }
        
        const img = new Image();
        img.onload = () => {
            this.previewCanvas.width = img.width;
            this.previewCanvas.height = img.height;
            
            const ctx = this.previewCanvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            
            // Draw ROI rectangle if exists
            if (roi) {
                ctx.strokeStyle = '#00ff00';
                ctx.lineWidth = 4;
                ctx.strokeRect(roi.x, roi.y, roi.width, roi.height);
                
                ctx.fillStyle = 'rgba(0, 255, 0, 0.1)';
                ctx.fillRect(roi.x, roi.y, roi.width, roi.height);
                
                // Add label
                ctx.fillStyle = '#00ff00';
                ctx.font = 'bold 20px Arial';
                ctx.fillText('ROI', roi.x + 10, roi.y + 30);
            }
        };
        img.src = frame;
    }
    
    showError(message) {
        this.loadingIndicator.style.display = 'none';
        this.resultsContainer.style.display = 'block';
        
        // Determine error type for better messaging
        let errorType = '❌ Error General';
        let suggestion = 'Por favor intenta nuevamente.';
        
        if (message.includes('NetworkError') || message.includes('Failed to fetch')) {
            errorType = '🌐 Error de Conexión';
            suggestion = 'Verifica que el backend esté ejecutándose (docker compose up).';
        } else if (message.includes('HTTP error')) {
            errorType = '🚫 Error del Servidor';
            suggestion = 'El backend respondió con un error. Revisa los logs de Docker.';
        } else if (message.includes('timeout')) {
            errorType = '⏱️ Timeout';
            suggestion = 'El análisis tomó demasiado tiempo. Intenta con una región más pequeña.';
        }
        
        this.textResults.textContent = `${errorType}\n\n${message}\n\n💡 Sugerencia: ${suggestion}\n\nRevisa la consola del navegador para más detalles.`;
        this.jsonResults.textContent = JSON.stringify({ 
            error: message,
            timestamp: new Date().toISOString(),
            errorType: errorType
        }, null, 2);
        
        // Switch to text tab to show error immediately
        this.switchTab('text');
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`.tab[data-tab="${tabName}"]`)?.classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}Tab`)?.classList.add('active');
    }
    
    copyJSON() {
        if (!this.apiClient.lastResults) return;
        
        const jsonText = JSON.stringify(this.apiClient.lastResults.json, null, 2);
        navigator.clipboard.writeText(jsonText).then(() => {
            this.copyJsonBtn.textContent = '✅ Copiado';
            setTimeout(() => {
                this.copyJsonBtn.textContent = '📋 Copiar JSON';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
            alert('Error al copiar al portapapeles');
        });
    }
    
    downloadReport() {
        if (!this.apiClient.lastResults) return;
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `watchdogs_analysis_${timestamp}.txt`;
        
        const blob = new Blob([this.apiClient.lastResults.text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        
        URL.revokeObjectURL(url);
        console.log('💾 Report downloaded:', filename);
    }
    
    resetAnalysis() {
        this.analysisSection.style.display = 'none';
        this.apiClient.lastResults = null;
        this.apiClient.currentFrame = null;
        this.apiClient.chatHistory = [];
        
        if (this.apiClient.chatHandler) {
            this.apiClient.chatHandler.reset();
        }
        
        if (this.apiClient.chatHandler?.sendChat) {
            this.apiClient.chatHandler.sendChat.disabled = true;
        }
        if (this.apiClient.chatHandler?.chatInput) {
            this.apiClient.chatHandler.chatInput.disabled = true;
        }
        
        window.roiSelector?.clearROI();
        console.log('🔄 Analysis reset');
    }
}
