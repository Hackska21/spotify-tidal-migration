import json
import logging

from secrets import tidal_id, tidal_id_2, tidal_username, tidal_username_2, tidal_pwd, tidal_pwd_2, spotify_id, \
    spotify_id_2, spotify_username, spotify_username_2, spotify_discover_weekly_id, SPOTIPY_CLIENT_ID, \
    SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import sys
import tidalapi
import time
from pprint import pprint

# Options:
# connect_to_spotify()
# connect_to_tidal(tidal_username, tidal_pwd)
# delete_all_tidal_playlists(tidal_id, tidal_session)
# move_all_tidal_playlists_to_spotify()
# move_one_tidal_playlist_to_spotify(playlist_id)
# move_all_spotify_playlists_to_tidal()
# move_favourites_from_spotify_to_tidal()
# move_discover_weekly_from_spotify_to_tidal()
# copy_tidal_playlists_to_another_tidal_account()
# MIGRATE SPOTIFY ACCOUNT = COPY PLAYLISTS + SAVED TRACKS
# copy_spotify_playlists_to_another_spotify_account()
# copy_spotify_saved_tracks_to_another_spotify_account()
logger = logging.getLogger(__name__)

# Endpoints not in tidalapi
def get_tidal_create_playlist_url(tidal_id):
    return 'https://listen.tidal.com/v1/users/' + tidal_id + '/playlists'
def get_tidal_add_track_to_playlist_url(playlist_id):
    return 'https://listen.tidal.com/v1/playlists/' + playlist_id + '/items'
def get_tidal_find_track_url():
    return 'https://listen.tidal.com/v1/search/tracks'
def get_tidal_playlist(playlist_id):
    return 'https://listen.tidal.com/v1/playlists/' + playlist_id
def get_tidal_user_playlists(tidal_id):
    return 'https://listen.tidal.com/v1/users/' + tidal_id + '/playlists'

# Endpoints not in spotipy
def get_discover_weekly_playlist():
    return 'https://api.spotify.com/v1/users/spotify/playlists/'  + spotify_discover_weekly_id + '/tracks'

tidal_oldplaylists = []

def connect_to_spotify():
    scope = 'user-library-read'
    token = util.prompt_for_user_token(
        spotify_username,
        scope,
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI
    )

    if token:
        sp = spotipy.Spotify(auth=token)
    else:
        print("Can't get spotify token for " + spotify_username)
        sys.exit()

    return sp, token


def connect_to_tidal(tidal_username, tidal_pwd):
    tidal_session = tidalapi.Session()
    try:
        # tidal_session.login(tidal_username, tidal_pwd)
        # login, future = tidal_session.login_oauth()
        print("jelou")
        tidal_session.login_oauth_simple()

        oauth_file = 'tida-sesi'
        if tidal_session.check_login():
            # store current OAuth session
            data = {}
            data['token_type'] = {'data': tidal_session.token_type}
            data['session_id'] = {'data': tidal_session.session_id}
            data['access_token'] = {'data': tidal_session.access_token}
            data['refresh_token'] = {'data': tidal_session.refresh_token}
            with open(oauth_file, 'w') as outfile:
                json.dump(data, outfile)
        dummy = 0
    except requests.exceptions.HTTPError as e:
        print("Can't login to tidal for username=" + tidal_username + ", password=" + tidal_pwd)
        sys.exit()
    return tidal_session


def move_favourites_from_spotify_to_tidal():
    user = tidal_session.user
    user_favourites = user.favorites

    def _get_spotify_favourites(offset):
        return sp.current_user_saved_tracks(limit=20, offset=offset)

    offset = 0
    spotify_favourites = _get_spotify_favourites(offset)
    while spotify_favourites:
        for item in spotify_favourites['items']:
            track = item['track']
            track_id = _search_for_track_on_tidal(
                track['name'], track['artists'][0]['name']
            )
            if track_id > 0:
                user_favourites.add_track(track_id)
        offset = offset + 20
        spotify_favourites = _get_spotify_favourites(offset)


