import requests
from grab import spotify_search
import os
import re

def get_playlist(station, day, frm, to):
    rval = []
    cfile = os.path.join('cache', '%s_%s_%s_%s.txt' % (station, day, frm.replace(":", "-"), 
                                                   to.replace(":", "-")))
    if os.path.exists(cfile):
        with open(cfile) as inf:
            while True:
                line = inf.readline()
                if line == '':
                    break
                line = line.strip().split('||')
                line = [line[0].split('+')] + line[1:]
                rval.append(line)
        return rval
    frm = '%sT%sZ' % (day, frm)
    to = '%sT%sZ' % (day, to)
    r = requests.get('http://music.abcradio.net.au/api/v1/plays/search.json?from=%(from)s&station=%(station)s&limit=100&offset=0&order=asc&to=%(to)s' % {'from':frm, 'to':to, 'station': station})
    pls = r.json()
    if 'items' in pls:
        print('found %s items for %s' % (len(pls['items']), day))
        tracks = []
        for item in pls['items']:
            if 'recording' not in item:
                continue
            rec = item['recording']
            title = rec['title'].replace(u"\u2019", u"'") # fix up broken shit
            artists = [a['name'] for a in rec['artists']]
            try:
                print('%s - %s' % ('+'.join(artists), title))
            except UnicodeEncodeError:
                raise
            rval.append([artists, title])
    return rval

def write_cache(station, day, frm, to, input):
    cfile = os.path.join('cache', '%s_%s_%s_%s.txt' % (station, day, frm.replace(":", "-"), 
                                                   to.replace(":", "-")))
    with open(cfile, 'w') as outf:
        for line in input:
            print line
            outf.write('||'.join(['+'.join(line[0])] + line[1:]) + '\n')

pattern = re.compile('[\W_]+')

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

    if (m2_name in name and m1_name in name) or (m1_name not in name and m2_name not in name) or (name in m1_name and name in m2_name) or (name not in m1_name and name not in m2_name):
        if m1_n_diff < m2_n_diff:
            return m1
        if m2_n_diff < m1_n_diff:
            return m2

    # most likely they are the same, pick the one with has the territories i need!
    if 'DE' in m1['album']['availability']['territories']:
        return m1
    if 'DE' in m2['album']['availability']['territories']:
        return m2
    # well, maybe we just pick the one with the longest territories list and hope for the best
    if len(m1['album']['availability']['territories']) > len(m2['album']['availability']['territories']):
        return m1
    elif len(m2['album']['availability']['territories']) > len(m1['album']['availability']['territories']):
        return m2

    print "UNABLE TO FIGURE OUT BEST MATCH"
    print m1
    print "--------------"
    print m2
    print "=============="

    return m1

def get_track(sr, artists, track_name):
    best_result = None
    track_name = track_name.lower()
    if 'info' in sr:
        if sr['info']['num_results'] > 0:
            for track in sr['tracks']:
                if 'href' in track:
                    best_result = pick_best_match(best_result, track, artists, track_name)
    return best_result['href'] if best_result is not None else None


def generate_playlist(station, day, frm, to):
    pls = get_playlist(station, day, frm, to)
    tracks = []
    for item in pls:
        if len(item) == 3:
            artists, title, href = item
        else:
            artists, title = item
            href = get_track(spotify_search('%s %s' % (' '.join(artists), title)), artists, title)
        if href:
            tracks.append(href)
            if len(item) == 2:
                item.append(href)
    write_cache(station, day, frm, to, pls)
    return tracks
