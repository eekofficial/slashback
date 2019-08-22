import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cashback.settings')
django.setup()

from time import sleep
from decimal import Decimal
# from datetime import timedelta

# import requests
from admitad import api

# from django.utils import timezone

from cashback.settings import ID, CLIENT_ID, CLIENT_SECRET
from cashback_app import models

client_id = CLIENT_ID
client_secret = CLIENT_SECRET

scope = 'statistics public_data advcampaigns_for_website'
client = api.get_oauth_client_client(
    client_id,
    client_secret,
    scope
)


# def rate(base, target):
#     date = (timezone.now() - timedelta(1)).strftime("%d.%m.%Y")
#     payload = {'base': base, 'target': target, 'date' : date}
#     headers = client.transport._headers
#     r = requests.get('https://api.admitad.com/currencies/rate/', params=payload, headers=headers)
#     return r.json()['rate']


while True:
    try:
        shops = []
        current = True
        offset = 0
        while current:
            current = client.CampaignsForWebsite.get(ID, limit=500, offset=offset)['results']
            offset += 500
            shops.extend(current)
        shops = [shop for shop in shops if shop['connection_status'] == 'active']
        shops = {shop['id']: shop for shop in shops}

        for shop in models.Shop.objects.all():
            try:
                if shop.offer_id in shops:
                    info = shops[shop.offer_id]
                    shop.done = True
                    if 'image' in info:
                        shop.photo = info['image']
                    shop.site = info['site_url']
                    shop.psite = info['gotolink']
                    percent = Decimal(0)
                    for a in info['actions_detail']:
                        if a['type'] == 'sale':
                            for b in a['tariffs']:
                                for c in b['rates']:
                                    if c['is_percentage']:
                                        percent = max(percent, Decimal(c['size']))
                    shop.percent = percent
                else:
                    shop.done = False
                shop.save()
            except BaseException as exception:
                print(type(exception).__name__ + ': ' + str(exception))

            sleep(0.1)

    except BaseException as exception:
        print(type(exception).__name__ + ': ' + str(exception))

    try:
        pass

    except BaseException as exception:
        print(type(exception).__name__ + ': ' + str(exception))

    sleep(10)
