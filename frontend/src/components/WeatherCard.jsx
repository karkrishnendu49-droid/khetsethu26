import { useEffect, useState } from 'react';
import { CloudSun, Droplets, CloudRain } from 'lucide-react';
import { api } from '../lib/api';

export const WeatherCard = ({ user }) => {
  const [w, setW] = useState(null);
  useEffect(() => {
    api.get('/weather', { params: { lat: user?.latitude || 23.471, lon: user?.longitude || 88.5565 } })
      .then(r => setW(r.data)).catch(() => setW(null));
  }, [user?.latitude, user?.longitude]);
  if (!w) return null;
  return (
    <section className="panel weather-panel" data-testid="weather-panel">
      <div className="panel-title"><h2>Farm weather · {user?.district || 'Nadia'}</h2>
        <span className="tag" data-testid="weather-source-tag">{w.demo ? 'DEMO WEATHER DATA' : 'LIVE · OPEN-METEO'}</span></div>
      <div className="weather-now">
        <CloudSun size={36} />
        <div><strong data-testid="weather-temperature">{Math.round(w.temperature)}°C</strong><span>{w.condition}</span></div>
        <div className="weather-meta">
          <span><Droplets size={14} /> Humidity {w.humidity}%</span>
          <span><CloudRain size={14} /> Rain {w.rainfall} mm</span>
        </div>
      </div>
      <div className="weather-forecast">{w.forecast.map((f, i) =>
        <div key={i} data-testid={`weather-forecast-${i}`}><small>{f.date.slice(5)}</small><b>{Math.round(f.max)}° / {Math.round(f.min)}°</b><span>{f.condition}</span></div>)}
      </div>
    </section>
  );
};
