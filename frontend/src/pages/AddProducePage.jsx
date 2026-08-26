import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronRight, LocateFixed } from 'lucide-react';
import { api } from '../lib/api';
import { KMap } from '../components/KMap';

export default function AddProduce() {
  const nav = useNavigate();
  const [form, setForm] = useState({ crop: 'Tomato', quantity: 500, unit: 'kg', grade: 'Grade A', harvest_date: '2026-04-05', expected_price: 25, description: '', village: '', district: 'Nadia', state: 'West Bengal', latitude: null, longitude: null });
  const [locStatus, setLocStatus] = useState('');
  const [error, setError] = useState('');

  const useMyLocation = () => {
    if (!navigator.geolocation) { setLocStatus('denied'); return; }
    setLocStatus('locating');
    navigator.geolocation.getCurrentPosition(
      pos => { setForm(f => ({ ...f, latitude: pos.coords.latitude, longitude: pos.coords.longitude })); setLocStatus('granted'); },
      () => setLocStatus('denied'), { timeout: 8000 });
  };

  const save = async (e) => {
    e.preventDefault();
    const location = [form.village, form.district, form.state].filter(Boolean).join(', ');
    try { await api.post('/produce', { ...form, location }); nav('/app/produce'); }
    catch (err) { setError(err.response?.data?.detail || 'Unable to save listing.'); }
  };

  return <>
    <div className="page-heading"><div><p className="eyebrow">NEW LISTING</p><h1>Add produce</h1><p className="muted">Tell verified buyers what is ready from your Khet.</p></div></div>
    <form className="panel form-panel" onSubmit={save}>
      <div className="form-grid">
        <label>Crop<select data-testid="produce-crop-input" value={form.crop} onChange={e => setForm({ ...form, crop: e.target.value })}><option>Tomato</option><option>Potato</option><option>Onion</option><option>Rice</option><option>Wheat</option></select></label>
        <label>Quantity<input data-testid="produce-quantity-input" type="number" min="1" required value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} /></label>
        <label>Unit<select data-testid="produce-unit-input" value={form.unit} onChange={e => setForm({ ...form, unit: e.target.value })}><option>kg</option><option>tonnes</option><option>boxes</option></select></label>
        <label>Grade<select data-testid="produce-grade-input" value={form.grade} onChange={e => setForm({ ...form, grade: e.target.value })}><option>Grade A</option><option>Grade B</option><option>Mixed</option></select></label>
        <label>Harvest date<input data-testid="produce-date-input" type="date" required value={form.harvest_date} onChange={e => setForm({ ...form, harvest_date: e.target.value })} /></label>
        <label>Expected price / kg<input data-testid="produce-price-input" type="number" min="1" required value={form.expected_price} onChange={e => setForm({ ...form, expected_price: e.target.value })} /></label>
        <label>Village<input data-testid="produce-village-input" value={form.village} onChange={e => setForm({ ...form, village: e.target.value })} placeholder="e.g. Fulia" /></label>
        <label>District<input data-testid="produce-district-input" required value={form.district} onChange={e => setForm({ ...form, district: e.target.value })} /></label>
        <label className="wide">State<input data-testid="produce-state-input" required value={form.state} onChange={e => setForm({ ...form, state: e.target.value })} /></label>
        <div className="wide">
          <div className="loc-actions">
            <button type="button" data-testid="use-my-location-button" className="secondary-button" onClick={useMyLocation}><LocateFixed size={16} /> {locStatus === 'locating' ? 'Locating…' : 'Use my location'}</button>
            {locStatus === 'granted' && <span className="loc-note" data-testid="location-confirmed-note">Location captured — confirm the pin below, or adjust your village/district.</span>}
            {locStatus === 'denied' && <span className="loc-note" data-testid="location-denied-note">Location permission unavailable — no problem, your village and district will be used.</span>}
            {!locStatus && <span className="loc-note">Optional: pin your exact farm location for better buyer matching.</span>}
          </div>
          {form.latitude != null && <KMap testId="produce-location-map" height={230} markers={[{ lat: form.latitude, lon: form.longitude, color: '#3f7a4b', popup: '<b>Your farm pickup point</b>' }]} />}
        </div>
        <label className="wide">Description<textarea data-testid="produce-description-input" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Anything buyers should know?" /></label>
      </div>
      {error && <p className="error" data-testid="produce-form-error">{error}</p>}
      <div className="form-actions"><Link data-testid="produce-cancel-link" className="secondary-button" to="/app/produce">Cancel</Link><button data-testid="publish-produce-button" className="primary-button">Publish produce <ChevronRight size={16} /></button></div>
    </form>
  </>;
}
