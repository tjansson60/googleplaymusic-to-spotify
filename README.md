# Transfer Google Play Music Playlist to Spotify

After Google announced that Google Play Music would be shut down and moved to Youtube Music I decided I wanted to move my playlists to Spotify instead. 

Unfortunately neither companies makes this very easy, so I either had to pay some website for the transfer which usually entailed a subscription style payment model for this one-time transfer or do it my self, so I did the later. 

## Requirements
 * Python 3 with the requirements defined in the yaml file.
 * A zip file from Google Takeout that contains all the tracks from the playlists. 
 * A existing Spotify account and credentials we can use to make the new playlist in Spotify. 

### Python environment:
Install miniconda: https://docs.conda.io/en/latest/miniconda.html

And create the environment using the yaml file:
```bash
conda env create -n googleplaymusic-to-spotify -f googleplaymusic-to-spotify.lock.yml
```
Afterwards activate the environment:
```bash
conda activate googleplaymusic-to-spotify
```



 ## Extracting the playlist from Google Play Music
 On the page https://takeout.google.com/settings/takeout:
  * `Deselect all` and only select `Google Play Music` once the zip file has been downloaded put in the `data` folder and take note of the name which is used in the script. 
 
## Spotify credentials
Setup some shell variables or hardcode them in your version of the script. The scripts assumes the following variables exists and these are Spotify API credentials, so include in your `.bashrc` or similar:

```bash
export SPOTIPY_USER=''
export SPOTIPY_CLIENT_ID=''
export SPOTIPY_CLIENT_SECRET=''
export SPOTIPY_REDIRECT_URI="http://localhost:9090"
```
Get your credentials at https://developer.spotify.com/my-applications

# Running the script
This script does a couple of things:

 * Unwraps the annoying Goolge zip file into a single xlsx file with all the data (which can easily be read into a pandas dataframe).
 * Matches all the songs to Spotify songs as good as possible and saves the Spotify trackId, names artists etc to a new xlsx file that can be inspected. 
 * Goes through a list of playlists and tries to recreate the playlist in Spotify using the Spotify trackId's and the ordering of the tracks from the Google Play Music playlist. 
