from math import radians, sin, cos, asin, sqrt

NADIA = (23.4710, 88.5565)
KOLKATA = (22.5726, 88.3639)

GAZETTEER = {
    'nadia': (23.4710, 88.5565), 'krishnanagar': (23.4058, 88.4907), 'kalyani': (22.9750, 88.4345),
    'ranaghat': (23.1740, 88.5642), 'kolkata': (22.5726, 88.3639), 'howrah': (22.5958, 88.2636),
    'barasat': (22.7228, 88.4800), 'siliguri': (26.7271, 88.3953), 'durgapur': (23.5204, 87.3119),
    'asansol': (23.6839, 86.9753), 'malda': (25.0108, 88.1411), 'burdwan': (23.2324, 87.8615),
    'west bengal': (22.9868, 87.8550), 'india': (22.3511, 78.6677),
}

def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))

def gazetteer_lookup(query):
    q = (query or '').lower()
    for name, coords in GAZETTEER.items():
        if name in q:
            return {'lat': coords[0], 'lon': coords[1], 'display_name': f'{name.title()}, India', 'source': 'gazetteer'}
    return None
