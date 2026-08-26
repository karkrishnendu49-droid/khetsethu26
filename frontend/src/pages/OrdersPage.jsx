import { useEffect, useState } from 'react';
import { ChevronRight, MapPin } from 'lucide-react';
import { api, fmt } from '../lib/api';
import { KMap } from '../components/KMap';

function RoutePanel({ orderId }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { api.get(`/orders/${orderId}/logistics`).then(r => setData(r.data)).catch(() => setError('Route unavailable right now.')); }, [orderId]);
  if (error) return <div className="route-panel"><p className="muted">{error}</p></div>;
  if (!data) return <div className="route-panel"><p className="muted">Calculating route…</p></div>;
  const { pickup, delivery, route } = data;
  return (
    <div className="route-panel" data-testid={`route-panel-${orderId}`}>
      <div className="route-metrics">
        <span data-testid={`route-distance-${orderId}`}><small>Distance</small><b>{route.distance_km} km</b></span>
        <span data-testid={`route-eta-${orderId}`}><small>ETA</small><b>{Math.floor(route.duration_min / 60)}h {route.duration_min % 60}m</b></span>
        <span data-testid={`route-cost-${orderId}`}><small>Transport</small><b>₹{fmt(route.transport_cost)}</b></span>
        <span className="tag" data-testid={`route-source-${orderId}`}>{route.source === 'osrm' ? 'LIVE ROUTE · OSRM' : 'ESTIMATED ROUTE'}</span>
      </div>
      <KMap testId={`logistics-map-${orderId}`} height={300} route={route.geometry} markers={[
        { lat: pickup.lat, lon: pickup.lon, color: '#3f7a4b', popup: `<b>Farmer pickup</b><br/>${pickup.name}<br/>${pickup.label}` },
        { lat: delivery.lat, lon: delivery.lon, color: '#dcaa4f', popup: `<b>Buyer delivery</b><br/>${delivery.name}<br/>${delivery.label}` }]} />
      <div className="route-endpoints">
        <span><i className="dot-pin green" />Pickup: {pickup.name} · {pickup.label}</span>
        <ChevronRight size={14} />
        <span><i className="dot-pin gold" />Delivery: {delivery.name} · {delivery.label}</span>
      </div>
    </div>
  );
}

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [openRoute, setOpenRoute] = useState(null);
  useEffect(() => { api.get('/orders').then(r => setOrders(r.data)); }, []);
  const next = { pending: 'accepted', accepted: 'pickup_scheduled', pickup_scheduled: 'in_transit', in_transit: 'delivered', delivered: 'completed' };
  const update = async (o) => {
    if (next[o.status]) {
      const { data } = await api.patch(`/orders/${o.order_id}/status`, { status: next[o.status] });
      setOrders(orders.map(x => x.order_id === o.order_id ? data : x));
    }
  };
  return <>
    <div className="page-heading"><div><p className="eyebrow">FARM TO BUYER</p><h1>Orders</h1><p className="muted">Follow every handoff until your produce is complete.</p></div></div>
    <section className="panel table-panel">{orders.map(o => <div key={o.order_id}>
      <div className="order-card" data-testid={`order-card-${o.order_id}`}>
        <div><span className="order-id">{o.order_id}</span><h3>{o.product} <small>{o.quantity} kg</small></h3><p>{o.delivery_location}</p></div>
        <span className={`status ${o.status}`}>{o.status.replaceAll('_', ' ')}</span>
        <div className="order-total"><b>₹{fmt(o.quantity * o.price)}</b><small>+ ₹{fmt(o.transport_cost)} transport</small></div>
        <button data-testid={`view-route-${o.order_id}`} className="text-button" onClick={() => setOpenRoute(openRoute === o.order_id ? null : o.order_id)}><MapPin size={15} /> {openRoute === o.order_id ? 'Hide route' : 'Route'}</button>
        <button data-testid={`advance-order-${o.order_id}`} className="secondary-button" disabled={!next[o.status]} onClick={() => update(o)}>{next[o.status] ? `Mark ${next[o.status].replace('_', ' ')}` : 'Complete'} <ChevronRight size={15} /></button>
      </div>
      {openRoute === o.order_id && <RoutePanel orderId={o.order_id} />}
    </div>)}</section>
  </>;
}
