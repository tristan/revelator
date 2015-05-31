# http://music.abcradio.net.au/api/v1/plays/search.json?from=2014-05-26T10:00:00.000Z&limit=100&offset=0&order=asc&station=doublej&to=2014-05-26T12:00:00.000Z

import sys
import json
import re
from abcradio_api import generate_playlist

false_positives = [
    'spotify:track:4b5Xvdwe76VHiwvtkmsfaa'
]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Missing input file")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]

    global_tracks = []
    for block in data:
        start_time = block['start_time']
        end_time = block['end_time']
        m = re.match('^(?P<hour>\d\d):(?P<minute>\d\d)(?::(?P<second>\d\d)(?:\.(?P<milli>\d+))?)?$', start_time)
        if not m:
            print("invalid start time: %s" % start_time)
            sys.exit(1)
        start_time = "%02d:%02d:%02d.%03d" % tuple(int(y) if y is not None else  0 for y in m.groups())
        m = re.match('^(?P<hour>\d\d):(?P<minute>\d\d)(?::(?P<second>\d\d)(?:\.(?P<milli>\d+))?)?$', end_time)
        if not m:
            print("invalid end time: %s" % end_time)
            sys.exit(1)
        end_time = "%02d:%02d:%02d.%03d" % tuple(int(y) if y is not None else  0 for y in m.groups())
        station = block['station']
        for day in block['days']:
            tracks = generate_playlist(station, day, start_time, end_time)
            for href in tracks:
                if href not in global_tracks:
                    global_tracks.append(href)
    for href in global_tracks:
        if href in false_positives:
            continue
        sys.stdout.write(href + '\n')
