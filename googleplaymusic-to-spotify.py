#!/usr/bin/env python

import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import util

# Authenticate
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

# Define the files
file_zip       = 'data/takeout-20200628T085613Z-001.zip'
file_xlsx      = 'data/takeout-20200628T085613Z-001.xlsx'
file_decorated = 'data/takeout-20200628T085613Z-001-decorated.xlsx'
file_no_match  = 'data/takeout-20200628T085613Z-001-no-match.xlsx'
playlists      = [  # Define the playlist that should be re-created in Spotify
    'Børnesange til bilen',
    'Thumbs Up',
    'Arbejdsmusik - rap',
    'Vinteren kommer',
    'Quentin Tarantino Takeover',
    'Cecilia Bartoli',
    'Warm Scandinavian morning',
]

# Parse the google takeout file into a pandas dataframe
try:
    df = pd.read_excel(file_xlsx)
except FileNotFoundError:
    df = util.read_google_takeout_zipfile(file_zip)
    print(df.describe())
    print(df.head(3).T)
    df.to_excel(file_xlsx, index=False)
    print(f'Processed file written to: {file_xlsx}')
print(df.Playlist.value_counts())

# Try to get song informations from spotify
try:
    df_decorated = pd.read_excel(file_decorated)
except FileNotFoundError:
    df[['spotify_track_id', 'spotify_track_name', 'spotify_track_album', 'spotify_track_artist', 'query']] = df.apply(
        lambda row: util.spotify_find_track_id(sp, row['Title'], row['Artist'], row['Album'], market='DK'), axis=1, result_type="expand")
    df_decorated = df
    df_decorated.to_excel(file_decorated, index=False)

# Debug
df_bad            = df_decorated[df_decorated['spotify_track_id'].isna()]
df_weird_match    = df_decorated[(df_decorated['spotify_track_id'].notna()) & (df_decorated['spotify_track_name'].str.lower() != df_decorated['Title'].str.lower())]
num_total         = len(df_decorated)
num_no_match      = len(df_bad)
num_match         = num_total - num_no_match
num_partial_match = len(df_weird_match)
df_bad.to_excel(file_no_match, index=False)
print()
print(f'Processed {num_total} tracks. {num_match} track were matched up, but {num_no_match} had no spotify matches. {num_partial_match} matches were not exact.')
print()

# print('Not possible to map to spotify tracks')
# print(df_bad)
# print()
# print('Non exact matches')
# print(df_weird_match[['Title', 'spotify_track_name']])

# Create the playlist from the trackIds
for playlist in playlists:

    # Make sure the numbers are listed the same order as in the Google playlists
    df_playlist = df_decorated[df_decorated['Playlist'] == playlist].copy()
    df_playlist.sort_values(by='Playlist Index', inplace=True)
    df_playlist.reset_index(inplace=True, drop=True)

    # Create the playlist or append to it if it already exists
    track_ids = df_playlist[df_playlist['spotify_track_id'].notna()]['spotify_track_id'].tolist()
    util.spotify_create_playlist_with_track_list(playlist, track_ids)
