import os
from urllib.parse import quote_plus
import time
import sys

import requests
from requests.exceptions import Timeout

from utils import rate_limited

spotify_access_token = {}
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

@rate_limited(9)
def _spotify_search(query):
    while True:
        print(f'querying for {query}', file=sys.stderr)
        try:
            r = requests.get(
                f'https://api.spotify.com/v1/search?q={query}&type=track',
                timeout=5,
                headers={
                    'Content-type': 'application/json',
                    'Authorization': f"Bearer {spotify_access_token['access_token']}"
                })
        except Timeout:
            print('timed out...', file=sys.stderr)
            time.sleep(1)
            continue
        if r.status_code == 403 or r.status_code == 502:
            # wait 11 seconds before trying again if we get forbidden
            print('got forbidden from spotify', file=sys.stderr)
            time.sleep(11)
            continue
        try:
            return r.json()
        except ValueError as e:
            print('================', file=sys.stderr)
            print(query, file=sys.stderr)
            print(e, file=sys.stderr)
            print(r, file=sys.stderr)
            print(r.status_code, file=sys.stderr)
            print(r.text, file=sys.stderr)
            raise

sqc = {}
def spotify_search(query):
    global sqc
    global spotify_access_token
    if 'access_token' not in spotify_access_token:
        r = requests.post('https://accounts.spotify.com/api/token',
                          auth=requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
                          data={'grant_type': 'client_credentials'})
        if r.status_code == 200:
            spotify_access_token.update(r.json())
        else:
            r.raise_for_status()
    query = quote_plus(query.encode('utf-8'))
    if query in sqc:
        return sqc[query]
    r = _spotify_search(query)
    sqc[query] = r
    return r
