# KhetSetu — API & Integrations Guide

KhetSetu uses a backend service layer so no API keys are ever exposed in the frontend.
All external providers used for the SIH prototype are **free and keyless**, and every
service degrades gracefully to clearly labelled demo data if unreachable.

## Providers

| Capability | Provider | Key required | Fallback |
|---|---|---|---|
| Map tiles | OpenStreetMap / CARTO (rendered client-side with Leaflet) | No | Static demo route panel |
| Routing (distance / ETA) | OSRM public server | No | Haversine estimate (×1.3 road factor, 35 km/h) |
| Geocoding | Nominatim (OpenStreetMap) | No | Built-in West Bengal gazetteer |
| Weather | Open-Meteo | No | Labelled "Demo Weather Data" |
| Market prices | Seeded prototype data | `MARKET_API_KEY` for a future verified API | Labelled "Demo / Prototype Data" |

## Service layer (backend)

```
/backend
  /config    settings.py            — env-driven configuration
  /routes    geo, weather, market, logistics, integrations
  /services  geocoding_service, routing_service, weather_service,
             market_price_service, matching_service, map_service
  /utils     db, auth, cache (TTL), geo (haversine + gazetteer)
```

## Key endpoints

- `GET /api/geo/geocode?q=Nadia, West Bengal`
- `GET /api/geo/route?from_lat=&from_lon=&to_lat=&to_lon=` → distance_km, duration_min, transport_cost, geometry, source
- `GET /api/weather?lat=&lon=` → temperature, rainfall, humidity, condition, forecast, demo flag
- `GET /api/market-prices?crop=&location=&date=` → crop, market, location, price, unit, date, source
- `GET /api/orders/{order_id}/logistics` (auth) → pickup, delivery, live route
- `GET /api/map/overview` (auth) → listings, buyers, markets for the marketplace map
- `GET /api/admin/integrations` + `POST /api/admin/integrations/test/{maps|weather|market}` (admin)

## Adding a real API key later

1. **Obtain the key** from the provider (e.g. a paid map/routing vendor, a weather vendor,
   or a verified government market-price API such as an Agmarknet gateway).
2. **Add it to `/app/backend/.env`** using the placeholders in `.env.example`
   (`MAP_API_KEY=`, `WEATHER_API_KEY=`, `MARKET_API_KEY=`). Never put keys in frontend code.
3. **Restart the backend**: `sudo supervisorctl restart backend`.
4. **Test it** from Admin → API & Integrations using the [Test Maps] / [Test Weather] /
   [Test Market Prices] buttons, or via curl:
   `curl "$BACKEND_URL/api/market-prices?crop=Tomato"`.

## Caching

Backend TTL caches avoid unnecessary external requests:
geocoding 24 h · routes 6 h · weather 30 min · market prices 1 h.
