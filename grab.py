import requests
import re
try:
    from secret_keys import CLIENT_ID, CLIENT_SECRET
    facebook_supported = True
except:
    facebook_supported = False
import os, sys
import time
from utils import rate_limited
from urllib import quote_plus
from io import open
from requests.exceptions import Timeout

class SimpleFaceBookClient:
    def __init__(self):
        r = requests.get('https://graph.facebook.com/oauth/access_token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (CLIENT_ID, CLIENT_SECRET))
        self.access_token = r.text.split('=')[1]

    def get_raw(self, url):
        r = requests.get(url)
        return r.json()

    def get(self, path, **kwargs):
        kwargs['access_token'] = self.access_token
        params = '&'.join(['%s=%s' % (k,v) for k,v in kwargs.items()])
        return self.get_raw('https://graph.facebook.com/%s?%s' % (path, params))

def _google_suggestion(query):
    """E.G.: http://google.com/complete/search?client=firefox&q=less+than+jake+gainsville+rock+city
    returns:
    ["less than jake gainsville rock city",["less than jake gainesville rock city","less than jake gainesville rock city lyrics","less than jake gainesville rock city tab","less than jake gainesville rock city mp3","less than jake gainesville rock city album","less than jake gainesville rock city bass tab","less than jake gainesville rock city live","less than jake gainesville rock city chords","less than jake gainesville rock city video","less than jake gainesville rock city download mp3"]]
    """
    r = requests.get('http://google.com/complete/search?client=firefox&q=%s' % query)
    r = r.json()
    orig = r[0]
    if len(r) < 2 or len(r[1]) < 1:
        return None
    fixed = r[1][0]
    if orig != fixed:
        return fixed
    return None

gqc = {}    
def google_suggestion(query):
    global gqc
    query = quote_plus(query)
    if query in gqc:
        return gqc[query]
    r = _google_suggestion(query)
    gqc[query] = r
    return r

@rate_limited(9)
def _spotify_search(query):
    while True:
        print 'querying for', query
        try:
            r = requests.get('http://ws.spotify.com/search/1/track.json?q=%s' % query, timeout=5)
        except Timeout, t:
            print 'timed out...'
            time.sleep(1)
            continue
        if r.status_code == 403 or r.status_code == 502: # wait 11 seconds before trying again if we get forbidden
            print 'got forbidden from spotify'
            time.sleep(11)
            continue
        try:
            return r.json()
        except ValueError, e:
            print '================'
            print query
            print e
            print r
            print r.status_code
            print r.text
            raise

sqc = {}
def spotify_search(query):
    global sqc
    query = quote_plus(query)
    if query in sqc:
        return sqc[query]
    r = _spotify_search(query)
    sqc[query] = r
    return r

file_re = re.compile('^(?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})\.txt$')
track_ex_re = re.compile('(?P<artist>.+) - (?P<song>[^*]+)\n')

time_re = re.compile('^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})T(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})\+(?P<offset>[0-9]{4})$')
#pls_re = re.compile('SHORT\.FAST\.LOUD\. PLAYLIST (?P<day>[0-9]{2})\.(?P<month>[0-9]{2})\.(?P<year>[0-9]{2})', re.IGNORECASE)
pls_re = re.compile('PLAYLIST', re.IGNORECASE)

track_re = re.compile('(?P<song>.+) // (?P<artist>[^*]+)(?P<aussie>[*]+)?')

if __name__ == '__main__':
    client = SimpleFaceBookClient()
    r = client.get('shortfastloud/posts', fields='message')

    OUT_FILE = 'output.txt'
    ERR_FILE = 'notfound.txt'
    OUT_AUSSIE = 'output_aussie_only.txt'
    OUT_REPLACEMENTS = 'replacements.txt'
    OUT_MATCHES = 'matches.txt'
    outhrefs = set()
    aushrefs = set()
    failedqueries = set()
    replacements = dict()
    matches = dict()
    """
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, 'r') as inf:
            while True:
                l = inf.readline().strip()
                if l == '':
                    break
                outhrefs.add(l)
    if os.path.exists(OUT_AUSSIE):
        with open(OUT_AUSSIE, 'r') as inf:
            while True:
                l = inf.readline().strip()
                if l == '':
                    break
                aushrefs.add(l)
    if os.path.exists(ERR_FILE):
        with open(ERR_FILE, 'r') as inf:
            while True:
                l = inf.readline().strip()
                if l == '':
                    break
                failedqueries.add(l)
    """

    # find extras
    extrasfound = []
    for f in os.listdir('.'):
        m = file_re.match(f)
        if m:
            print 'adding extra playlist from: %s' % f
            with open(f, 'r') as inf:
                lines = [track_ex_re.match(x) for x in inf.readlines()]
                lines = ''.join(["%s // %s\n" % (x.group('song'), x.group('artist')) for x in lines if x is not None])
                message = "SHORT.FAST.LOUD. PLAYLIST %s.%s.%s\n\n%s" % (m.group('day'), m.group('month'), m.group('year'), lines)
            ex = dict(created_time="%s-%s-%sT00:00:00+0000" % (m.group('year'), m.group('month'), m.group('day')),
                      message=message)
            extrasfound.append(m.groupdict())
            r['data'].insert(0, ex)

    keepgoing = True
    while keepgoing:
        if len(r['data']) == 0:
            break
        for item in r['data']:
            message = item.get('message')
            if message is None:
                continue
            t = time_re.match(item.get('created_time', ''))
            if t is None:
                raise "missing created_time key"
            if t.group('year') == '2013':
                keepgoing = False
                break
            m = pls_re.search(message)
            if m is None:
                continue
            print item.get('created_time')
            for line in message.split('\n'):
                lm = track_re.match(line)
                if lm is None:
                    continue
                query = '%(artist)s %(song)s' % lm.groupdict()
                # manually fix weird things
                oquery = query = query.replace(u"\u2019", "'")
                while True:
                    try:
                        sr = spotify_search(query)
                    except KeyError:
                        print 'error processing:', query
                        sr = dict(info=dict(num_results=0))
                
                    #print query
                    written = False
                    if sr['info']['num_results'] > 0:
                        for track in sr['tracks']:
                            if 'href' in track:
                                matches[line] = '%s - %s' % (track['artists'][0]['name'], track['name'])
                                outhrefs.add(track['href'])
                                if lm.group('aussie') is not None:
                                    aushrefs.add(track['href'])
                                written = True
                                break
                    elif query == oquery:
                        fquery = google_suggestion(query)
                        # ignore random broken stuff
                        if fquery == "mowgli messua":
                            break
                        if fquery:
                            replacements[query] = fquery
                            query = fquery
                            continue
                    break
                if not written:
                    failedqueries.add(oquery)
        if keepgoing and 'paging' in r and 'next' in r['paging']:
            r = client.get_raw(r['paging']['next'])
        else:
            break
    with open(OUT_FILE, 'w') as outf:
        for l in outhrefs:
            outf.write(l + '\n')
    with open(OUT_AUSSIE, 'w') as outf:
        for l in aushrefs:
            outf.write(l + '\n')
    with open(ERR_FILE, 'w') as outf:
        for l in failedqueries:
            outf.write(l + '\n')
    with open(OUT_REPLACEMENTS, 'w') as outf:
        for l in replacements.items():
            outf.write("%s | %s\n" % l)
    with open(OUT_MATCHES, 'w') as outf:
        for l in matches.items():
            try:
                outf.write("%s | %s\n" % l)
            except UnicodeEncodeError:
                print l
                raise
