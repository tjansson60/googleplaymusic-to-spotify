#!/usr/bin/env python

from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import util

# Parse the google takeout file into a pandas dataframe
df = util.read_google_takeout_zipfile('data/takeout-20200628T085613Z-001.zip')
print(df.Playlist.value_counts())

playlists = [
    'Børnesange til bilen',
    'Thumbs Up',
    'Arbejdsmusik - rap',
    'Vinteren kommer',
    'Quentin Tarantino Takeover',
    'Cecilia Bartoli',
    'Warm Scandinavian morning',
]

# Set up the Spotify crendentials
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
for playlist in playlists:
    df_playlist = df[df['Playlist'] == playlist].copy()

    # Decorate the dataframe with the spotify track ids so we can create the playlist
    df_playlist['trackId'] = df_playlist.apply(lambda row: util.spotify_find_track_id(sp, row['Title'], row['Artist'], row['Album']), axis=1)

    # Create the playlist from the trackIds
    print(playlist)
    print(df_playlist[df_playlist['trackId'].isna()])
    print()
    track_ids       = df_playlist[df_playlist['trackId'].notna()]['trackId'].tolist()
    util.spotify_create_playlist_with_track_list(playlist, track_ids)