def delete_all_tidal_playlists(tidal_id, tidal_session):
    try:
        r = requests.request(
            'GET',
            get_tidal_user_playlists(tidal_id),
            headers={
                'x-tidal-sessionid': tidal_session.session_id,
                'if-none-match': '*'
            },
            params={
                'countryCode': 'US',
                'limit': 999
            }
        )
        playlists = [item['uuid'] for item in r.json()['items']]
    except requests.exceptions.RequestException as e:
        print("Could not get list of playlists")

    if playlists:
        for playlist in playlists:
            try:
                r = requests.request(
                    'DELETE',
                    get_tidal_playlist(playlist),
                    headers={
                        'x-tidal-sessionid': tidal_session.session_id,
                    },
                    params={
                        'countryCode': 'US'
                    }
                )
            except requests.exceptions.RequestException as e:
                print("Could not delete playlist " + playlist_id)


def move_all_tidal_playlists_to_spotify():
    pass
    # _add_tracks_to_spotify_playlist(track_ids, spotify_playlist_id)


def move_one_tidal_playlist_to_spotify(playlist_id):
    pass
    # _add_tracks_to_spotify_playlist(track_ids, spotify_playlist_id)


def move_all_spotify_playlists_to_tidal():
    get_tidal_old_playlists(tidal_id, tidal_session)
    playlists = sp.user_playlists(spotify_id)
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            if playlist['name'] not in tidal_oldplaylists:
                print("Workin on playlist:" + playlist['name'])
                _add_playlist_to_tidal(playlist, tidal_session)
            else:
                print("A playlist with name " + playlist['name'] + " already exists in TIDAL. Skipping...")
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None


def copy_tidal_playlists_to_another_tidal_account():
    get_tidal_old_playlists(tidal_id_2, tidal_session_2)
    playlists_to_copy = tidal_session_2.get_user_playlists(tidal_id)
    i=1
    for playlist in playlists_to_copy:
        #check if playlist with a same name already exists
        if playlist.name not in tidal_oldplaylists:
                print("Working on playlist " + str(i) + "/" + str(len(playlists_to_copy)) + ": " + playlist.name)
                playlist_id = _create_tidal_playlist(playlist.name, tidal_id_2, tidal_session_2)
                tracks = tidal_session_2.get_playlist_tracks(playlist.id)
                #add tracks to playlist_id
                _add_tracks_to_tidal_playlist(playlist_id, tracks, tidal_session_2)
        else:
                print("A playlist with name " + playlist.name + " already exists in TIDAL. Skipping...")
        i+=1

def move_discover_weekly_from_spotify_to_tidal():
    try:
        r = requests.request(
           'GET',
           get_discover_weekly_playlist(),
           headers={
               'Authorization': 'Bearer ' + sp_token
           }
        )
    except requests.exceptions.RequestException as e:
        print("Could not get Discovery Weekly playlist. Are you sure the ID is correct?")

    playlist = r.json()
    _add_playlist_to_tidal(playlist, tidal_session, playlist_name="Discover Weekly", tracks=playlist)


def _add_playlist_to_tidal(playlist, tidal_session, tracks=None, playlist_name=None):
    playlist_name_catch = playlist_name if playlist_name else playlist['name']
    playlist_id = _create_tidal_playlist(playlist_name_catch, tidal_id, tidal_session)

    if not playlist_id:
        return

    sanitized_tracks = []
    def _add_track_to_sanitized_list(tracks):
        for i, item in enumerate(tracks['items']):
            track = item['track']
            sanitized_tracks.append([
                track['name'], track['artists'][0]['name']
            ])

    tracks_catch = tracks if tracks else sp.user_playlist(playlist['owner']['id'], playlist['id'], fields="tracks,next")['tracks']
    _add_track_to_sanitized_list(tracks_catch)
    while tracks_catch['next']:
        tracks_catch = sp.next(tracks_catch)
        _add_track_to_sanitized_list(tracks_catch)
    _add_tracks_to_tidal_playlist(playlist_id, sanitized_tracks, tidal_session)


