# Revelator

This is a python script that pulls the playlists down from http://doublej.net.au
and generates a "best-fit" list of spotify uris.

# Public playlist

The playlist I generate with this can be found at:
http://open.spotify.com/user/1121834524/playlist/3WQEPPWdWnbnz3U0bbjnmE

# Requirements

```
requests
```

# Running

```
python revelator.py
```

output is `revelator_all.spotify`

# Managing results

All the playlists and matched tracks are stored in text files in the `cache/` folder.
It happens that sometimes the doublej playlist songs don't quite match ones on
spotify, and thus have no spotify entry in these cache files. You can edit them
manually, and next time they'll be included in the final output.

# History

This started out as a script to parse the playlists that Stu Harvey used to put on
the short.fast.loud facebook page and turn them into spotify playlists.

This was always a bit hit and miss as the facebook posted playlists often contained
spelling errors (which I tried to fix with google search suggestions, which was
also hit and miss) or Stu sometimes just didn't post the playlist (shit happens).

With the re-launch of doublej, they started providing a list of all the tracks played
on the station, so I poked around the network traffic a bit and figured out how
to call their api manually. Using this I can get quite a reasonable list of all the
tracks played over a particular period, So I decided to use it to build up a playlist
of Emma Swifts favoite songs!! (i.e. all the songs played on the doublej revelator
program).

I've played around with grabbing the short.fast.loud playlists with the same api
however last time I tried (which I'll admit was quite some time ago) the triplej
playlists wern't nearly as good as the doublej ones are so it didn't work out too
well.