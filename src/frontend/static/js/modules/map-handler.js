/**
 * Map Handler Module — Tactical Map (Mapbox GL JS)
 *
 * Always-visible command-center map for OSINT geolocation:
 * - Tactical map in dedicated section (top of page)
 * - Fullscreen overlay with marker sidebar
 * - Listens to 'watchdogs:location-found' CustomEvents
 */

import { log } from './logger.js';

export class MapHandler {
    constructor() {
        /** @type {mapboxgl.Map|null} */
        this.tacticalMap = null;
        /** @type {mapboxgl.Map|null} */
        this.fullMap = null;
        /** @type {string|null} */
        this.token = null;
        /** @type {Array<{lat:number, lon:number, label:string|null, source:string, marker:mapboxgl.Marker, id:string}>} */
        this.markers = [];
        /** @type {boolean} */
        this.ready = false;

        this._MAX_MARKERS = 50;
        this._STYLE = 'mapbox://styles/mapbox/dark-v11';

        // DOM refs for tactical HUD
        this._statusEl = document.getElementById('mapStatus');
        this._coordsEl = document.getElementById('mapCoords');
        this._counterEl = document.getElementById('markerCount');
        this._expandBtn = document.getElementById('mapExpandBtn');

        this._bindEvents();
        log.debug('MapHandler constructed — waiting for init()');
    }

    // ========================================================================
    // Initialisation
    // ========================================================================

    /**
     * Fetch the Mapbox token from the backend and bootstrap both maps.
     * Called once from APIClient after DOM is ready.
     */
    async init() {
        try {
            const resp = await fetch('/api/mapbox-token');
            const data = await resp.json();

            if (!data.success || !data.token) {
                log.warn('Mapbox token not available — maps disabled');
                this._renderUnavailable();
                return;
            }

            this.token = data.token;

            // Wait for mapboxgl to be available (loaded via CDN)
            if (typeof mapboxgl === 'undefined') {
                log.error('mapboxgl not loaded — ensure CDN script is present');
                this._renderUnavailable();
                return;
            }

            mapboxgl.accessToken = this.token;

            this._initTacticalMap();
            this._initFullscreenOverlay();

            this.ready = true;
            log.info('MapHandler initialised — tactical map active');
        } catch (err) {
            log.error('MapHandler init failed:', err);
            this._renderUnavailable();
        }
    }

    // ========================================================================
    // Tactical Map (always-visible command center)
    // ========================================================================

    _initTacticalMap() {
        const container = document.getElementById('tacticalMapContainer');
        if (!container) {
            log.error('tacticalMapContainer not found in DOM');
            return;
        }

        this.tacticalMap = new mapboxgl.Map({
            container: 'tacticalMapContainer',
            style: this._STYLE,
            center: [0, 20],
            zoom: 1.8,
            attributionControl: false,
            pitch: 0,
        });

        this.tacticalMap.addControl(
            new mapboxgl.NavigationControl({ showCompass: true }),
            'bottom-right'
        );

        // Update coordinate display on mouse move
        this.tacticalMap.on('mousemove', (e) => {
            if (this._coordsEl) {
                const lat = e.lngLat.lat.toFixed(4);
                const lon = e.lngLat.lng.toFixed(4);
                const latDir = e.lngLat.lat >= 0 ? 'N' : 'S';
                const lonDir = e.lngLat.lng >= 0 ? 'E' : 'W';
                this._coordsEl.textContent =
                    `${Math.abs(lat).toString().padStart(8, ' ')}${latDir} / ${Math.abs(lon).toString().padStart(9, ' ')}${lonDir}`;
            }
        });

        // Reset coords when mouse leaves
        this.tacticalMap.on('mouseout', () => {
            if (this._coordsEl) {
                this._coordsEl.textContent = '---.----N / ---.----E';
            }
        });

        // Expand button
        if (this._expandBtn) {
            this._expandBtn.addEventListener('click', () => this.toggleFullscreen(true));
        }

        log.debug('Tactical map created in #tacticalMapContainer');
    }

    // ========================================================================
    // Fullscreen overlay
    // ========================================================================