def dump(obj):
  for attr in dir(obj):
    print("obj.%s = %r" % (attr, getattr(obj, attr)))

def _add_tracks_to_tidal_playlist(playlist_id, tracks, tidal_session):
    url = get_tidal_add_track_to_playlist_url(playlist_id)
    #print(len(tracks))
    #for track in tracks:
#	print("INIZIO")
#	dump(track)
#	print("FINE")
    for track in tracks:
        tidal_track_id = track.id
        if tidal_track_id > -1:
            try:
                r = requests.request(
                    'POST',
                    url,
                    data={'trackIds':tidal_track_id, 'toIndex':1},
                    headers={
                        'x-tidal-sessionid': tidal_session.session_id,
                        'if-none-match': "*"
                    },
                    params={
                        'countryCode': 'US'
                    }
                )
            except requests.exceptions.RequestException as e:
                print('Error adding tracks to playlist: ' + e)
                # TODO: should add playlist name to CSV of failures

def get_tidal_old_playlists(tidal_id, tidal_session):
    try:
        r = tidal_session.request.request(
            'GET',
            get_tidal_user_playlists(tidal_id),
            params={
                'countryCode': 'US',
                'limit': 999
            }
        )
        # playlist = tidal_session.user.create_playlist("Example playlist", "An example of a playlist")
        playlists = [item['title'] for item in r.json()['items']]
    except requests.exceptions.RequestException as e:
        print("Could not get list of playlists")
    if playlists:
        for playlist in playlists:
                tidal_oldplaylists.append(playlist)


def _search_for_track_on_tidal(name, artist):
    id = -1
    artist = artist.lower()

    def _artist_in_response(track):
        for response_artist in track['artists']:
            if response_artist['name'].lower() == artist:
                return True
        return False

    matched_artist = False
    offset = 0
    limit = 300
    end_of_track_list = False
    while not matched_artist and not end_of_track_list:
        try:
            r = requests.request(
                'GET',
                get_tidal_find_track_url(),
                headers={
                    'x-tidal-sessionid': tidal_session.session_id
                },
                params={
                    'offset': offset,
                    'countryCode': 'US',
                    'limit': limit,
                    'query': name
                }
            )

            if len(r.json()['items']) == 0:
                end_of_track_list = True

            for track in r.json()['items']:
                if _artist_in_response(track):
                    id = track['id']
                    matched_artist = True
                    break
            offset = offset + 300
            limit = offset + 300
        except requests.exceptions.RequestException as e:
            print('Could not make request for track name=' + name + ", artist=" + artist)
            # TODO: should add track name to CSV of failures

    if not matched_artist:
        print('Could not find track name=' + name + ", artist=" + artist)
        # TODO: should add track name to CSV of failures

    return id;


def _create_tidal_playlist(playlist_name, tidal_id, tidal_session):
    try:
        r = requests.request(
            'POST',
            get_tidal_create_playlist_url(tidal_id),
            data={'title':playlist_name, 'description':''},
            headers={
                'x-tidal-sessionid': tidal_session.session_id
            },
            params={
                'sessionId': tidal_session.session_id,
                'countryCode': 'US',
                'limit': '999'
            }
        )
    except requests.exceptions.RequestException as e:
        print('Error creating playlist: ' + e)
        # TODO: should add playlist name to CSV of failures
        return None

    return r.json()['uuid']

def _add_tracks_to_spotify_playlist(track_ids, playlist_id):
    scope = 'playlist-modify-public'
    token = util.prompt_for_user_token(username, scope)

    if token:
        sp = spotipy.Spotify(auth=token)
        sp.trace = False
        results = sp.user_playlist_add_tracks(username, playlist_id, track_ids)
    else:
        print("Can't get token for " + username)

