#!/usr/bin/env python

import numpy as np
import pandas as pd
import zipfile
import tqdm
#import spotipy  # https://spotipy.readthedocs.io/en/2.13.0/


def read_google_takeout_zipfile(filename):
    playlistpath = 'Takeout/Google Play Music/Playlists/'
    df_list = []
    with zipfile.ZipFile(filename, 'r') as f:
        for name in tqdm.tqdm(f.namelist()):
            if playlistpath in name:
                if name.endswith(".csv"):
                    playlist = name.replace(playlistpath, '').split('/')[0]
                    _df = pd.read_csv(f.open(name))
                    _df['Playlist'] = playlist
                    try:
                        _df['Duration (min)'] = _df['Duration (ms)'] / (1000 * 60)
                    except KeyError:
                        _df['Duration (min)'] = np.nan
                    df_list.append(_df)

    df = pd.concat(df_list)

    print('Playlists found and number of songs in each')
    print(df.groupby('Playlist')['Duration (min)'].agg(['sum', 'count']))
    print()
    print(df.head(3).T)
    print()

    return df


#def spotify:
#    spotify_client_id     = os.environ['spotify_client_id']
#    spotify_client_secret = os.environ['spotify_client_secret']



df = read_google_takeout_zipfile('data/takeout-20200628T085613Z-001.zip')
