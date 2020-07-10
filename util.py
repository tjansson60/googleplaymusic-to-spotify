#!/usr/bin/env python

import os
import html
import numpy as np
import zipfile
import pandas as pd
import tqdm
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pandarallel import pandarallel
pandarallel.initialize()

# https://spotipy.readthedocs.io/en/2.13.0/
# https://github.com/plamere/spotipy/tree/master/examples


def get_spotify_instance():
    username = os.environ['SPOTIPY_USER']
    scope = "user-library-read playlist-modify-public playlist-modify-private playlist-read-private"

    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
    except KeyError:
        # Login as a user so the data can be written to the playlists of the user
        token = spotipy.util.prompt_for_user_token(username, scope=scope,
            client_id=os.environ['SPOTIPY_CLIENT_ID'],
            client_secret=os.environ['SPOTIPY_CLIENT_SECRET'],
            redirect_uri=os.environ['SPOTIPY_REDIRECT_URI'])
        sp = spotipy.Spotify(auth=token)
    return sp, username


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

    # Remove duplicates
    df.drop_duplicates(subset=['Title', 'Artist', 'Album', 'Playlist'], keep=False, inplace=True)

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


def spotify_find_track_id(sp, name, artist, album=None, debug=False, market=None):
    # How to write a query: https://developer.spotify.com/documentation/web-api/reference/search/search/ For example:
    # The query q=album:gold%20artist:abba&type=album returns only albums with the text “gold” in the album name and the
    # text “abba” in the artist name.
    # explicit=true

    # https://github.com/plamere/spotipy/issues/522
    # I used to get the same problem few days ago. My fix was to change the market where you are making the search. By
    # default I think it's using the "US" market, and for my searches I had to revert back to a "FR" market to get some
    # results.

    # First try with a specific market and if this does not work revert back to default US
    query = f'{name} {artist}'
    #query = 'artist:' + artist + ' track:' + name
    result = sp.search(q=query, limit=1, type='track', market=market)
    if not len(result['tracks']['items']):
        result = sp.search(q=query, limit=1, type='track')
        market = None

    if len(result['tracks']['items']):
        track_id     = result['tracks']['items'][0]['id']
        track_name   = result['tracks']['items'][0]['name']
        track_album  = result['tracks']['items'][0]['album']['name']
        track_artist = result['tracks']['items'][0]['album']['artists'][0]['name']
        if debug:
            print()
            print(track_id)
            print(name, artist, album)
            print(track_name, track_artist, track_album)
    else:
        track_id     = np.nan
        track_name   = np.nan
        track_album  = np.nan
        track_artist = np.nan
        print(f'No matches found for "{query}"')

    return track_id, track_name, track_album, track_artist, query


def spotify_create_playlist_with_track_list(
        playlist_name,
        track_list,
        public=False,
        description="Exported from GooglePlay Music"):

    # Authenticate and get credentials
    sp, username = get_spotify_instance()

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

        # Upload in chunks smaller than 100:
        # TODO: Add support for track positions
        for i in range(0, len(tracks), 99):
            tracks_chunk = tracks[i:i + 99]
            sp.user_playlist_add_tracks(username, playlist_id, tracks_chunk)
    else:
        print(f'No tracks to upload to "{playlist_name}". Already existing or not found on Spotify.')
