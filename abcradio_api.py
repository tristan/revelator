from urllib.parse import urlencode
import os
import re
import json
import sys

import requests
import requests.utils

from spotify import spotify_search

def get_playlist(station, frm, to, offset=0, limit=100):
    rval = []
    cfile = os.path.join(
        'cache',
        f'{station}_{frm.replace(":", "-")}_{to.replace(":", "-")}_{offset}_{limit}.txt')
    if os.path.exists(cfile):
        print(f"Loading data from cache file: {cfile}", file=sys.stderr)
        with open(cfile, 'rb') as inf:
            while True:
                line = inf.readline()
                if line == b'':
                    break
                line = line.decode('utf-8')
                line = line.strip().split('||')
                line = [line[0].split('+')] + line[1:]
                rval.append(line)
        return rval
    query_args = {
        'station': station,
        'from': frm,
        'to': to,
        'limit': limit,
        'offset': offset,
        'order': 'asc'
    }
    url = f'http://music.abcradio.net.au/api/v1/plays/search.json?{urlencode(query_args)}'
    print(f"Retreiving data from API: {url}", file=sys.stderr)
    r = requests.get(url)
    # fucking this shit \\" gets decoded to ", which breaks things
    content = r.content.replace(b'\\"', b'\\\\\\"')
    # then we have to decode any unicode escapes
    content = content.decode('unicode_escape')
    # then we have to make sure everything is utf
    pls = json.loads(content.encode('utf-8'))
    if 'items' in pls:
        print(f"found {len(pls['items'])} items for {frm}", file=sys.stderr)
        for item in pls['items']:
            if 'recording' not in item:
                continue
            rec = item['recording']
            title = rec['title'].replace(u"\u2019", u"'") # fix up broken shit
            artists = [a['name'] for a in rec['artists']]
            try:
                print('{} - {}'.format('+'.join(artists), title), file=sys.stderr)
            except UnicodeEncodeError:
                raise
            rval.append([artists, title])
    return rval

def write_cache(station, frm, to, offset, limit, input):
    cfile = os.path.join(
        'cache',
        f'{station}_{frm.replace(":", "-")}_{to.replace(":", "-")}_{offset}_{limit}.txt')
    if not os.path.exists('cache'):
        os.mkdir('cache')
    with open(cfile, 'w') as outf:
        for line in input:
            line = '||'.join(['+'.join(line[0])] + line[1:]) + '\n'
            outf.write(line)

pattern = re.compile(r'[\W_]+')

def strip(strng):
    """Strips non-alphanumeric characters from the string"""
    return pattern.sub('', strng.lower())

def pick_best_match(m1, m2, artists, name):
    if m1 is not None and m2 is None:
        return m1
    if m1 is None:
        return m2  # may be None too, but that doesn't matter

    name = strip(name)
    artists = [strip(a) for a in artists]
    m1_name = strip(m1['name'])
    m2_name = strip(m2['name'])
    m1_matching_artists = [strip(a['name']) for a in m1['artists'] if strip(a['name']) in artists]
    m2_matching_artists = [strip(a['name']) for a in m2['artists'] if strip(a['name']) in artists]
    m1_matching_artists.sort()
    m2_matching_artists.sort()

    m1_a_diff = abs(len(artists) - len(m1_matching_artists))
    m2_a_diff = abs(len(artists) - len(m2_matching_artists))
    # check if we have a better artist match in either option
    if m1_a_diff < m2_a_diff:
        return m1
    if m2_a_diff < m1_a_diff:
        return m2

    if m1_name == name and m2_name != name:
        return m1
    if m2_name == name and m1_name != name:
        return m2
    if m1_name == name and m2_name == name:
        # both things match, so it doesn't matter, just take the first
        return m1

    # check if name is a longer version of one of the options and not the other
    if m1_name in name and m2_name not in name:
        return m1
    if m2_name in name and m1_name not in name:
        return m2

    if name in m1_name and name not in m2_name:
        return m1
    if name in m2_name and name not in m1_name:
        return m2

    m1_n_diff = abs(len(name) - len(m1_name))
    m2_n_diff = abs(len(name) - len(m2_name))

    if (m2_name in name and m1_name in name) or \
       (m1_name not in name and m2_name not in name) or \
       (name in m1_name and name in m2_name) or \
       (name not in m1_name and name not in m2_name):
        if m1_n_diff < m2_n_diff:
            return m1
        if m2_n_diff < m1_n_diff:
            return m2

    # most likely they are the same, pick the one with has the territories i need!
    if 'DE' in m1['available_markets']:
        return m1
    if 'DE' in m2['available_markets']:
        return m2
    # well, maybe we just pick the one with the longest territories list and hope for the best
    if len(m1['available_markets']) > len(m2['available_markets']):
        return m1
    elif len(m2['available_markets']) > len(m1['available_markets']):
        return m2

    print("UNABLE TO FIGURE OUT BEST MATCH", file=sys.stderr)
    print(m1, file=sys.stderr)
    print("--------------", file=sys.stderr)
    print(m2, file=sys.stderr)
    print("==============", file=sys.stderr)

    return m1

def get_track(sr, artists, track_name):
    best_result = None
    track_name = track_name.lower()
    if 'tracks' in sr:
        for track in sr['tracks']['items']:
            if 'uri' in track:
                best_result = pick_best_match(best_result, track, artists, track_name)
    return best_result['uri'] if best_result is not None else None

MILO_HATES = []
with open("milohates.txt") as f:
    for line in f.readlines():
        cmtidx = line.find('#')
        if cmtidx > -1:
            line = line[:cmtidx]
        line = line.strip()
        if line != '':
            MILO_HATES.append(line)

CUSTOM_MATCHES = {}
with open("custommatches.txt") as f:
    for line in f.readlines():
        cmtidx = line.find('#')
        if cmtidx > -1:
            line = line[:cmtidx]
        line = line.strip()
        if line != '':
            artist, track, href = line.strip().rsplit(',', 2)
            CUSTOM_MATCHES[(artist, track)] = href

def generate_playlist(station, *args):
    # legacy shit!
    if len(args) == 3:
        day, frm, to = args
        # fix up hours to be padded with 0
        if frm[1] == ':':
            frm = f'0{frm}'
        if to[1] == ':':
            to = f'0{to}'
        frm = f'{day}T{frm}Z'
        to = f'{day}T{to}Z'
    elif len(args) == 2:
        frm, to = args
    pls = []
    offset = 0
    limit = 100
    while True:
        results = get_playlist(station, frm, to, offset, limit)
        pls.extend(results)
        write_cache(station, frm, to, offset, limit, results)
        if len(results) < limit:
            break
        offset += limit
    tracks = []
    for item in pls:
        if len(item) == 3:
            artists, title, href = item
        else:
            artists, title = item
            # check if we have a custom match for this artist, track
            custom_key = (','.join(artists), title)
            if custom_key in CUSTOM_MATCHES:
                href = CUSTOM_MATCHES[custom_key]
            else:
                # if not ask spotify
                href = get_track(spotify_search(
                    f"{' '.join(artists)} {title}"), artists, title)
        if href:
            # ignore shit that milo doesn't like
            if href in MILO_HATES:
                continue
            tracks.append(href)
            if len(item) == 2:
                item.append(href)
    if len(args) == 3:
        return tracks
    else:
        return [(item[0], item[1], item[2] if len(item) == 3 else '') for item in pls]
