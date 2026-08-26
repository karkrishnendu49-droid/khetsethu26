import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const pin = (color) => L.divIcon({ className: 'kmap-pin', html: `<span class="kmap-dot" style="background:${color}"></span>`, iconSize: [22, 22], iconAnchor: [11, 11] });

export const KMap = ({ markers = [], route = null, height = 340, testId = 'khetsetu-map' }) => {
  const ref = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = L.map(ref.current, { scrollWheelZoom: false, tap: false });
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        attribution: '© Esri © OpenStreetMap contributors', maxZoom: 16,
      }).addTo(mapRef.current);
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', { maxZoom: 16 }).addTo(mapRef.current);
    }
    if (layerRef.current) layerRef.current.remove();
    const group = L.featureGroup();
    markers.filter(m => m.lat != null && m.lon != null).forEach(m => {
      const mk = L.marker([m.lat, m.lon], { icon: pin(m.color || '#dcaa4f') });
      if (m.popup) mk.bindPopup(m.popup);
      mk.addTo(group);
    });
    if (route && route.length > 1) L.polyline(route, { color: '#dcaa4f', weight: 3, opacity: 0.85 }).addTo(group);
    group.addTo(mapRef.current);
    layerRef.current = group;
    try {
      if (group.getLayers().length) mapRef.current.fitBounds(group.getBounds().pad(0.25));
      else mapRef.current.setView([23.2, 88.4], 8);
    } catch (e) { mapRef.current.setView([23.2, 88.4], 8); }
  }, [JSON.stringify(markers), JSON.stringify(route)]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => () => { if (mapRef.current) { mapRef.current.remove(); mapRef.current = null; } }, []);

  return <div data-testid={testId} className="kmap" style={{ height }} ref={ref} />;
};