    _initFullscreenOverlay() {
        const overlay = document.getElementById('mapFullscreenOverlay');
        if (!overlay) return;

        this.fullMap = new mapboxgl.Map({
            container: 'fullMapContainer',
            style: this._STYLE,
            center: [0, 20],
            zoom: 1.8,
        });

        this.fullMap.addControl(new mapboxgl.NavigationControl(), 'top-right');
        this.fullMap.addControl(new mapboxgl.ScaleControl(), 'bottom-left');

        // Close button
        overlay.querySelector('.map-close-btn')
            ?.addEventListener('click', () => this.toggleFullscreen(false));

        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.toggleFullscreen(false);
        });
    }

    toggleFullscreen(show) {
        const overlay = document.getElementById('mapFullscreenOverlay');
        if (!overlay) return;

        if (show) {
            overlay.classList.add('active');
            // Must resize after overlay becomes visible
            setTimeout(() => {
                this.fullMap?.resize();
                this._syncMarkersToFull();
                // Fly to last marker
                if (this.markers.length > 0) {
                    const last = this.markers[this.markers.length - 1];
                    this.fullMap?.flyTo({ center: [last.lon, last.lat], zoom: 12, duration: 800 });
                }
            }, 100);
        } else {
            overlay.classList.remove('active');
        }
    }

    // ========================================================================
    // Markers
    // ========================================================================

    /**
     * Add a marker to both maps and the sidebar list.
     * @param {{lat:number, lon:number, label?:string|null, confidence_radius?:number, source:string}} location
     */
    addMarker(location) {
        if (!this.ready) return;

        const { lat, lon, source } = location;
        const label = location.label || `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
        const id = `loc-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;

        // Enforce max markers (FIFO)
        if (this.markers.length >= this._MAX_MARKERS) {
            const oldest = this.markers.shift();
            oldest.marker.remove();
            oldest.fullMarker?.remove();
        }

        // Marker colour by source
        const color = source === 'analysis' ? '#ff4444' : '#4da6ff';

        // Create tactical map marker
        const marker = new mapboxgl.Marker({ color })
            .setLngLat([lon, lat])
            .setPopup(new mapboxgl.Popup({ offset: 20 }).setHTML(this._popupHTML(label, lat, lon, location.confidence_radius, source)))
            .addTo(this.tacticalMap);

        // Create fullscreen marker (if overlay is open)
        let fullMarker = null;
        if (this.fullMap) {
            fullMarker = new mapboxgl.Marker({ color })
                .setLngLat([lon, lat])
                .setPopup(new mapboxgl.Popup({ offset: 20 }).setHTML(this._popupHTML(label, lat, lon, location.confidence_radius, source)))
                .addTo(this.fullMap);
        }

        this.markers.push({ lat, lon, label, source, marker, fullMarker, id });

        // Fly tactical map to new marker
        this.tacticalMap?.flyTo({ center: [lon, lat], zoom: 10, duration: 1200 });

        // Update HUD
        this._setStatus('active');
        this._updateCounter();
        this._updateSidebar();

        log.debug(`Marker added: "${label}" [${lat}, ${lon}] (${source})`);
    }

    /**
     * Navigate map to coordinates without adding a new marker.
     */
    flyTo(lat, lon, zoom = 12) {
        if (!this.ready) return;
        this.tacticalMap?.flyTo({ center: [lon, lat], zoom, duration: 1200 });
        if (document.getElementById('mapFullscreenOverlay')?.classList.contains('active')) {
            this.fullMap?.flyTo({ center: [lon, lat], zoom, duration: 1200 });
        }
    }

    clearMarkers() {
        this.markers.forEach(m => {
            m.marker.remove();
            m.fullMarker?.remove();
        });
        this.markers = [];
        this._setStatus('standby');
        this._updateCounter();
        this._updateSidebar();
    }

    reset() {
        this.clearMarkers();
        this.toggleFullscreen(false);
        // Reset view
        this.tacticalMap?.flyTo({ center: [0, 20], zoom: 1.8, duration: 600 });
    }

    // ========================================================================
    // HUD status helpers
    // ========================================================================

    _setStatus(status) {
        if (!this._statusEl) return;
        this._statusEl.textContent = status === 'active' ? 'ACTIVE' : 'STANDBY';
        this._statusEl.className = `tactical-status ${status}`;
    }

    // ========================================================================
    // Internal helpers
    // ========================================================================

    _popupHTML(label, lat, lon, radius, source) {
        const radiusText = radius ? `~${radius >= 1000 ? (radius / 1000).toFixed(0) + ' km' : radius + ' m'} radius` : '';
        return `
            <div class="map-popup-label">${label}</div>
            <div class="map-popup-coords">${lat.toFixed(5)}, ${lon.toFixed(5)}</div>
            ${radiusText ? `<div class="map-popup-meta">${radiusText}</div>` : ''}
            <div class="map-popup-meta">Source: ${source}</div>
        `;
    }

    _updateCounter() {
        if (this._counterEl) {
            const count = this.markers.length;
            this._counterEl.textContent = `${count} TARGET${count !== 1 ? 'S' : ''}`;
            this._counterEl.classList.toggle('has-targets', count > 0);
        }
    }

    _updateSidebar() {
        const list = document.getElementById('markerList');
        if (!list) return;

        if (this.markers.length === 0) {
            list.innerHTML = '<div class="map-no-markers">No targets acquired</div>';
            return;
        }

        list.innerHTML = this.markers.map(m => `
            <div class="map-marker-item" data-lat="${m.lat}" data-lon="${m.lon}">
                <div class="marker-label">
                    &#x1F4CD; ${m.label}
                    <span class="marker-source ${m.source}">${m.source}</span>
                </div>
                <div class="marker-coords">${m.lat.toFixed(5)}, ${m.lon.toFixed(5)}</div>
            </div>
        `).join('');

        // Click to fly
        list.querySelectorAll('.map-marker-item').forEach(item => {
            item.addEventListener('click', () => {
                const lat = parseFloat(item.dataset.lat);
                const lon = parseFloat(item.dataset.lon);
                this.fullMap?.flyTo({ center: [lon, lat], zoom: 14, duration: 800 });
            });
        });
    }

    _syncMarkersToFull() {
        if (!this.fullMap) return;

        // Remove existing full markers and re-create from state
        this.markers.forEach(m => {
            m.fullMarker?.remove();
            const color = m.source === 'analysis' ? '#ff4444' : '#4da6ff';
            m.fullMarker = new mapboxgl.Marker({ color })
                .setLngLat([m.lon, m.lat])
                .setPopup(new mapboxgl.Popup({ offset: 20 }).setHTML(this._popupHTML(m.label, m.lat, m.lon, null, m.source)))
                .addTo(this.fullMap);
        });

        this._updateSidebar();
    }

    _renderUnavailable() {
        const container = document.getElementById('tacticalMapContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="map-unavailable" style="height:100%;display:flex;align-items:center;justify-content:center;">
                MAP OFFLINE — CONFIGURE MAP_BOX_ACCESS_TOKEN
            </div>
        `;
    }

    // ========================================================================
    // Event system
    // ========================================================================

    _bindEvents() {
        window.addEventListener('watchdogs:location-found', (e) => {
            const loc = e.detail;
            if (loc && typeof loc.lat === 'number' && typeof loc.lon === 'number') {
                this.addMarker(loc);
            }
        });
    }
}
