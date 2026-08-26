import { useEffect, useState } from 'react';
import { api, fmt } from '../lib/api';

const DOT = { connected: '#6fbf73', demo: '#dcaa4f', error: '#e0745c', not_configured: '#8f8163' };
const LABEL = { connected: 'Connected', demo: 'Demo Mode', error: 'Error', not_configured: 'Not Configured' };

function Integrations() {
  const [list, setList] = useState(null);
  const [results, setResults] = useState({});
  const [busy, setBusy] = useState('');
  useEffect(() => { api.get('/admin/integrations').then(r => setList(r.data.integrations)).catch(() => setList([])); }, []);
  const test = async (s) => {
    setBusy(s);
    try { const { data } = await api.post(`/admin/integrations/test/${s}`); setResults(r => ({ ...r, [s]: data })); }
    catch (e) { setResults(r => ({ ...r, [s]: { result: 'failed', detail: 'Test failed to run.' } })); }
    finally { setBusy(''); }
  };
  return (
    <section className="panel" data-testid="integrations-panel">
      <div className="panel-title"><h2>API & Integrations</h2><span className="tag">NO KEYS EXPOSED</span></div>
      {!list ? <p className="muted">Checking integrations…</p> : <div className="integration-list">{list.map(i => (
        <div className="integration-row" key={i.service} data-testid={`integration-row-${i.service}`}>
          <div><h3>{i.label}</h3>
            <span className="int-status" data-testid={`integration-status-${i.service}`}><i className="int-dot" style={{ background: DOT[i.status] }} />{LABEL[i.status]}</span></div>
          <div><p className="int-detail">{i.detail}</p>
            {results[i.service] && <p className="int-result" data-testid={`test-result-${i.service}`}>
              {results[i.service].result === 'success' ? '✓ Success' : results[i.service].result === 'demo' ? '● Demo Mode' : '✕ Failed'} — {results[i.service].detail}{results[i.service].latency_ms != null ? ` · ${results[i.service].latency_ms} ms` : ''}</p>}</div>
          {i.service !== 'geolocation' && <button className="secondary-button" data-testid={`test-${i.service}-button`} disabled={busy === i.service} onClick={() => test(i.service)}>{busy === i.service ? 'Testing…' : `Test ${i.label.replace(' API', '')}`}</button>}
        </div>))}</div>}
    </section>
  );
}

export default function Admin() {
  const [m, setM] = useState(null);
  useEffect(() => { api.get('/admin/metrics').then(r => setM(r.data)); }, []);
  if (!m) return <div className="loading">Loading admin view…</div>;
  return <>
    <div className="page-heading"><div><p className="eyebrow">OPERATIONS / ADMIN</p><h1>See the whole bridge.</h1><p className="muted">A clear picture of the network moving produce forward.</p></div><span className="tag">SIMULATED DEMO METRICS</span></div>
    <div className="stats-grid admin-stats">{[['Farmers', m.farmers], ['Buyers', m.buyers], ['Active listings', m.listings], ['Active orders', m.orders], ['Avg farmer share', `${m.farmer_share}%`], ['Avg price gap', `₹${m.price_gap}`]].map(([a, b], i) => <div className="stat" data-testid={`admin-metric-${i}`} key={a}><span>{a}</span><strong>{fmt(b)}</strong><small>across KhetSetu</small></div>)}</div>
    <Integrations />
    <section className="panel analyzer"><div><p className="eyebrow">SUPPLY CHAIN ANALYZER</p><h2>Fewer layers. More value retained.</h2><p className="muted">Compare the traditional route with a direct KhetSetu connection.</p></div><div className="chain traditional-chain"><span>Traditional</span>{['Farmer', 'Trader', 'Wholesaler', 'Distributor', 'Retail'].map(x => <b key={x}>{x}<i>→</i></b>)}<strong>₹18/kg</strong></div><div className="chain direct-chain"><span>KhetSetu</span>{['Farmer', 'FPO / Buyer', 'Logistics', 'Consumer'].map(x => <b key={x}>{x}<i>→</i></b>)}<strong>₹25/kg</strong></div></section>
  </>;
}
