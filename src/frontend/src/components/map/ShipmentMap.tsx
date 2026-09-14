import React, { useEffect, useRef, useState, useMemo } from 'react';
import L from 'leaflet';
import { 
  Maximize2, 
  Layers, 
  AlertTriangle, 
  Truck, 
  ThermometerSnowflake, 
  Compass, 
  Eye, 
  EyeOff, 
  RotateCcw,
  Navigation
} from 'lucide-react';

export interface RouteStop {
  sequence_order: number;
  location_name: string;
  latitude: number;
  longitude: number;
  status?: string;
  stop_type?: 'ORIGIN' | 'DESTINATION' | 'TRANSIT STOP' | string;
}

export interface DisruptionMarker {
  id: number;
  name: string;
  type: string;
  location: string;
  latitude: number;
  longitude: number;
  severity: string;
  description?: string;
  expected_duration_days?: number;
  is_intersecting?: boolean;
}

export interface FleetMarker {
  id: number;
  asset_identifier: string;
  asset_type: string;
  current_location: string;
  latitude: number;
  longitude: number;
  capacity?: number;
  capacity_unit?: string;
  is_refrigerated?: boolean;
  status?: string;
  is_recommended_redeployment?: boolean;
}

export interface ShipmentMapProps {
  origin?: { name: string; latitude: number; longitude: number };
  destination?: { name: string; latitude: number; longitude: number };
  currentLocation?: { name: string; latitude: number; longitude: number };
  activeRoutePoints?: RouteStop[];
  previewRoutePoints?: RouteStop[];
  previewRouteName?: string;
  disruptions?: DisruptionMarker[];
  fleetAssets?: FleetMarker[];
  coldChainEnabled?: boolean;
  currentTemperature?: number | null;
  isColdChainCritical?: boolean;
  height?: string;
  showControls?: boolean;
  interactive?: boolean;
  onSelectShipment?: (id: number) => void;
  shipmentsLayer?: Array<{
    id: number;
    shipment_identifier: string;
    origin: { name: string; latitude: number; longitude: number };
    destination: { name: string; latitude: number; longitude: number };
    current_location: { name: string; latitude: number; longitude: number };
    status: string;
    risk_score: number;
    risk_level: string;
    cold_chain_enabled?: boolean;
    route_points?: RouteStop[];
  }>;
}

