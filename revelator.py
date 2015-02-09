# http://music.abcradio.net.au/api/v1/plays/search.json?from=2014-05-26T10:00:00.000Z&limit=100&offset=0&order=asc&station=doublej&to=2014-05-26T12:00:00.000Z

from abcradio_api import generate_playlist

DAYS = [
    '2014-05-12',
    '2014-05-19',
    '2014-05-26',
    '2014-06-02',
    '2014-06-09',
    '2014-06-16',
    '2014-06-23',
    '2014-06-30',
    '2014-07-07',
    '2014-07-14',
    '2014-07-21',
    '2014-07-28',
    '2014-08-04',
    '2014-08-11',
    '2014-08-18',
    '2014-08-25',
    '2014-09-01',
    '2014-09-08',
    '2014-09-15',
    '2014-09-22',
    '2014-09-29',
    '2014-10-06',
    '2014-10-13',
    '2014-10-20',
    '2014-10-27',
    '2014-11-03',
    '2014-11-10',
    '2014-11-17',
    '2014-11-24',
    '2014-12-01',
    '2014-12-08',
    '2015-01-12',
    #'2015-01-19', (was beat the drum)
    '2015-01-26',
    '2015-02-02',
    '2015-02-09',
]

false_positives = [
    'spotify:track:4b5Xvdwe76VHiwvtkmsfaa'
]

if __name__ == '__main__':

    global_tracks = []
    for day in DAYS:
        tracks = generate_playlist("doublej", day, "10:00:00.000", "12:00:00.000")
        with open('revelator_%s.spotify' % day, 'w') as f:
            for href in tracks:
                if href not in global_tracks:
                    global_tracks.append(href)
                f.write(href + '\n')
    with open('revelator_all.spotify', 'w') as f:
        for href in global_tracks:
            if href in false_positives:
                continue
            f.write(href + '\n')
