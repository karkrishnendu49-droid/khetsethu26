import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronRight, Leaf, X } from 'lucide-react';
import { api, fmt } from '../lib/api';
import { KMap } from '../components/KMap';

const STEPS = ['The problem', 'Your Khet', 'Market opportunity', 'Market suggestion', 'Buyer matching', 'The order', 'Logistics', 'Live route & logistics', 'Delivery', 'Price transparency', 'KhetSetu impact'];
const COPY = [
  'Multiple intermediaries can hide value between the farm and the family buying produce.',
  'Meet Arjun Das, a small farmer in Nadia, West Bengal, growing Grade A tomatoes.',
  'KhetSetu surfaces verified buyers within a practical distance — without the guesswork.',
  'A transparent prototype match explains why FreshMart is a strong fit for this listing.',
  'FreshMart Retail is looking for 500 kg of tomatoes at a fair ₹25/kg.',
  'One order keeps the farmer, buyer and route visible from the start.',
  'Rahul Logistics brings a mini truck and a scheduled pickup from Nadia.',
  'A live road route from Arjun\'s farm in Nadia to FreshMart in Kolkata — distance, time and transport cost calculated in real time.',
  'The order moves through pickup, transit and delivery with clear updates.',
  'The direct route makes the farmer share visible: 73.5% in this simulated scenario.',
  'A simpler route can improve farmer realization by 38.9% — simulated demonstration data.'];
const FALLBACK = { distance_km: 115.7, duration_min: 104, transport_cost: 1750, source: 'estimate', geometry: [[23.471, 88.5565], [22.5726, 88.3639]] };

export default function Demo() {
  const nav = useNavigate();
  const destination = localStorage.getItem('ks_user') ? '/app/dashboard' : '/';
  const [step, setStep] = useState(1);
  const [route, setRoute] = useState(null);
  const total = STEPS.length;
  const isRouteStep = STEPS[step - 1] === 'Live route & logistics';

  useEffect(() => {
    if (isRouteStep && !route) {
      api.get('/geo/route', { params: { from_lat: 23.471, from_lon: 88.5565, to_lat: 22.5726, to_lon: 88.3639 } })
        .then(r => setRoute(r.data)).catch(() => setRoute(FALLBACK));
    }
  }, [isRouteStep, route]);

  return <div className="demo-page">
    <header><Link className="logo" data-testid="brand-logo" to="/"><span className="logo-mark"><Leaf size={18} /></span><span>KhetSetu<small>खेतसेतु</small></span></Link><span className="demo-label">SIH 2026 · PRESENTATION MODE</span><Link data-testid="demo-exit-link" to="/">Exit demo <X size={15} /></Link></header>
    <main>
      <div className="demo-progress"><span>{String(step).padStart(2, '0')}</span><div><b style={{ width: `${step / total * 100}%` }} /></div><span>{total}</span></div>
      <p className="eyebrow">GUIDED LIVE DEMO</p>
      <h1>{STEPS[step - 1]}</h1>
      <p className="demo-copy">{COPY[step - 1]}</p>
      {isRouteStep ? <div className="demo-route" data-testid="demo-route-step">
        {route ? <>
          <div className="demo-route-metrics">
            <span data-testid="demo-route-distance"><small>DISTANCE</small><b>{route.distance_km} km</b></span>
            <span data-testid="demo-route-eta"><small>ETA</small><b>{Math.floor(route.duration_min / 60)}h {route.duration_min % 60}m</b></span>
            <span data-testid="demo-route-cost"><small>TRANSPORT</small><b>₹{fmt(route.transport_cost)}</b></span>
            <span data-testid="demo-route-source"><small>SOURCE</small><b>{route.source === 'osrm' ? 'Live · OSRM' : 'Estimated'}</b></span>
          </div>
          <KMap testId="demo-route-map" height={280} route={route.geometry} markers={[
            { lat: 23.471, lon: 88.5565, color: '#3f7a4b', popup: '<b>Farmer</b><br/>Arjun Das · Nadia, West Bengal' },
            { lat: 22.5726, lon: 88.3639, color: '#dcaa4f', popup: '<b>Buyer</b><br/>FreshMart Retail · Kolkata' }]} />
        </> : <p className="demo-copy">Calculating the live route…</p>}
      </div> : <div className="demo-metric"><span>{step === 1 ? '₹18 → ₹42/kg' : step === total - 1 ? '73.5% farmer share' : step === total ? '38.9% improvement' : 'KhetSetu'}</span><small>SIMULATED DEMO SCENARIO</small></div>}
    </main>
    <footer className="demo-controls">
      <span>Step {step} of {total}</span>
      <div>
        <button data-testid="demo-skip-button" className="text-button" onClick={() => nav(destination)}>Skip</button>
        {step > 1 && <button data-testid="demo-previous-button" className="secondary-button" onClick={() => setStep(step - 1)}>Previous</button>}
        {step < total ? <button data-testid="demo-next-button" className="primary-button" onClick={() => setStep(step + 1)}>Next <ChevronRight size={16} /></button> : <button data-testid="demo-finish-button" className="primary-button" onClick={() => nav(destination)}>Finish demo <ChevronRight size={16} /></button>}
      </div>
    </footer>
  </div>;
}
