/**
 * Map Handler Module — Mapbox GL JS integration
 *
 * Manages interactive maps for OSINT geolocation:
 * - Mini-map inside the geolocation agent card
 * - Fullscreen overlay with marker sidebar
 * - Listens to 'watchdogs:location-found' CustomEvents
 */

import { log } from './logger.js';

export class MapHandler {
    constructor() {
        /** @type {mapboxgl.Map|null} */
        this.miniMap = null;
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

            this._initMiniMap();
            this._initFullscreenOverlay();

            this.ready = true;
            log.info('MapHandler initialised with Mapbox GL JS');
        } catch (err) {
            log.error('MapHandler init failed:', err);
            this._renderUnavailable();
        }
    }

    // ========================================================================
    // Mini-map (inside geolocation card)
    // ========================================================================

    _initMiniMap() {
        const container = document.getElementById('geolocationContent');
        if (!container) return;

        // Inject mini-map container if not present
        let mapDiv = document.getElementById('miniMapContainer');
        if (!mapDiv) {
            const wrapper = document.createElement('div');
            wrapper.className = 'map-container-mini';
            wrapper.innerHTML = `
                <div id="miniMapContainer" style="width:100%;height:100%;"></div>
                <button class="map-expand-btn" title="Expandir mapa">⛶</button>
                <div class="map-marker-count" id="markerCount">0 ubicaciones</div>
            `;
            container.appendChild(wrapper);

            // Expand button
            wrapper.querySelector('.map-expand-btn')
                .addEventListener('click', () => this.toggleFullscreen(true));
        }

        this.miniMap = new mapboxgl.Map({
            container: 'miniMapContainer',
            style: this._STYLE,
            center: [0, 20],
            zoom: 1.5,
            attributionControl: false,
        });

        this.miniMap.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'bottom-right');
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
            zoom: 1.5,
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

        // Create mini-map marker
        const marker = new mapboxgl.Marker({ color })
            .setLngLat([lon, lat])
            .setPopup(new mapboxgl.Popup({ offset: 20 }).setHTML(this._popupHTML(label, lat, lon, location.confidence_radius, source)))
            .addTo(this.miniMap);

        // Create fullscreen marker (if overlay is open)
        let fullMarker = null;
        if (this.fullMap) {
            fullMarker = new mapboxgl.Marker({ color })
                .setLngLat([lon, lat])
                .setPopup(new mapboxgl.Popup({ offset: 20 }).setHTML(this._popupHTML(label, lat, lon, location.confidence_radius, source)))
                .addTo(this.fullMap);
        }

        this.markers.push({ lat, lon, label, source, marker, fullMarker, id });

        // Fly mini-map
        this.miniMap?.flyTo({ center: [lon, lat], zoom: 10, duration: 1200 });

        // Update counter & sidebar
        this._updateCounter();
        this._updateSidebar();

        log.debug(`Marker added: "${label}" [${lat}, ${lon}] (${source})`);
    }

    /**
     * Navigate map to coordinates without adding a new marker.
     */
    flyTo(lat, lon, zoom = 12) {
        if (!this.ready) return;
        this.miniMap?.flyTo({ center: [lon, lat], zoom, duration: 1200 });
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
        this._updateCounter();
        this._updateSidebar();
    }

    reset() {
        this.clearMarkers();
        this.toggleFullscreen(false);
        // Reset view
        this.miniMap?.flyTo({ center: [0, 20], zoom: 1.5, duration: 600 });
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
        const el = document.getElementById('markerCount');
        if (el) {
            el.textContent = `${this.markers.length} ubicacion${this.markers.length !== 1 ? 'es' : ''}`;
        }
    }

    _updateSidebar() {
        const list = document.getElementById('markerList');
        if (!list) return;

        if (this.markers.length === 0) {
            list.innerHTML = '<div class="map-no-markers">Sin ubicaciones detectadas todavia</div>';
            return;
        }

        list.innerHTML = this.markers.map(m => `
            <div class="map-marker-item" data-lat="${m.lat}" data-lon="${m.lon}">
                <div class="marker-label">
                    📍 ${m.label}
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
        const container = document.getElementById('geolocationContent');
        if (!container) return;

        // Only inject if no map already exists
        if (!container.querySelector('.map-unavailable')) {
            const div = document.createElement('div');
            div.className = 'map-unavailable';
            div.textContent = '🗺️ Mapa no disponible — configure MAP_BOX_ACCESS_TOKEN';
            container.appendChild(div);
        }
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
