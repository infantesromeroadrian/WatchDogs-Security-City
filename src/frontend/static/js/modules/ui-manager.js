/**
 * UI Manager Module
 * Handles all UI updates, displays, and user interactions
 * Updated for CIA-Level 7-Agent Dashboard
 */

import { log } from './logger.js';

/**
 * Escape HTML special characters to prevent XSS injection.
 * MUST be applied to all dynamic data before innerHTML assignment,
 * especially LLM-generated content which is susceptible to prompt injection.
 */
function esc(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

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
        
        // L-10: Defensive null guards on action buttons
        this.copyJsonBtn?.addEventListener('click', () => {
            this.copyJSON();
        });
        
        this.downloadReportBtn?.addEventListener('click', () => {
            this.downloadReport();
        });
        
        this.newAnalysisBtn?.addEventListener('click', () => {
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
        
        // Clear any previous ROI feedback
        this._clearROIFeedback();
        
        // Scroll to analysis section
        this.analysisSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * Show ROI crop confirmation to user during analysis.
     * Called when the SSE session event confirms ROI was applied server-side.
     */
    showROIFeedback(cropSize, originalSize) {
        // Update the summary text to show ROI info
        if (this.summaryText) {
            this.summaryText.textContent =
                `Analyzing ROI: ${cropSize.width}x${cropSize.height}px ` +
                `(from ${originalSize.width}x${originalSize.height}) with 7 agents...`;
        }
        
        // Add a visible ROI badge above the agent cards
        const dashboard = document.getElementById('intelSummary');
        if (dashboard) {
            const existing = document.getElementById('roiFeedbackBadge');
            if (existing) existing.remove();
            
            const badge = document.createElement('div');
            badge.id = 'roiFeedbackBadge';
            badge.style.cssText =
                'background: linear-gradient(135deg, #00d2ff22, #764ba222); ' +
                'border: 1px solid #00d2ff; border-radius: 8px; padding: 8px 16px; ' +
                'margin-bottom: 12px; display: flex; align-items: center; gap: 8px; ' +
                'font-size: 13px; color: #00d2ff;';
            badge.innerHTML =
                `<span style="font-size: 16px;">&#9986;</span> ` +
                `<strong>ROI Active</strong> &mdash; ` +
                `${esc(String(cropSize.width))}x${esc(String(cropSize.height))}px crop ` +
                `from ${esc(String(originalSize.width))}x${esc(String(originalSize.height))} original`;
            dashboard.prepend(badge);
        }
    }
    
    _clearROIFeedback() {
        const badge = document.getElementById('roiFeedbackBadge');
        if (badge) badge.remove();
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
            this.summaryText.textContent = 'Analyzing with 14 intelligence agents...';
        }
        
        // Reset all agent cards (original 7 + military block 1 + block 2)
        const agentIds = [
            'vision', 'ocr', 'detection', 'geolocation', 'faceAnalysis',
            'forensicAnalysis', 'contextIntel',
            'vehicleDetection', 'weaponDetection', 'crowdAnalysis',
            'shadowAnalysis', 'infrastructureAnalysis',
            'temporalComparison', 'nightVision'
        ];
        agentIds.forEach(id => {
            const content = document.getElementById(`${id}Content`);
            if (content) {
                content.innerHTML = '<p class="placeholder">Awaiting analysis...</p>';
            }
        });
        
        // Reset military badge values
        const vehicleCount = document.getElementById('vehicleCount');
        if (vehicleCount) vehicleCount.textContent = '0';
        const threatLevel = document.getElementById('threatLevel');
        if (threatLevel) {
            threatLevel.textContent = '-';
            threatLevel.className = 'threat-level-badge';
        }
        const crowdCount = document.getElementById('crowdCount');
        if (crowdCount) crowdCount.textContent = '-';
        // Block 2 badges
        const postureLevel = document.getElementById('postureLevel');
        if (postureLevel) {
            postureLevel.textContent = '-';
            postureLevel.className = 'posture-badge';
        }
        const nightRiskLevel = document.getElementById('nightRiskLevel');
        if (nightRiskLevel) {
            nightRiskLevel.textContent = '-';
            nightRiskLevel.className = 'risk-level-badge';
        }
        
        // Hide key inferences
        if (this.keyInferencesPanel) {
            this.keyInferencesPanel.style.display = 'none';
        }
    }
    
    renderIntelDashboard(jsonData) {
        if (!jsonData || !jsonData.agents) {
            log.warn('No agent data in results');
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
        // Military Intelligence Block 1
        this.renderVehicleDetectionCard(agents.vehicle_detection);
        this.renderWeaponDetectionCard(agents.weapon_detection);
        this.renderCrowdAnalysisCard(agents.crowd_analysis);
        this.renderShadowAnalysisCard(agents.shadow_analysis);
        this.renderInfrastructureAnalysisCard(agents.infrastructure_analysis);
        // Military Intelligence Block 2
        this.renderTemporalComparisonCard(agents.temporal_comparison);
        this.renderNightVisionCard(agents.night_vision);
        
        // Render key inferences from context_intel
        this.renderKeyInferences(agents.context_intel);
        
        log.info('Military-Grade Intel Dashboard rendered with 14 agents');
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
            context_intel: data => this.renderContextIntelCard(data),
            // Military Intelligence Block 1
            vehicle_detection: data => this.renderVehicleDetectionCard(data),
            weapon_detection: data => this.renderWeaponDetectionCard(data),
            crowd_analysis: data => this.renderCrowdAnalysisCard(data),
            shadow_analysis: data => this.renderShadowAnalysisCard(data),
            infrastructure_analysis: data => this.renderInfrastructureAnalysisCard(data),
            // Military Intelligence Block 2
            temporal_comparison: data => this.renderTemporalComparisonCard(data),
            night_vision: data => this.renderNightVisionCard(data)
        };

        const renderer = renderMap[agentName];
        if (renderer) {
            renderer(result);
            log.debug(`Agent card updated: ${agentName}`);
        } else {
            log.warn(`Unknown agent: ${agentName}`);
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
            'contextIntelContent',
            'vehicleDetectionContent',
            'weaponDetectionContent',
            'crowdAnalysisContent',
            'shadowAnalysisContent',
            'infrastructureAnalysisContent',
            'temporalComparisonContent',
            'nightVisionContent'
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
            content.innerHTML = `<p>${esc(this.truncateText(data.analysis, 300))}</p>`;
            if (badge && data.confidence) {
                badge.textContent = data.confidence;
                badge.className = `confidence-badge ${this.getConfidenceClass(data.confidence)}`;
            }
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
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
            content.innerHTML = `<p>${esc(this.truncateText(data.analysis, 300))}</p>`;
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
        }
    }
    
    renderDetectionCard(data) {
        const content = document.getElementById('detectionContent');
        const badge = document.getElementById('detectionConfidence');
        if (!content || !data) return;
        
        if (data.status === 'success') {
            content.innerHTML = `<p>${esc(this.truncateText(data.analysis, 300))}</p>`;
            if (badge && data.confidence) {
                badge.textContent = data.confidence;
                badge.className = `confidence-badge ${this.getConfidenceClass(data.confidence)}`;
            }
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
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
                    <div class="location-main">📍 ${esc(city)}, ${esc(country)}</div>
                    ${region ? `<div class="location-detail">${esc(region)}</div>` : ''}
                </div>
            `;
            
            // Add key clues
            const clues = data.key_clues || data.evidence_chain || [];
            if (clues.length > 0) {
                html += '<p><strong>Key Clues:</strong></p><ul>';
                clues.slice(0, 4).forEach(clue => {
                    const clueText = typeof clue === 'string' ? clue : clue.evidence || clue;
                    html += `<li>${esc(this.truncateText(clueText, 80))}</li>`;
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
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
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
                <p><strong>Detected:</strong> ${esc(personCount)} person(s)</p>
                <p><strong>Faces visible:</strong> ${esc(detection.faces_visible || 'N/A')}</p>
                <p><strong>ID Quality:</strong> ${esc(detection.identification_quality || 'N/A')}</p>
            `;
            
            // Person summary chips
            const persons = data.persons || [];
            if (persons.length > 0) {
                html += '<div class="person-summary">';
                persons.slice(0, 4).forEach(person => {
                    const demo = person.demographics || {};
                    const age = demo.age_range || '?';
                    const gender = demo.gender || '?';
                    html += `<span class="person-chip">P${esc(person.person_id)}: ${esc(age)}, ${esc(gender)}</span>`;
                });
                html += '</div>';
            }
            
            // Distinctive features
            const features = data.most_distinctive_features || [];
            if (features.length > 0) {
                html += '<p><strong>Distinctive:</strong></p><ul>';
                features.slice(0, 3).forEach(f => {
                    html += `<li>${esc(this.truncateText(f, 60))}</li>`;
                });
                html += '</ul>';
            }
            
            content.innerHTML = html;
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
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
                    <div class="verdict-text">${esc(classification.toUpperCase())}</div>
                    ${integrity !== null ? `<div class="verdict-score">Integrity: ${esc(integrity)}/100</div>` : ''}
                </div>
            `;
            
            // Justification
            if (verdict.justification) {
                html += `<p><em>${esc(this.truncateText(verdict.justification, 150))}</em></p>`;
            }
            
            // Anomalies summary
            const anomalies = data.anomalies || {};
            const anomalyCount = this.countAnomalies(anomalies);
            if (anomalyCount > 0) {
                html += `<p><strong>Anomalies detected:</strong> ${esc(anomalyCount)}</p>`;
            }
            
            // Recommendations
            const recs = data.recommendations || [];
            if (recs.length > 0) {
                html += '<p><strong>Recommendations:</strong></p><ul>';
                recs.slice(0, 2).forEach(r => {
                    html += `<li>${esc(this.truncateText(r, 50))}</li>`;
                });
                html += '</ul>';
            }
            
            content.innerHTML = html;
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
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
                html += `<p><em>${esc(this.truncateText(data.executive_summary, 200))}</em></p>`;
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
                            <div class="temporal-label">${esc(item.label)}</div>
                            <div class="temporal-value">${esc(item.value)}</div>
                        </div>
                    `;
                });
                html += '</div>';
            }
            
            // Sociocultural
            const socio = data.sociocultural_analysis || {};
            if (socio.socioeconomic_level) {
                html += `<p><strong>Socioeconomic:</strong> ${esc(socio.socioeconomic_level)}</p>`;
            }
            if (socio.cultural_context) {
                html += `<p><strong>Cultural:</strong> ${esc(this.truncateText(socio.cultural_context, 80))}</p>`;
            }
            
            // Event classification
            const event = data.event_classification || {};
            if (event.event_type) {
                html += `<p><strong>Event Type:</strong> ${esc(event.event_type)}</p>`;
            }
            
            content.innerHTML = html || '<p class="placeholder">No context data available</p>';
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
        }
    }
    
    // =========================================================================
    // MILITARY INTELLIGENCE BLOCK 1 — Card renderers
    // =========================================================================

    renderVehicleDetectionCard(data) {
        const content = document.getElementById('vehicleDetectionContent');
        const countBadge = document.getElementById('vehicleCount');
        if (!content) return;

        if (!data || data.status === 'skipped') {
            content.innerHTML = '<p class="placeholder">Agent not executed</p>';
            return;
        }

        if (countBadge) countBadge.textContent = data.vehicle_count || 0;

        if (data.status === 'success') {
            let html = '';
            if (data.summary) {
                html += `<p><em>${esc(this.truncateText(data.summary, 200))}</em></p>`;
            }

            const vehicles = data.vehicles || [];
            if (vehicles.length > 0) {
                html += '<div class="vehicle-list">';
                vehicles.slice(0, 5).forEach(v => {
                    const cat = v.category || 'Unknown';
                    const catClass = cat.toLowerCase().includes('militar') ? 'military' :
                                     cat.toLowerCase().includes('emergencia') ? 'emergency' : 'civilian';
                    html += `<div class="vehicle-item ${catClass}">`;
                    html += `<strong>${esc(v.type || 'Vehicle')}</strong>`;
                    if (v.color) html += ` - ${esc(v.color)}`;
                    if (v.make_model) html += ` (${esc(v.make_model)})`;
                    if (v.license_plate) html += `<br><span class="plate-reading">🔢 ${esc(v.license_plate)}</span>`;
                    if (v.threat_level && v.threat_level !== 'Ninguno') {
                        html += `<br><span class="threat-tag">${esc(v.threat_level)}</span>`;
                    }
                    html += '</div>';
                });
                html += '</div>';
            }

            const plates = data.license_plates || [];
            if (plates.length > 0) {
                html += '<p><strong>Plates:</strong> ';
                html += plates.slice(0, 5).map(p => {
                    const reading = typeof p === 'string' ? p : (p.reading || 'N/A');
                    return esc(reading);
                }).join(', ');
                html += '</p>';
            }

            const assessment = data.tactical_assessment || {};
            if (assessment.threat_level) {
                const tlClass = this.getThreatClass(assessment.threat_level);
                html += `<p class="threat-assessment ${tlClass}"><strong>Threat:</strong> ${esc(assessment.threat_level)}</p>`;
            }

            content.innerHTML = html || '<p class="placeholder">No vehicles detected</p>';
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
        }
    }

    renderWeaponDetectionCard(data) {
        const content = document.getElementById('weaponDetectionContent');
        const threatBadge = document.getElementById('threatLevel');
        if (!content) return;

        if (!data || data.status === 'skipped') {
            content.innerHTML = '<p class="placeholder">Agent not executed</p>';
            return;
        }

        const assessment = data.threat_assessment || {};
        if (threatBadge && assessment.threat_level) {
            threatBadge.textContent = assessment.threat_level;
            threatBadge.className = `threat-level-badge ${this.getThreatClass(assessment.threat_level)}`;
        }

        if (data.status === 'success') {
            let html = '';
            if (data.summary) {
                html += `<p><em>${esc(this.truncateText(data.summary, 200))}</em></p>`;
            }

            const weaponCount = data.weapon_count || 0;
            html += `<p><strong>Weapons detected:</strong> ${esc(weaponCount)}</p>`;

            if (assessment.threat_level) {
                const tlClass = this.getThreatClass(assessment.threat_level);
                html += `<p class="threat-assessment ${tlClass}"><strong>THREAT LEVEL:</strong> ${esc(assessment.threat_level)}</p>`;
            }

            const equipment = data.military_equipment || [];
            if (equipment.length > 0) {
                html += '<p><strong>Military Equipment:</strong></p><ul>';
                equipment.slice(0, 4).forEach(eq => {
                    html += `<li>${esc(typeof eq === 'string' ? eq : JSON.stringify(eq))}</li>`;
                });
                html += '</ul>';
            }

            const explosive = data.explosive_indicators || [];
            if (explosive.length > 0) {
                html += '<p><strong>Explosive Indicators:</strong></p><ul>';
                explosive.slice(0, 3).forEach(ind => {
                    html += `<li>${esc(typeof ind === 'string' ? ind : JSON.stringify(ind))}</li>`;
                });
                html += '</ul>';
            }

            content.innerHTML = html || '<p class="placeholder">No threats detected</p>';
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
        }
    }

    renderCrowdAnalysisCard(data) {
        const content = document.getElementById('crowdAnalysisContent');
        const countBadge = document.getElementById('crowdCount');
        if (!content) return;

        if (!data || data.status === 'skipped') {
            content.innerHTML = '<p class="placeholder">Agent not executed</p>';
            return;
        }

        const density = data.density_estimate || {};
        if (countBadge) {
            countBadge.textContent = density.total_count || density.density_level || '-';
        }

        if (data.status === 'success') {
            let html = '';
            if (data.summary) {
                html += `<p><em>${esc(this.truncateText(data.summary, 200))}</em></p>`;
            }

            if (density.total_count) {
                html += `<p><strong>Estimated count:</strong> ${esc(density.total_count)}</p>`;
            }
            if (density.density_level) {
                html += `<p><strong>Density:</strong> ${esc(density.density_level)}</p>`;
            }

            const behavior = data.behavioral_assessment || {};
            if (behavior.general_mood) {
                html += `<p><strong>General mood:</strong> ${esc(behavior.general_mood)}</p>`;
            }

            const concerns = data.security_concerns || [];
            if (concerns.length > 0) {
                html += '<p><strong>Security Concerns:</strong></p><ul>';
                concerns.slice(0, 3).forEach(c => {
                    html += `<li>${esc(typeof c === 'string' ? c : JSON.stringify(c))}</li>`;
                });
                html += '</ul>';
            }

            content.innerHTML = html || '<p class="placeholder">No crowd data available</p>';
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
        }
    }

    renderShadowAnalysisCard(data) {
        const content = document.getElementById('shadowAnalysisContent');
        if (!content) return;

        if (!data || data.status === 'skipped') {
            content.innerHTML = '<p class="placeholder">Agent not executed</p>';
            return;
        }

        if (data.status === 'success') {
            let html = '';
            if (data.summary) {
                html += `<p><em>${esc(this.truncateText(data.summary, 200))}</em></p>`;
            }

            const timeEst = data.time_estimate || {};
            if (timeEst.time_range) {
                html += `<p><strong>Estimated time:</strong> ${esc(timeEst.time_range)}`;
                if (timeEst.confidence) html += ` (${esc(timeEst.confidence)})`;
                html += '</p>';
            }

            const sunPos = data.sun_position || {};
            if (sunPos.azimuth_estimate) {
                html += `<p><strong>Sun azimuth:</strong> ${esc(sunPos.azimuth_estimate)}</p>`;
            }
            if (sunPos.hemisphere) {
                html += `<p><strong>Hemisphere:</strong> ${esc(sunPos.hemisphere)}</p>`;
            }

            const season = data.season_inference || {};
            if (season.estimated_season) {
                html += `<p><strong>Season:</strong> ${esc(season.estimated_season)}`;
                if (season.confidence) html += ` (${esc(season.confidence)})`;
                html += '</p>';
            }

            const forensic = data.forensic_indicators || [];
            if (forensic.length > 0) {
                html += '<p><strong>Shadow Inconsistencies:</strong></p><ul>';
                forensic.slice(0, 3).forEach(f => {
                    html += `<li>${esc(typeof f === 'string' ? f : JSON.stringify(f))}</li>`;
                });
                html += '</ul>';
            }

            content.innerHTML = html || '<p class="placeholder">No shadow data available</p>';
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
        }
    }

    renderInfrastructureAnalysisCard(data) {
        const content = document.getElementById('infrastructureAnalysisContent');
        if (!content) return;

        if (!data || data.status === 'skipped') {
            content.innerHTML = '<p class="placeholder">Agent not executed</p>';
            return;
        }

        if (data.status === 'success') {
            let html = '';
            if (data.summary) {
                html += `<p><em>${esc(this.truncateText(data.summary, 200))}</em></p>`;
            }

            const buildings = data.buildings || [];
            const roads = data.roads || [];
            const bridges = data.bridges || [];
            const signage = data.signage || [];

            html += '<div class="infra-stats">';
            if (buildings.length) html += `<span class="infra-stat">🏢 ${buildings.length} buildings</span>`;
            if (roads.length) html += `<span class="infra-stat">🛣️ ${roads.length} roads</span>`;
            if (bridges.length) html += `<span class="infra-stat">🌉 ${bridges.length} bridges</span>`;
            if (signage.length) html += `<span class="infra-stat">🪧 ${signage.length} signs</span>`;
            html += '</div>';

            const assessment = data.strategic_assessment || {};
            if (assessment.military_significance) {
                html += `<p><strong>Military significance:</strong> ${esc(this.truncateText(assessment.military_significance, 100))}</p>`;
            }

            const vulns = assessment.vulnerability_points;
            if (vulns && Array.isArray(vulns) && vulns.length > 0) {
                html += '<p><strong>Vulnerability points:</strong></p><ul>';
                vulns.slice(0, 3).forEach(v => {
                    html += `<li>${esc(typeof v === 'string' ? v : JSON.stringify(v))}</li>`;
                });
                html += '</ul>';
            }

            content.innerHTML = html || '<p class="placeholder">No infrastructure data</p>';
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
        }
    }

    // =========================================================================
    // MILITARY INTELLIGENCE BLOCK 2 — Card renderers
    // =========================================================================

    renderTemporalComparisonCard(data) {
        const content = document.getElementById('temporalComparisonContent');
        const postureBadge = document.getElementById('postureLevel');
        if (!content) return;

        if (!data || data.status === 'skipped') {
            content.innerHTML = '<p class="placeholder">Agent not executed</p>';
            return;
        }

        const posture = data.strategic_posture || {};
        if (postureBadge && posture.posture_type) {
            postureBadge.textContent = posture.posture_type;
            postureBadge.className = `posture-badge ${this.getPostureClass(posture.posture_type)}`;
        }

        if (data.status === 'success') {
            let html = '';
            if (data.summary) {
                html += `<p><em>${esc(this.truncateText(data.summary, 200))}</em></p>`;
            }

            if (posture.posture_type) {
                const pClass = this.getPostureClass(posture.posture_type);
                html += `<p class="threat-assessment ${pClass}"><strong>Strategic Posture:</strong> ${esc(posture.posture_type)}</p>`;
            }

            const structural = data.structural_changes || {};
            const newItems = structural.new_constructions || [];
            const removed = structural.removed_structures || [];
            const modified = structural.modifications || [];
            if (newItems.length || removed.length || modified.length) {
                html += '<div class="infra-stats">';
                if (newItems.length) html += `<span class="infra-stat">🆕 ${newItems.length} new</span>`;
                if (removed.length) html += `<span class="infra-stat">🗑️ ${removed.length} removed</span>`;
                if (modified.length) html += `<span class="infra-stat">🔄 ${modified.length} modified</span>`;
                html += '</div>';
            }

            const activity = data.activity_detection || {};
            if (Object.keys(activity).length > 0) {
                html += '<p><strong>Activity Changes:</strong></p><ul>';
                Object.entries(activity).slice(0, 4).forEach(([key, val]) => {
                    html += `<li>${esc(key)}: ${esc(typeof val === 'string' ? val : JSON.stringify(val))}</li>`;
                });
                html += '</ul>';
            }

            const chronology = data.chronology || [];
            if (chronology.length > 0) {
                html += '<div class="chronology-list">';
                chronology.slice(0, 4).forEach(event => {
                    if (typeof event === 'object') {
                        html += `<div class="chronology-item">`;
                        html += `<strong>${esc(event.timeframe || 'N/A')}</strong>: ${esc(event.description || 'N/A')}`;
                        html += '</div>';
                    } else {
                        html += `<div class="chronology-item">${esc(event)}</div>`;
                    }
                });
                html += '</div>';
            }

            content.innerHTML = html || '<p class="placeholder">No temporal changes detected</p>';
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
        }
    }

    renderNightVisionCard(data) {
        const content = document.getElementById('nightVisionContent');
        const riskBadge = document.getElementById('nightRiskLevel');
        if (!content) return;

        if (!data || data.status === 'skipped') {
            content.innerHTML = '<p class="placeholder">Agent not executed</p>';
            return;
        }

        const assessment = data.tactical_assessment || {};
        if (riskBadge && assessment.risk_level) {
            riskBadge.textContent = assessment.risk_level;
            riskBadge.className = `risk-level-badge ${this.getRiskClass(assessment.risk_level)}`;
        }

        if (data.status === 'success') {
            let html = '';
            if (data.summary) {
                html += `<p><em>${esc(this.truncateText(data.summary, 200))}</em></p>`;
            }

            const visibility = data.visibility_conditions || {};
            if (Object.keys(visibility).length > 0) {
                html += '<div class="visibility-info">';
                if (visibility.ambient_light) html += `<p><strong>Ambient Light:</strong> ${esc(visibility.ambient_light)}</p>`;
                if (visibility.visibility_range) html += `<p><strong>Visibility Range:</strong> ${esc(visibility.visibility_range)}</p>`;
                if (visibility.quality) html += `<p><strong>Image Quality:</strong> ${esc(visibility.quality)}</p>`;
                html += '</div>';
            }

            const lightSources = data.light_sources || {};
            const sources = lightSources.identified_sources || [];
            if (sources.length > 0) {
                html += '<div class="light-source-info">';
                html += '<p><strong>Light Sources:</strong></p><ul>';
                sources.slice(0, 4).forEach(src => {
                    if (typeof src === 'object') {
                        html += `<li>${esc(src.type || 'N/A')}: ${esc(src.description || 'N/A')}</li>`;
                    } else {
                        html += `<li>${esc(src)}</li>`;
                    }
                });
                html += '</ul></div>';
            }

            const nocturnal = data.nocturnal_activity || {};
            if (Object.keys(nocturnal).length > 0) {
                html += '<p><strong>Night Activity:</strong></p><ul>';
                Object.entries(nocturnal).slice(0, 4).forEach(([key, val]) => {
                    html += `<li>${esc(key)}: ${esc(typeof val === 'string' ? val : JSON.stringify(val))}</li>`;
                });
                html += '</ul>';
            }

            const covert = data.covert_indicators || {};
            const indicators = covert.indicators || [];
            if (indicators.length > 0) {
                html += '<p><strong>Covert Indicators:</strong></p><ul>';
                indicators.slice(0, 3).forEach(ind => {
                    html += `<li>${esc(typeof ind === 'string' ? ind : JSON.stringify(ind))}</li>`;
                });
                html += '</ul>';
            }

            if (assessment.risk_level) {
                const rClass = this.getRiskClass(assessment.risk_level);
                html += `<p class="threat-assessment ${rClass}"><strong>Night Risk:</strong> ${esc(assessment.risk_level)}</p>`;
            }

            content.innerHTML = html || '<p class="placeholder">No night vision data</p>';
        } else {
            content.innerHTML = `<p class="placeholder">Error: ${esc(data.error || 'Unknown error')}</p>`;
        }
    }

    getPostureClass(postureType) {
        if (!postureType) return '';
        const upper = postureType.toUpperCase();
        if (upper.includes('BUILDUP') || upper.includes('CONCENTRACIÓN')) return 'posture-buildup';
        if (upper.includes('WITHDRAWAL') || upper.includes('RETIRADA')) return 'posture-withdrawal';
        if (upper.includes('FORTIF') || upper.includes('FORTIFICACIÓN')) return 'posture-fortification';
        if (upper.includes('CRISIS') || upper.includes('EMERGENCY')) return 'posture-crisis';
        return 'posture-normal';
    }

    getRiskClass(riskLevel) {
        if (!riskLevel) return '';
        const upper = riskLevel.toUpperCase();
        if (upper.includes('CRITICAL') || upper.includes('CRÍTICO')) return 'risk-critical';
        if (upper.includes('HIGH') || upper.includes('ALTO')) return 'risk-high';
        if (upper.includes('MEDIUM') || upper.includes('MEDIO')) return 'risk-medium';
        if (upper.includes('LOW') || upper.includes('BAJO')) return 'risk-low';
        return 'risk-minimal';
    }

    getThreatClass(threatLevel) {
        if (!threatLevel) return '';
        const upper = threatLevel.toUpperCase();
        if (upper.includes('CRITICAL') || upper.includes('CRÍTICO')) return 'threat-critical';
        if (upper.includes('HIGH') || upper.includes('ALTO')) return 'threat-high';
        if (upper.includes('MEDIUM') || upper.includes('MEDIO')) return 'threat-medium';
        if (upper.includes('LOW') || upper.includes('BAJO')) return 'threat-low';
        return 'threat-none';
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
                    <span class="inference-order">${esc(inf.order || '?')}</span>
                    <span class="inference-text">${esc(inf.inference || 'N/A')}</span>
                    <span class="inference-confidence ${confClass}">${esc(confidence)}%</span>
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
        log.info('Multi-frame results displayed:', frameCollection.length, 'frames');
    }
    
    displayPreview() {
        const frame = window.videoPlayer?.getCapturedFrame();
        const roi = window.roiSelector?.getROI();
        
        if (!frame) {
            log.warn('No frame available for preview');
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
        // Update tab buttons (L-7: toggle aria-selected for accessibility)
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
            tab.setAttribute('aria-selected', 'false');
        });
        const activeTab = document.querySelector(`.tab[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
            activeTab.setAttribute('aria-selected', 'true');
        }
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}Tab`)?.classList.add('active');
    }
    
    copyJSON() {
        if (!this.apiClient.lastResults) return;
        
        const jsonText = JSON.stringify(this.apiClient.lastResults.json, null, 2);

        // L-8: Clipboard API fallback — navigator.clipboard requires secure context (HTTPS/localhost)
        const onSuccess = () => {
            this.copyJsonBtn.textContent = '✅ Copiado';
            setTimeout(() => { this.copyJsonBtn.textContent = '📋 Copiar JSON'; }, 2000);
        };

        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(jsonText).then(onSuccess).catch(err => {
                log.warn('Clipboard API failed, trying fallback:', err);
                this._copyFallback(jsonText) ? onSuccess() : alert('Error al copiar al portapapeles');
            });
        } else {
            this._copyFallback(jsonText) ? onSuccess() : alert('Error al copiar al portapapeles');
        }
    }

    /** L-8: Textarea-based copy fallback for insecure contexts. */
    _copyFallback(text) {
        try {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.cssText = 'position:fixed;left:-9999px;top:-9999px';
            document.body.appendChild(ta);
            ta.select();
            const ok = document.execCommand('copy');
            ta.remove();
            return ok;
        } catch (e) {
            log.error('Copy fallback failed:', e);
            return false;
        }
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
        log.debug('Report downloaded:', filename);
    }
    
    resetAnalysis() {
        this.analysisSection.style.display = 'none';
        this.apiClient.lastResults = null;
        this.apiClient.currentFrame = null;
        // H-7: Clear stale session so next analysis starts fresh
        this.apiClient.currentSessionId = null;
        this.apiClient.currentROI = null;
        this.apiClient.isMultiFrameAnalysis = false;
        this.apiClient.frameCollection = null;
        
        if (this.apiClient.chatHandler) {
            this.apiClient.chatHandler.reset();
        }
        
        if (this.apiClient.chatHandler?.sendChat) {
            this.apiClient.chatHandler.sendChat.disabled = true;
        }
        if (this.apiClient.chatHandler?.chatInput) {
            this.apiClient.chatHandler.chatInput.disabled = true;
        }
        
        // Reset military badge values
        const vehicleCount = document.getElementById('vehicleCount');
        if (vehicleCount) vehicleCount.textContent = '0';
        const threatLevel = document.getElementById('threatLevel');
        if (threatLevel) {
            threatLevel.textContent = '-';
            threatLevel.className = 'threat-level-badge';
        }
        const crowdCount = document.getElementById('crowdCount');
        if (crowdCount) crowdCount.textContent = '-';
        // Block 2 badges
        const postureLevel = document.getElementById('postureLevel');
        if (postureLevel) {
            postureLevel.textContent = '-';
            postureLevel.className = 'posture-badge';
        }
        const nightRiskLevel = document.getElementById('nightRiskLevel');
        if (nightRiskLevel) {
            nightRiskLevel.textContent = '-';
            nightRiskLevel.className = 'risk-level-badge';
        }
        
        window.roiSelector?.clearROI();
        log.debug('Analysis reset');
    }
}
