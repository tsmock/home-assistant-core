from homeassistant.components.itron_riva_gen5.sensor import ItronApi, ItronRivaGen5Consumption, ItronRivaGen5Power, ItronRivaGen5Production
import csv
import os

import datetime
import time

TEST_HOST: str = "https://10.192.56.140:8081"
TEST_CERTIFICATE: str = """-----BEGIN CERTIFICATE-----
FIXME: DO NOT COMMIT
-----END CERTIFICATE-----"""
TEST_KEY: str = """-----BEGIN PRIVATE KEY-----
FIXME: DO NOT COMMIT
-----END PRIVATE KEY-----"""
with open(os.path.join(os.path.dirname(__file__), "data", 'cert.pem'), 'r') as f:
    TEST_CERT = f.read()
with open(os.path.join(os.path.dirname(__file__), "data", 'key.pem'), 'r') as f:
    TEST_KEY = f.read()

def test_real_data():
    api: ItronApi = ItronApi(None, TEST_HOST, TEST_CERTIFICATE, TEST_KEY)
    api.debug = os.path.join(os.path.dirname(__file__), "data")
    consumption: ItronRivaGen5Consumption = ItronRivaGen5Consumption(api)
    power: ItronRivaGen5Power = ItronRivaGen5Power(api)
    production: ItronRivaGen5Production = ItronRivaGen5Production(api)
    file = os.path.join(os.path.dirname(__file__), 'real_data.csv')
    with open(file, 'a') as f:
        field_names = ['date', 'consumption', 'power', 'production']
        writer = csv.DictWriter(f, fieldnames=field_names)
        if not os.path.exists(file):
            writer.writeheader()
        d = {'consumption': consumption, 'power': power, 'production': production}
        while True:
            time.sleep(1)
            k = {k: v.async_update() for k, v in d.items()}
            writer.writerow({'date': datetime.datetime.now().isoformat(), **k})

if __name__ == '__main__':
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    test_real_data()