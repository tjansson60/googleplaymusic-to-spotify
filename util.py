#!/usr/bin/env python

import os
import html
import numpy as np
import pandas as pd
import zipfile
import tqdm
import pprint
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pandarallel import pandarallel
pandarallel.initialize(nb_workers=4)

# https://spotipy.readthedocs.io/en/2.13.0/
# https://github.com/plamere/spotipy/tree/master/examples


def read_google_takeout_zipfile(filename, debug=False):
    playlistpath = 'Takeout/Google Play Music/Playlists/'
    df_list = []
    with zipfile.ZipFile(filename, 'r') as f:
        for name in tqdm.tqdm(f.namelist()):
            if playlistpath in name:
                if name.endswith(".csv"):
                    playlist = name.replace(playlistpath, '').split('/')[0]
                    _df = pd.read_csv(f.open(name), encoding='utf-8')
                    _df['Playlist'] = playlist
                    try:
                        _df['Duration (min)'] = _df['Duration (ms)'] / (1000 * 60)
                    except KeyError:
                        _df['Duration (min)'] = np.nan
                    df_list.append(_df)

    df = pd.concat(df_list)

    # Remove entries with no values in title or artist
    df.dropna(subset=['Title', 'Artist'], inplace=True)

    # Remove columns with only nan values
    df.dropna(axis=1, how='all')

    # convert HTML characters to strings in pandas dataframe
    df['Title']  = df['Title'].astype(str).apply(html.unescape)
    df['Artist'] = df['Artist'].astype(str).apply(html.unescape)

    # df.applymap(lambda x: html.unescape(x) if pd.notnull(x) else x)
    df['Title']  = df['Title'].replace("&#39;", "'")
    df['Artist'] = df['Artist'].replace("&#39;", "'")

    if debug:
        print('Playlists found and number of songs in each')
        print(df.groupby('Playlist')['Duration (min)'].agg(['sum', 'count']))
        print()
        print(df.head(3).T)
        print()

    return df


def spotify_find_track_id(sp, name, artist, album=None, debug=False):
    query = f'{name} - {artist}'
    result = sp.search(q=query, limit=1)

    if debug:
        print(query)
        pprint.pprint(result)

    try:
        track_id     = result['tracks']['items'][0]['id']
        track_name   = result['tracks']['items'][0]['name']
        track_album  = result['tracks']['items'][0]['album']['name']
        track_artist = result['tracks']['items'][0]['album']['artists'][0]['name']
        assert name.lower() == track_name.lower(), f'{name.lower()} != {track_name.lower()}'
        assert artist.lower() == track_artist.lower(), f'{artist.lower()} != {track_artist.lower()}'
        if debug:
            print(track_id, track_name, track_artist, track_album)
    except:
        track_id = np.nan
        print(name, artist)

    return track_id


def spotify_create_playlist_with_track_list(playlist_name, track_list, public=False, description="Exported from Google Play Music"):

    # Login as a user so the data can be written to the playlists of the user
    scope = "user-library-read playlist-modify-public playlist-modify-private playlist-read-private"
    username = os.environ['SPOTIPY_USER']
    token = spotipy.util.prompt_for_user_token(username, scope=scope,
        client_id=os.environ['SPOTIPY_CLIENT_ID'],
        client_secret=os.environ['SPOTIPY_CLIENT_SECRET'],
        redirect_uri=os.environ['SPOTIPY_REDIRECT_URI'])
    sp = spotipy.Spotify(auth=token)

    # Check if a playlist already exists
    playlist_search_results = sp.current_user_playlists()
    playlists = {item['name']: item['id'] for item in playlist_search_results['items']}
    try:
        # Try to use a existing playlist of the same name
        playlist_id = playlists[playlist_name]
        print(f'Playlist called "{playlist_name}" already exists with id="{playlist_id}"')
    except KeyError:
        # Create the playlist
        playlist_result = sp.user_playlist_create(username, playlist_name, public=public, description=description)
        playlist_id = playlist_result['id']

    # If the playlist already exists do not try to readd the numbers to the list, only the difference
    try:
        playlist_track_response = sp.playlist_tracks(playlist_id, offset=0, fields='items.track.id')
        existing_tracks = list(set([item['track']['id'] for item in playlist_track_response['items']]))
        tracks = [track for track in track_list if track not in existing_tracks]
    except KeyError:
        tracks = track_list

    # Add the tracks to the playlist
    if len(tracks):
        print(f'Uploading {len(tracks)} new tracks to the playlist "{playlist_name}"')
        sp.user_playlist_add_tracks(username, playlist_id, tracks)
    else:
        print(f'No tracks to upload to "{playlist_name}". Already existing or not found on Spotify.')