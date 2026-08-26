import { useEffect, useState } from 'react';
import { ChevronRight, Search, List, Map as MapIcon } from 'lucide-react';
import { api, cropEmoji } from '../lib/api';
import { KMap } from '../components/KMap';

export default function Marketplace() {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState('');
  const [view, setView] = useState('list');
  const [overview, setOverview] = useState(null);

  useEffect(() => { api.get('/marketplace', { params: { search } }).then(r => setItems(r.data)); }, [search]);
  useEffect(() => { api.get('/map/overview').then(r => setOverview(r.data)).catch(() => setOverview({ listings: [], buyers: [], markets: [] })); }, []);

  const markers = [
    ...(overview?.listings || []).map(l => ({ lat: l.latitude, lon: l.longitude, color: '#3f7a4b', popup: `<b>${l.crop}</b><br/>${l.quantity} ${l.unit} · ₹${l.expected_price}/kg<br/>${l.location}<br/>${l.distance_km} km from buyer · <b>${l.match_score}% match</b>` })),
    ...(overview?.buyers || []).map(b => ({ lat: b.latitude, lon: b.longitude, color: '#dcaa4f', popup: `<b>${b.name}</b><br/>Verified buyer<br/>${b.address}` })),
    ...(overview?.markets || []).map(m => ({ lat: m.latitude, lon: m.longitude, color: '#8a6f47', popup: `<b>${m.name}</b><br/>Mandi / market<br/>${m.location}` })),
  ];

  return <>
    <div className="page-heading"><div><p className="eyebrow">THE OPEN BAZAAR</p><h1>Find a better market.</h1><p className="muted">Verified buyers looking for produce like yours.</p></div>
      <div className="view-toggle" data-testid="marketplace-view-toggle">
        <button data-testid="marketplace-list-toggle" className={view === 'list' ? 'active' : ''} onClick={() => setView('list')}><List size={15} /> List view</button>
        <button data-testid="marketplace-map-toggle" className={view === 'map' ? 'active' : ''} onClick={() => setView('map')}><MapIcon size={15} /> Map view</button>
      </div></div>
    {view === 'list' ? <>
      <label className="search-box large-search"><Search size={17} /><input data-testid="marketplace-search-input" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search crop or location" /></label>
      <div className="market-grid">{items.map(p => <div className="market-card" data-testid={`market-card-${p.id}`} key={p.id}>
        <div className="market-top"><span className="produce-thumb">{cropEmoji(p.crop)}</span><span className="match" data-testid={`match-score-${p.id}`}>{p.match_score}% match</span></div>
        <h3>{p.crop}</h3><p>{p.quantity} {p.unit} · {p.grade}</p>
        <div className="market-meta"><span><b>₹{p.expected_price}/kg</b><small>asking price</small></span><span><b>{p.distance}</b><small>from buyer</small></span></div>
        <p className="match-note" data-testid={`match-explanation-${p.id}`}>{p.match_explanation}</p>
        <div className="market-buyer"><div className="avatar tiny">F</div><span><b>{p.buyer}</b><small>Verified buyer</small></span></div>
        <button data-testid={`request-purchase-${p.id}`} className="primary-button full" onClick={() => alert(`Purchase request sent to ${p.buyer}.`)}>Request purchase <ChevronRight size={16} /></button>
      </div>)}</div>
    </> : <div className="map-wrap" data-testid="marketplace-map-view">
      <KMap testId="marketplace-map" height={520} markers={markers} />
      <div className="map-legend">
        <span><i className="dot-pin green" />Farmer listings</span>
        <span><i className="dot-pin gold" />Verified buyers</span>
        <span><i className="dot-pin soil" />Mandis / markets</span>
      </div>
    </div>}
  </>;
}
