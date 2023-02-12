import inspect
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pprint import pprint
from typing import List, Dict

from dataclass_utils import FromDictMixin
from services.music_service_interface import MusicServiceSyncInterface, TrackItemInterface
from persistance import dump_to_file, dump_to_pickle, load_from_pickle, create_folder
from secrets import spotify_id, \
    spotify_username, SPOTIPY_CLIENT_ID, \
    SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
import spotipy


class SpotifySearchTypes(Enum):
    ALBUM = 'album'
    TRACK = 'track'


@dataclass
class SpotifyTrack(FromDictMixin, TrackItemInterface):
    artists: List
    name: str
    album: str
    id: str = None


@dataclass
class SpotifyQueryBuilder:
    search_term: str = None
    track_name: str = None
    album: str = None
    artist: str = None

    def get_custom_attr(self, attr):
        value = self.__getattribute__(attr)
        if value == None:
            return ''
        if attr == 'search_term':
            return value
        else:
            return f'{attr}:{value}'

    @classmethod
    def get_params(cls):
        return inspect.signature(cls).parameters

    def get_query(self):
        return "".join([self.get_custom_attr(x) for x in self.get_params()]),


class SpotifyService(MusicServiceSyncInterface):
    secret = SPOTIPY_CLIENT_SECRET
    client = SPOTIPY_CLIENT_ID
    redirect = SPOTIPY_REDIRECT_URI
    service_name = 'spotify'

    def __init__(self, username=spotify_username, user_id=spotify_id):
        self._playlist = None
        self._user_id = user_id
        self._username = username
        self.sp, self.sp_token = self._login()

    def dump_playlist_to_file(self, playlist_obj):
        filename = f"{playlist_obj['name']}-{playlist_obj['id']}"
        folder = f"spotify/playlist/{self.client}/"
        create_folder(folder)
        tracks = self.get_tracks_for_playlist(playlist_obj['id'])
        dump_to_file(folder + filename, tracks)

    def _login(self):
        scope = 'user-library-read,user-library-modify'
        token = spotipy.util.prompt_for_user_token(
            self._username,
            scope,
            client_id=self.client,
            client_secret=self.secret,
            redirect_uri=self.redirect
        )
        # spotipy.SpotifyOAuth()

        if token:
            sp = spotipy.Spotify(auth=token)
        else:
            print("Can't get spotify token for " + self._username)
            sys.exit()
        return sp, token

    def _get_all_of_request_sp(self, calleable, key_resonse=None, key_item='', *args):
        " deprecreated?"
        items = []
        response = calleable()
        if key_resonse:
            response = response[key_resonse]
        items.extend(response[key_item])
        while response['next']:
            response = None

    def get_all_playlist(self):
        if self._playlist is not None:
            return self._playlist
        playlists: Dict = self.sp.user_playlists(self.spotify_id)
        self._playlist = []
        while playlists:
            self._playlist.extend(playlists['items'])
            if playlists['next']:
                playlists = self.sp.next(playlists)
            else:
                playlists = None

        return self._playlist

    def get_tracks_for_playlist(self, playlist_id):
        all_tracks = []
        tracks = self.sp.playlist(playlist_id)['tracks']
        all_tracks.extend(tracks['items'])
        while tracks['next']:
            tracks = self.sp.next(tracks)
            all_tracks.extend(tracks['items'])
        return [self._parse_track(x['track']) for x in all_tracks]

    def _parse_track(self, track_item):
        return SpotifyTrack(
            name=track_item['name'],
            artists=[x['name'] for x in track_item['artists']],
            album=track_item['album']['name'],
            id=track_item['id']
        )

    def search_for_track_id(self, query=None, track_name=None, artist=None, album=None):
        q = SpotifyQueryBuilder(search_term=query, track_name=track_name, artist=artist, album=album).get_query()
        seudo_track = SpotifyTrack(artists=[artist], name=query, album=album)
        response = self.sp.search(q)
        tracks = [self._parse_track(x) for x in response['tracks']['items']]
        best = self.best_track_id(seudo_track, tracks)
        if best is not None:
            return best
        else:
            q = SpotifyQueryBuilder(search_term=query + " " + artist + " " + album).get_query()
            response = self.sp.search(q)
            tracks = [self._parse_track(x) for x in response['tracks']['items']]
            return self.best_track_id(seudo_track, tracks)

    def add_track_to_playlist(self, tracks_ids: List, playlist_id):
        self.sp.playlist_add_items(playlist_id=playlist_id, items=tracks_ids)

    def add_favorites(self, tracks_ids):
        self.sp.current_user_saved_tracks_add(tracks=tracks_ids)

    def _has_new_favorites(self, fav_response, added_after: datetime):
        if added_after is None:
            return True
        most_recent = datetime.fromisoformat(fav_response[0]['added_at'].replace('Z', ''))
        return most_recent > added_after

    def get_favorites(self, added_after: datetime = None):
        favs = []
        response = self.sp.current_user_saved_tracks()
        favs.extend(response['items'])
        if not self._has_new_favorites(favs, added_after):
            return None
        while response['next'] and self._has_new_favorites(response['items'], added_after):
            response = self.sp.next(response)
            favs.extend(response['items'])
            # response['next'] = None
        # pprint(most_recent)
        return [self._parse_track(x['track']) for x in favs]


if __name__ == '__main__':
    instance = SpotifyService()
    # playlist = instance.get_all_playlist()
    # pprint(playlist)
    # for i in playlist:
    #    instance.dump_playlist_to_file(i)
    ##tracks = instance.get_tracks_for_playlist(playlist[0]['id'])
    ##pprint(tracks)
    # response = instance.search_for_track_id('The way i',  artist='ingrid',)
    # pprint(response)
    # tracks = instance.get_favorites()
    # tracks = instance.get_favorites()
    tracks = load_from_pickle('original_favorites')
    pprint(len(tracks))
    dump_to_pickle('original_favorites', tracks)