def copy_spotify_playlists_to_another_spotify_account():
    scope = 'playlist-read-private'
    print("LOGIN WITH SOURCE SPOTIFY ACCOUNT (TO COPY FROM) (" + spotify_username + ")")
    token = util.prompt_for_user_token(spotify_username, scope)

    if token:
        sp = spotipy.Spotify(auth=token)
        sp.trace = False
        offsets = [0,50,100,150,200,250,300] #TODO: How many playlists does the user have?
        playlists_owner_ids = []
        playlists_ids = []
        for offset in offsets:
                r = sp.user_playlists(spotify_id,50,offset)
                for item in r['items']:
                        playlists_owner_ids.append(item['owner']['id'])
                        playlists_ids.append(item['id'])
        scope_2 = 'playlist-modify-public'
        print("LOGIN WITH DESTINATION SPOTIFY ACCOUNT (TO COPY TO) (" + spotify_username_2 + ")")
        token_2 = util.prompt_for_user_token(spotify_username_2, scope_2)

        if token_2:
                sp_2 = spotipy.Spotify(auth=token_2)
                sp_2.trace = False
                i=len(playlists_ids)-1
                for playlist_id in playlists_ids:
                        #print("PLAYLIST NUMBER " + str(i) + ": playlist_id=" + playlists_ids[i] + ", playlist_owner_id=" + playlists_owner_ids[i])
                        sp_2.user_playlist_follow_playlist(playlists_owner_ids[i], playlists_ids[i])
                        i-=1
        else:
                print("Can't get token for " + spotify_username_2)
    else:
        print("Can't get token for " + spotify_username)

def copy_spotify_saved_tracks_to_another_spotify_account():
    scope = 'user-library-read'
    print("LOGIN WITH SOURCE SPOTIFY ACCOUNT (TO COPY FROM) (" + spotify_username + ")")
    token = util.prompt_for_user_token(spotify_username, scope)

    if token:
        sp = spotipy.Spotify(auth=token)
        sp.trace = False
        offsets = [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300] #TODO: How many tracks does the user have?
        tracks_ids = []
        for offset in offsets:
                r = sp.current_user_saved_tracks(20,offset)
                for item in r['items']:
                     tracks_ids.append(item['track']['id'])
        scope_2 = 'user-library-modify'
        print("LOGIN WITH DESTINATION SPOTIFY ACCOUNT (TO COPY TO) (" + spotify_username_2 + ")")
        token_2 = util.prompt_for_user_token(spotify_username_2, scope_2)
        if token_2:
               sp_2 = spotipy.Spotify(auth=token_2)
               sp_2.trace = False
               i=len(tracks_ids)-1
               for track_id in tracks_ids:
                   sp_2.current_user_saved_tracks_add([tracks_ids[i]])
                   i -= 1
                   # sleep needed to preserve tracks "chronological order". Apparently 0.5s is not enough
                   time.sleep(1)
        else:
            print("Can't get token for " + spotify_username_2)
    else:
        print("Can't get token for " + spotify_username)


start = time.time()
sp, sp_token = connect_to_spotify()  # NEEDED ONLY FOR MOVING FROM SPOTIFY TO TIDAL

tidal_session = connect_to_tidal(tidal_username,
                                 tidal_pwd)  # NEEDED ONLY FOR 1) MOVING FROM SPOTIFY TO TIDAL 2) MOVING FROM TIDAL1 TO TIDAL2
# tidal_session_2 = connect_to_tidal(tidal_username_2, tidal_pwd_2) #NEEDED ONLY FOR MOVING FROM TIDAL1 TO TIDAL2
# move_discover_weekly_from_spotify_to_tidal()

move_all_spotify_playlists_to_tidal()
# copy_tidal_playlists_to_another_tidal_account()
# MIGRATE SPOTIFY ACCOUNT = COPY PLAYLISTS + SAVED TRACKS
# copy_spotify_playlists_to_another_spotify_account()
# copy_spotify_saved_tracks_to_another_spotify_account()
end = time.time()
print("Time elapsed: " + str(end - start) + " s (" + str((end - start) / 60) + " min)")