export const ShipmentMap: React.FC<ShipmentMapProps> = ({
  origin,
  destination,
  currentLocation,
  activeRoutePoints = [],
  previewRoutePoints = [],
  previewRouteName,
  disruptions = [],
  fleetAssets = [],
  coldChainEnabled = false,
  currentTemperature = null,
  isColdChainCritical = false,
  height = '420px',
  showControls = true,
  interactive = true,
  onSelectShipment,
  shipmentsLayer = []
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layersRef = useRef<{
    activeRoute?: L.Polyline;
    previewRoute?: L.Polyline;
    markers?: L.LayerGroup;
    disruptions?: L.LayerGroup;
    fleet?: L.LayerGroup;
    networkShipments?: L.LayerGroup;
  }>({});

  const [hasError, setHasError] = useState(false);
  const [showDisruptions, setShowDisruptions] = useState(true);
  const [showFleet, setShowFleet] = useState(true);
  const [showPreview, setShowPreview] = useState(true);

  // Initialize map instance
  useEffect(() => {
    if (!mapContainerRef.current) return;
    try {
      if (!mapInstanceRef.current) {
        const map = L.map(mapContainerRef.current, {
          center: [20.0, 55.0],
          zoom: 3,
          zoomControl: false,
          attributionControl: true,
          scrollWheelZoom: interactive,
          dragging: interactive
        });

        if (map.attributionControl) {
          map.attributionControl.setPrefix(false);
        }

        // Public keyless OpenStreetMap tile layer
        const osmTiles = L.tileLayer(
          'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
          {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
          }
        );

        osmTiles.addTo(map);

        L.control.zoom({ position: 'bottomright' }).addTo(map);

        layersRef.current.markers = L.layerGroup().addTo(map);
        layersRef.current.disruptions = L.layerGroup().addTo(map);
        layersRef.current.fleet = L.layerGroup().addTo(map);
        layersRef.current.networkShipments = L.layerGroup().addTo(map);

        mapInstanceRef.current = map;
      }
    } catch (e) {
      console.error('Leaflet initialization error:', e);
      setHasError(true);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update layers & markers whenever data or toggles change
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    try {
      const { markers, disruptions: dLayer, fleet: fLayer, networkShipments: nLayer } = layersRef.current;
      if (!markers || !dLayer || !fLayer || !nLayer) return;

      // Clear existing overlays
      markers.clearLayers();
      dLayer.clearLayers();
      fLayer.clearLayers();
      nLayer.clearLayers();

      if (layersRef.current.activeRoute) {
        map.removeLayer(layersRef.current.activeRoute);
        layersRef.current.activeRoute = undefined;
      }
      if (layersRef.current.previewRoute) {
        map.removeLayer(layersRef.current.previewRoute);
        layersRef.current.previewRoute = undefined;
      }

      const allBoundsPoints: L.LatLngExpression[] = [];

      // 1. Render Network-wide Shipments (for Dashboard mode)
      if (shipmentsLayer && shipmentsLayer.length > 0) {
        shipmentsLayer.forEach((s) => {
          const sPts: [number, number][] = [];
          if (s.route_points && s.route_points.length > 1) {
            s.route_points.forEach((pt) => {
              if (pt.latitude && pt.longitude) sPts.push([pt.latitude, pt.longitude]);
            });
          } else if (s.origin?.latitude && s.destination?.latitude) {
            sPts.push([s.origin.latitude, s.origin.longitude]);
            if (s.current_location?.latitude) sPts.push([s.current_location.latitude, s.current_location.longitude]);
            sPts.push([s.destination.latitude, s.destination.longitude]);
          }

          if (sPts.length >= 2) {
            const isCrit = s.risk_score >= 81;
            const isWarn = s.risk_score >= 60;
            const strokeColor = isCrit ? '#f43f5e' : isWarn ? '#f59e0b' : '#38bdf8';

            const poly = L.polyline(sPts, {
              color: strokeColor,
              weight: isCrit ? 3.5 : 2.5,
              opacity: 0.85,
              dashArray: isWarn ? '6, 6' : undefined
            }).addTo(nLayer);

            poly.bindTooltip(
              `<div style="font-family: monospace; font-size: 11px; padding: 4px 6px;">
                <div style="font-weight: bold; color: ${strokeColor};">${s.shipment_identifier}</div>
                <div>${s.origin.name} → ${s.destination.name}</div>
                <div>Risk: ${s.risk_score}/100 (${s.risk_level})</div>
                ${s.cold_chain_enabled ? '<div style="color: #22d3ee;">❄ Cold Chain Active</div>' : ''}
              </div>`,
              { sticky: true }
            );

            if (onSelectShipment) {
              poly.on('click', () => onSelectShipment(s.id));
            }

            sPts.forEach(p => allBoundsPoints.push(p));
          }
        });
      }

      // 2. Render Active Shipment Route (Single Shipment Mode)
      if (activeRoutePoints && activeRoutePoints.length > 0) {
        const routeCoords: [number, number][] = activeRoutePoints
          .filter(p => p.latitude && p.longitude)
          .map(p => [p.latitude, p.longitude]);

        if (routeCoords.length >= 2) {
          const activeLine = L.polyline(routeCoords, {
            color: '#38bdf8', // vivid sky blue
            weight: 4,
            opacity: 0.9
          }).addTo(map);

          layersRef.current.activeRoute = activeLine;
          routeCoords.forEach(c => allBoundsPoints.push(c));
        }

        // Render stop markers along active route
        const totalStops = activeRoutePoints.length;
        activeRoutePoints.forEach((stop, idx) => {
          if (!stop.latitude || !stop.longitude) return;

          const isOrigin = idx === 0;
          const isDest = idx === totalStops - 1;
          const isCurrent = stop.status === 'CURRENT';

          let bgCol = '#3b82f6';
          let borderCol = '#60a5fa';
          let labelText = `${stop.sequence_order}`;

          if (isOrigin) {
            bgCol = '#10b981';
            borderCol = '#34d399';
            labelText = 'A';
          } else if (isDest) {
            bgCol = '#8b5cf6';
            borderCol = '#a78bfa';
            labelText = 'B';
          } else if (isCurrent) {
            bgCol = '#0284c7';
            borderCol = '#38bdf8';
          }

          const iconHtml = `
            <div style="
              width: 26px;
              height: 26px;
              background-color: ${bgCol};
              border: 2px solid ${borderCol};
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              font-family: monospace;
              font-size: 11px;
              font-weight: bold;
              box-shadow: 0 0 10px rgba(0,0,0,0.6);
            ">
              ${labelText}
            </div>
          `;

          const customIcon = L.divIcon({
            html: iconHtml,
            className: 'custom-stop-marker',
            iconSize: [26, 26],
            iconAnchor: [13, 13]
          });

          const marker = L.marker([stop.latitude, stop.longitude], { icon: customIcon }).addTo(markers);
          marker.bindPopup(`
            <div style="font-family: sans-serif; font-size: 12px; color: #0f172a; padding: 2px 4px;">
              <div style="font-weight: bold; color: ${bgCol}; text-transform: uppercase;">
                ${isOrigin ? 'Origin' : isDest ? 'Destination' : `Stop ${stop.sequence_order} (Transit Stop)`}
              </div>
              <div style="font-size: 13px; font-weight: 600; margin-top: 2px;">${stop.location_name}</div>
              <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Status: ${stop.status || 'PENDING'}</div>
            </div>
          `);

          allBoundsPoints.push([stop.latitude, stop.longitude]);
        });
      } else if (origin?.latitude && destination?.latitude) {
        // Fallback straight corridor
        const coords: [number, number][] = [
          [origin.latitude, origin.longitude],
          [destination.latitude, destination.longitude]
        ];
        const directLine = L.polyline(coords, { color: '#38bdf8', weight: 3, opacity: 0.8 }).addTo(map);
        layersRef.current.activeRoute = directLine;
        coords.forEach(c => allBoundsPoints.push(c));
      }

      // 3. Render Proposed / Preview Alternative Route (Dashed amber/violet line)
      if (showPreview && previewRoutePoints && previewRoutePoints.length > 0) {
        const previewCoords: [number, number][] = previewRoutePoints
          .filter(p => p.latitude && p.longitude)
          .map(p => [p.latitude, p.longitude]);

        if (previewCoords.length >= 2) {
          const previewLine = L.polyline(previewCoords, {
            color: '#f59e0b', // amber alternative
            weight: 3.5,
            opacity: 0.9,
            dashArray: '8, 8'
          }).addTo(map);

          layersRef.current.previewRoute = previewLine;
          previewCoords.forEach(c => allBoundsPoints.push(c));

          // Highlight intermediate alternative stops (e.g. Colombo)
          previewRoutePoints.forEach((stop, idx) => {
            if (!stop.latitude || !stop.longitude) return;
            if (idx > 0 && idx < previewRoutePoints.length - 1) {
              const stopHtml = `
                <div style="
                  width: 28px;
                  height: 28px;
                  background-color: #d97706;
                  border: 2px solid #fbbf24;
                  border-radius: 6px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  color: white;
                  font-family: monospace;
                  font-size: 11px;
                  font-weight: bold;
                  box-shadow: 0 0 12px rgba(245, 158, 11, 0.7);
                ">
                  ★${idx}
                </div>
              `;
              const stopIcon = L.divIcon({
                html: stopHtml,
                className: 'custom-alt-stop-marker',
                iconSize: [28, 28],
                iconAnchor: [14, 14]
              });

              const marker = L.marker([stop.latitude, stop.longitude], { icon: stopIcon }).addTo(markers);
              marker.bindPopup(`
                <div style="font-family: sans-serif; font-size: 12px; color: #0f172a; padding: 2px 4px;">
                  <div style="font-weight: bold; color: #d97706; text-transform: uppercase;">Proposed Transit Hub</div>
                  <div style="font-size: 13px; font-weight: 600; margin-top: 2px;">${stop.location_name}</div>
                  <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Bypass routing for: ${previewRouteName || 'Alternative Route'}</div>
                </div>
              `);
            }
          });
        }
      }

      // 4. Render Current Location Live Position Marker
      if (currentLocation?.latitude && currentLocation?.longitude) {
        const isCritical = isColdChainCritical;
        const pingColor = isCritical ? '#f43f5e' : '#06b6d4';

        const liveIconHtml = `
          <div style="position: relative; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;">
            <div style="
              position: absolute;
              width: 32px;
              height: 32px;
              border-radius: 50%;
              background: ${pingColor};
              opacity: 0.35;
              animation: pulse 1.5s infinite;
            "></div>
            <div style="
              position: relative;
              width: 22px;
              height: 22px;
              border-radius: 50%;
              background: ${pingColor};
              border: 2px solid #ffffff;
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              box-shadow: 0 0 10px rgba(0,0,0,0.5);
            ">
              🚚
            </div>
          </div>
        `;

        const liveIcon = L.divIcon({
          html: liveIconHtml,
          className: 'custom-live-marker',
          iconSize: [34, 34],
          iconAnchor: [17, 17]
        });

        const liveMarker = L.marker([currentLocation.latitude, currentLocation.longitude], { icon: liveIcon }).addTo(markers);
        liveMarker.bindPopup(`
          <div style="font-family: sans-serif; font-size: 12px; color: #0f172a; padding: 2px 4px;">
            <div style="font-weight: bold; color: #0284c7; text-transform: uppercase;">Current Live Position</div>
            <div style="font-size: 13px; font-weight: 600; margin-top: 2px;">${currentLocation.name}</div>
            ${coldChainEnabled ? `
              <div style="margin-top: 4px; padding: 3px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; ${isCritical ? 'background: #ffe4e6; color: #e11d48;' : 'background: #cffafe; color: #0891b2;'}">
                ❄ Telemetry: ${currentTemperature !== null && currentTemperature !== undefined ? `${currentTemperature.toFixed(1)}°C` : 'Active'} ${isCritical ? '(CRITICAL EXCURSION)' : '(NORMAL)'}
              </div>
            ` : ''}
            <div style="font-size: 10px; color: #64748b; margin-top: 4px;">Source: Demo GPS Simulation</div>
          </div>
        `);

        allBoundsPoints.push([currentLocation.latitude, currentLocation.longitude]);
      }

      // 5. Render Disruption Layer
      if (showDisruptions && disruptions && disruptions.length > 0) {
        disruptions.forEach((d) => {
          if (!d.latitude || !d.longitude) return;

          const isHigh = d.severity === 'CRITICAL' || d.severity === 'HIGH';
          const zoneColor = isHigh ? '#e11d48' : '#f59e0b';

          // Circle hazard perimeter
          L.circle([d.latitude, d.longitude], {
            radius: 45000, // 45km radius
            color: zoneColor,
            fillColor: zoneColor,
            fillOpacity: 0.18,
            weight: 1.5,
            dashArray: '4, 4'
          }).addTo(dLayer);

          // Hazard Icon marker
          const hazardHtml = `
            <div style="
              width: 30px;
              height: 30px;
              background-color: ${zoneColor};
              border: 2px solid #ffffff;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              font-size: 14px;
              box-shadow: 0 0 14px ${zoneColor};
            ">
              ⚠
            </div>
          `;

          const hazardIcon = L.divIcon({
            html: hazardHtml,
            className: 'custom-hazard-marker',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
          });

          const dMarker = L.marker([d.latitude, d.longitude], { icon: hazardIcon }).addTo(dLayer);
          dMarker.bindPopup(`
            <div style="font-family: sans-serif; font-size: 12px; color: #0f172a; padding: 2px 4px; max-width: 200px;">
              <div style="font-weight: bold; color: ${zoneColor}; text-transform: uppercase;">
                ${d.severity} DISRUPTION: ${d.type}
              </div>
              <div style="font-size: 13px; font-weight: bold; margin-top: 2px;">${d.name}</div>
              <div style="font-size: 11px; color: #475569; margin-top: 2px;">Location: ${d.location}</div>
              ${d.expected_duration_days ? `<div style="font-size: 11px; color: #475569;">Duration: ~${d.expected_duration_days} days</div>` : ''}
              ${d.description ? `<p style="font-size: 11px; margin-top: 4px; line-height: 1.3; color: #334155;">${d.description}</p>` : ''}
            </div>
          `);

          allBoundsPoints.push([d.latitude, d.longitude]);
        });
      }

      // 6. Render Fleet Assets Layer
      if (showFleet && fleetAssets && fleetAssets.length > 0) {
        fleetAssets.forEach((f) => {
          if (!f.latitude || !f.longitude) return;

          const isRec = f.is_recommended_redeployment;
          const isIdle = f.status === 'IDLE';
          const bgCol = isRec ? '#eab308' : isIdle ? '#f97316' : '#10b981';

          const fleetHtml = `
            <div style="
              width: 26px;
              height: 26px;
              background-color: ${bgCol};
              border: 2px solid #ffffff;
              border-radius: 6px;
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              font-size: 12px;
              box-shadow: 0 0 8px rgba(0,0,0,0.5);
            ">
              ${f.is_refrigerated ? '❄' : '🚚'}
            </div>
          `;

          const fIcon = L.divIcon({
            html: fleetHtml,
            className: 'custom-fleet-marker',
            iconSize: [26, 26],
            iconAnchor: [13, 13]
          });

          const fMarker = L.marker([f.latitude, f.longitude], { icon: fIcon }).addTo(fLayer);
          fMarker.bindPopup(`
            <div style="font-family: sans-serif; font-size: 12px; color: #0f172a; padding: 2px 4px;">
              <div style="font-weight: bold; color: ${bgCol};">
                ${f.asset_identifier} (${f.asset_type})
              </div>
              <div style="font-size: 11px; color: #475569; margin-top: 2px;">Position: ${f.current_location}</div>
              <div style="font-size: 11px; color: #475569;">Capacity: ${f.capacity || ''} ${f.capacity_unit || ''}</div>
              <div style="font-size: 11px; color: #475569;">Status: <b>${f.status}</b></div>
              ${f.is_refrigerated ? '<div style="color: #0891b2; font-weight: bold; font-size: 10px; margin-top: 2px;">✓ Refrigerated Reefer</div>' : ''}
              ${isRec ? '<div style="background: #fef08a; color: #854d0e; padding: 2px 4px; border-radius: 4px; font-weight: bold; font-size: 10px; margin-top: 4px;">⚡ Recommended for Redeployment</div>' : ''}
            </div>
          `);

          allBoundsPoints.push([f.latitude, f.longitude]);
        });
      }

      // Auto-fit bounds
      if (allBoundsPoints.length > 0) {
        const bounds = L.latLngBounds(allBoundsPoints);
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 8 });
      }

      // Invalidate size to ensure proper tile tiling inside responsive modals/dashboards
      setTimeout(() => {
        map.invalidateSize();
      }, 100);

    } catch (err) {
      console.error('Error updating Leaflet map layers:', err);
      setHasError(true);
    }
  }, [
    origin,
    destination,
    currentLocation,
    activeRoutePoints,
    previewRoutePoints,
    previewRouteName,
    disruptions,
    fleetAssets,
    showDisruptions,
    showFleet,
    showPreview,
    coldChainEnabled,
    currentTemperature,
    isColdChainCritical,
    shipmentsLayer
  ]);

  const handleFitBounds = () => {
    const map = mapInstanceRef.current;
    if (!map) return;
    const pts: L.LatLngExpression[] = [];
    if (activeRoutePoints && activeRoutePoints.length > 0) {
      activeRoutePoints.forEach(p => { if (p.latitude && p.longitude) pts.push([p.latitude, p.longitude]); });
    }
    if (previewRoutePoints && previewRoutePoints.length > 0) {
      previewRoutePoints.forEach(p => { if (p.latitude && p.longitude) pts.push([p.latitude, p.longitude]); });
    }
    if (currentLocation?.latitude && currentLocation?.longitude) {
      pts.push([currentLocation.latitude, currentLocation.longitude]);
    }
    if (pts.length > 0) {
      map.fitBounds(L.latLngBounds(pts), { padding: [40, 40], maxZoom: 8 });
    }
  };

  if (hasError) {
    return (
      <div 
        style={{ height }}
        className="w-full bg-[#0d1424] border border-slate-800 rounded-xl flex flex-col items-center justify-center p-6 text-center space-y-3"
      >
        <AlertTriangle className="w-8 h-8 text-amber-500" />
        <div>
          <p className="text-sm font-semibold text-slate-200">Map view temporarily unavailable</p>
          <p className="text-xs text-slate-400 mt-1">Route, waypoint, and telemetry details remain fully accessible.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full rounded-xl overflow-hidden border border-slate-800 bg-[#0d1424] shadow-inner group">
      {/* Map Canvas */}
      <div ref={mapContainerRef} style={{ height }} className="w-full z-0" />

      {/* Floating Header Badge */}
      <div className="absolute top-3 left-3 z-[400] flex items-center gap-2 pointer-events-auto">
        <div className="px-3 py-1 rounded-lg bg-slate-900/90 border border-slate-700/80 backdrop-blur-md text-xs text-slate-200 flex items-center gap-2 shadow-lg">
          <Navigation className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-bold tracking-wide">
            {previewRoutePoints && previewRoutePoints.length > 0 
              ? `Previewing: ${previewRouteName || 'Alternative Route'}`
              : 'Interactive Logistics Corridor'}
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        </div>
      </div>

      {/* Interactive Controls Strip (Top Right) */}
      {showControls && (
        <div className="absolute top-3 right-3 z-[400] flex items-center gap-1.5 pointer-events-auto">
          {/* Fit Route */}
          <button
            onClick={handleFitBounds}
            title="Fit Route to View"
            className="p-1.5 bg-slate-900/90 hover:bg-slate-800 border border-slate-700 text-slate-300 rounded-lg transition-colors shadow-md backdrop-blur-md"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>

          {/* Toggle Disruptions */}
          <button
            onClick={() => setShowDisruptions(!showDisruptions)}
            title="Toggle Disruption Zones"
            className={`px-2.5 py-1 text-[11px] font-semibold border rounded-lg transition-colors flex items-center gap-1 shadow-md backdrop-blur-md ${
              showDisruptions
                ? 'bg-rose-950/80 border-rose-800 text-rose-300'
                : 'bg-slate-900/80 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            <AlertTriangle className="w-3 h-3" />
            <span>Hazards</span>
          </button>

          {/* Toggle Fleet Assets */}
          <button
            onClick={() => setShowFleet(!showFleet)}
            title="Toggle Fleet Layer"
            className={`px-2.5 py-1 text-[11px] font-semibold border rounded-lg transition-colors flex items-center gap-1 shadow-md backdrop-blur-md ${
              showFleet
                ? 'bg-emerald-950/80 border-emerald-800 text-emerald-300'
                : 'bg-slate-900/80 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            <Truck className="w-3 h-3" />
            <span>Fleet</span>
          </button>

          {/* Toggle Preview Route if present */}
          {previewRoutePoints && previewRoutePoints.length > 0 && (
            <button
              onClick={() => setShowPreview(!showPreview)}
              title="Toggle Alternative Route Preview"
              className={`px-2.5 py-1 text-[11px] font-semibold border rounded-lg transition-colors flex items-center gap-1 shadow-md backdrop-blur-md ${
                showPreview
                  ? 'bg-amber-950/80 border-amber-800 text-amber-300'
                  : 'bg-slate-900/80 border-slate-700 text-slate-400'
              }`}
            >
              <Compass className="w-3 h-3" />
              <span>Alternative</span>
            </button>
          )}
        </div>
      )}

      {/* Bottom Floating Legend */}
      <div className="absolute bottom-3 left-3 z-[400] pointer-events-auto">
        <div className="px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800/90 backdrop-blur-md text-[11px] text-slate-300 flex flex-wrap items-center gap-3 shadow-lg">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span>Origin</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
            <span>Position</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500" />
            <span>Destination</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 bg-sky-400 inline-block" />
            <span>Active Corridor</span>
          </div>
          {previewRoutePoints && previewRoutePoints.length > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-0.5 bg-amber-400 border-b border-dashed inline-block" />
              <span>Proposed Bypass</span>
            </div>
          )}
          {showDisruptions && (
            <div className="flex items-center gap-1.5">
              <span className="text-rose-400 font-bold">⚠</span>
              <span>Disruption</span>
            </div>
          )}
          {coldChainEnabled && (
            <div className="flex items-center gap-1.5 text-cyan-400">
              <ThermometerSnowflake className="w-3 h-3" />
              <span>Cold Chain</span>
            </div>
          )}
          <span className="text-[10px] text-slate-400/80 border-l border-slate-700/80 pl-2">
            © OpenStreetMap contributors
          </span>
        </div>
      </div>
    </div>
  );
};
