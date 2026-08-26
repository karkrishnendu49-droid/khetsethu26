from services.market_price_service import price_for_crop, demand_for_crop

WEIGHTS = {'crop': 0.30, 'quantity': 0.20, 'price': 0.20, 'distance': 0.15, 'demand': 0.15}
CROP_DEMAND = {'tomato': 100, 'potato': 90, 'onion': 85, 'rice': 80, 'wheat': 78}

def compute_match(produce: dict, distance_km: float):
    crop = (produce.get('crop') or '').lower()
    crop_score = CROP_DEMAND.get(crop, 70)

    q = float(produce.get('quantity') or 0)
    if q <= 0: quantity_score = 40
    elif q < 50: quantity_score = 60
    elif q < 200: quantity_score = 85
    elif q <= 1000: quantity_score = 100
    elif q <= 2000: quantity_score = 85
    else: quantity_score = 70

    market = price_for_crop(produce.get('crop'))
    expected = float(produce.get('expected_price') or 0)
    if market and expected > 0:
        ratio = expected / market
        price_score = 100 if ratio <= 1 else 85 if ratio <= 1.1 else 65 if ratio <= 1.25 else 45
    else:
        price_score = 70

    d = distance_km if distance_km is not None else 150
    distance_score = 100 if d <= 25 else 90 if d <= 50 else 80 if d <= 100 else 60 if d <= 200 else 40

    demand = demand_for_crop(produce.get('crop'))
    demand_score = min(100, 60 + demand * 3) if demand is not None else 70

    factors = {'crop': crop_score, 'quantity': quantity_score, 'price': price_score,
               'distance': distance_score, 'demand': demand_score}
    score = round(sum(WEIGHTS[k] * v for k, v in factors.items()))

    parts = []
    parts.append('strong crop match' if crop_score >= 90 else 'reasonable crop fit')
    if quantity_score >= 90: parts.append('suitable quantity')
    parts.append('competitive price' if price_score >= 85 else 'price above market range')
    parts.append('short transportation distance' if distance_score >= 80 else 'longer transportation distance')
    if demand_score >= 90: parts.append('high market demand')
    explanation = (', '.join(parts[:-1]) + ' and ' + parts[-1] + '.').capitalize()

    return {'score': score, 'explanation': explanation, 'factors': factors, 'distance_km': round(d, 1)}
