CROP_IMAGES = {
    'Tomato': 'https://static.prod-images.emergentagent.com/jobs/3d32f513-0b87-458e-9987-231610df2547/images/9a6742622566f30a690f147b8c94e5e6565e97e370794967f28f4179527f6095.jpeg',
    'Potato': 'https://static.prod-images.emergentagent.com/jobs/3d32f513-0b87-458e-9987-231610df2547/images/7be33c43fbc1aa590f8c61b4a1120f2c3c52422bbf67342e73718ada99d12475.jpeg',
    'Onion': 'https://static.prod-images.emergentagent.com/jobs/3d32f513-0b87-458e-9987-231610df2547/images/31edd5a9ca161ff00e224c795a982ddc8338f10ea72c10a86653c7dd943c0618.jpeg',
    'Carrot': 'https://static.prod-images.emergentagent.com/jobs/3d32f513-0b87-458e-9987-231610df2547/images/7d03014a663b868b90d9ea4432cc47c7fee29d844085f489f3dd9cc6f966b8af.jpeg',
    'Cabbage': 'https://static.prod-images.emergentagent.com/jobs/3d32f513-0b87-458e-9987-231610df2547/images/909bbc823db232e5b927bd8e5a3b62fcdbd39f7b3e4d60bd2b4490184e823eff.jpeg',
    'Cauliflower': 'https://static.prod-images.emergentagent.com/jobs/3d32f513-0b87-458e-9987-231610df2547/images/7552298aae9be8e9a63217134db834e8268e27d24e48aa896fd6567a09f9de4e.jpeg',
    'Green Chili': 'https://static.prod-images.emergentagent.com/jobs/3d32f513-0b87-458e-9987-231610df2547/images/196760b6ac8c340bc77249c855796f81035862d1e0d5b7b464ad76e5a6abf48c.jpeg',
    'Brinjal': 'https://static.prod-images.emergentagent.com/jobs/3d32f513-0b87-458e-9987-231610df2547/images/5b2602b02fa6147b4695ba5462c1bfa85e578f5bb6015524d4456e6f6f2f339c.jpeg',
}
CROPS = list(CROP_IMAGES.keys())

def crop_image(crop):
    return CROP_IMAGES.get(crop, CROP_IMAGES['Tomato'])

def availability(quantity):
    q = float(quantity or 0)
    return 'sold_out' if q <= 0 else 'low_stock' if q < 100 else 'available'
