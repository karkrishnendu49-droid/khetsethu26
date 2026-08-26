import { useEffect, useState } from 'react';
import { api, cropEmoji } from '../lib/api';

export default function Prices() {
  const [rows, setRows] = useState([]);
  useEffect(() => { api.get('/market-prices').then(r => setRows(r.data.rows)).catch(() => setRows([])); }, []);
  const byCrop = [...new Map(rows.map(r => [r.crop, r])).values()];
  const cards = ['Tomato', 'Potato', 'Onion'].map(c => byCrop.find(r => r.crop === c)).filter(Boolean);
  return <>
    <div className="page-heading"><div><p className="eyebrow">UNDERSTAND YOUR BAZAAR</p><h1>Market prices</h1><p className="muted">A simple view of current opportunities. No mystery, just a starting point.</p></div><span className="tag" data-testid="prices-source-tag">DEMO / PROTOTYPE DATA</span></div>
    <section className="price-hero panel"><div><span className="tag">TOMATO · MOST ACTIVE</span><h2>₹{cards[0]?.price || 28}<span>/kg</span></h2><p>+₹{(cards[0]?.price || 28) - (cards[0]?.previous || 26)} from last week · Demand <b className="positive">+{cards[0]?.demand || 12}%</b></p></div><div className="trend-chart"><i /><i /><i /><i /><i /><i /><i /></div><div className="recommendation"><span className="crop-icon">↗</span><div><b>Good time to compare buyers</b><p>Organized buyers are offering up to ₹32/kg.</p></div></div></section>
    <div className="price-cards">{cards.map((x, i) => <div className="price-card" data-testid={`price-card-${i}`} key={x.crop}><span className="crop-icon">{cropEmoji(x.crop)}</span><h3>{x.crop}</h3><strong>₹{x.price}<small>/kg</small></strong><span>Expected {x.range}</span><b className="positive">+{x.demand}% demand</b></div>)}</div>
    <section className="panel table-panel mandi-board">
      <div className="panel-title mandi-title"><h2>Mandi price board</h2><span className="tag">DEMO / PROTOTYPE DATA</span></div>
      <div className="table-head mandi-row"><span>Crop</span><span>Market</span><span>Location</span><span>Price</span><span>Date</span><span>Source</span></div>
      {rows.map((r, i) => <div className="table-row mandi-row" data-testid={`mandi-row-${i}`} key={i}>
        <div><span className="produce-thumb small-thumb">{cropEmoji(r.crop)}</span><b>{r.crop}</b></div>
        <span>{r.market}</span><span>{r.location}</span><strong>{r.price} {r.unit}</strong><span>{r.date}</span><span className="muted-cell">{r.source}</span>
      </div>)}
    </section>
    <div className="panel transparency"><div><p className="eyebrow">PRICE TRANSPARENCY</p><h2>Where does ₹34 go?</h2><p className="muted">A simulated tomato journey with one direct buyer route.</p></div><div className="share-ring"><strong>73.5%<small>farmer share</small></strong></div><div className="breakdown"><span><i className="farmer" />Farmer <b>₹25</b></span><span><i />Transportation <b>₹3</b></span><span><i />Storage & packaging <b>₹2</b></span><span><i />Retail <b>₹4</b></span></div></div>
  </>;
}
