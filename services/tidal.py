import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint
from typing import List

import requests
import tidalapi
from tidalapi import Track

from dataclass_utils import FromDictMixin
from services.music_service_interface import MusicServiceSyncInterface, TrackItemInterface
from persistance import dump_to_pickle
from secrets import tidal_id, tidal_username

logger = logging.getLogger('')
logger.setLevel(logging.INFO)
format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(format)
logger.addHandler(ch)


class CantLoginException(Exception):
    pass


@dataclass
class TidalPlaylistInterface(FromDictMixin):
    title: str
    type: str
    url: str
    lastUpdated: str
    uuid: str


@dataclass
class TidalTrack(FromDictMixin, TrackItemInterface):
    artists: List
    name: str
    album: str
    id: str = None


class TidalService(MusicServiceSyncInterface):
    _base_api_path = 'https://listen.tidal.com/v1/'
    _user_playlist = '{base}users/{user_id}/playlists'
    _session_file = 'tidal_session_{}'

    service_name = 'tidal'

    def __init__(self, tidal_id=tidal_id, tidal_username=tidal_username):
        self.tidal_id = tidal_id
        self._user_id = tidal_username
        self._session = None

    @property
    def session(self):
        """
            Only log if a request is triggered
        :return:
        """
        if self.session is None:
            self._session = self.login()
        return self._session

    def oauth_login_new_session(self, tidal_session):
        # create a new session
        tidal_session.login_oauth_simple(function=logger.info)
        if tidal_session.check_login():
            # store current OAuth session
            data = {}
            data['token_type'] = tidal_session.token_type
            data['session_id'] = tidal_session.session_id
            data['access_token'] = tidal_session.access_token
            data['refresh_token'] = tidal_session.refresh_token
            data['expiry_time'] = tidal_session.expiry_time.timestamp()
            with open(self._session_file.format(self.tidal_id), 'w') as outfile:
                json.dump(data, outfile)

    def login(self) -> tidalapi.Session:
        tidal_session = tidalapi.Session()

        try:
            # attempt to reload existing session from file
            with open(self._session_file.format(self.tidal_id)) as f:
                logger.info("Loading OAuth session from %s..." % self._session_file.format(self.tidal_id))
                data = json.load(f)
                tidal_session.load_oauth_session(
                    token_type=data['token_type'],
                    access_token=data['access_token'],
                    refresh_token=data['refresh_token'],
                    expiry_time=datetime.fromtimestamp(data['expiry_time'])
                )
        except:
            logger.info("Could not load OAuth session from %s" % self._session_file.format(self.tidal_id))
        if not tidal_session.check_login():
            logger.info("Creating new OAuth session...")
            self.oauth_login_new_session(tidal_session)

        if tidal_session.check_login():
            logger.info("TIDAL Login OK")
        else:
            logger.info("TIDAL Login KO")

        return tidal_session

    def get_all_playlist(self) -> List[TidalPlaylistInterface]:
        try:
            r = self.session.request.request(
                'GET',
                self._user_playlist.format(base=self._base_api_path, user_id=self.tidal_id),
                params={
                    'countryCode': 'US',
                    'limit': 999
                }
            )
        except requests.exceptions.RequestException as e:
            raise Exception("Could not get list of playlists")
        playlists = r.json()['items']
        playlists = [TidalPlaylistInterface.from_dict(item) for item in playlists]

        return playlists

    def get_tracks_for_playlist(self, playlist_id) -> List[tidalapi.media.Track]:
        playlist = tidalapi.Playlist(self.session, playlist_id)
        return playlist.tracks()

    def create_playlist(self, playlist_name, description=""):
        try:
            r = self.session.request(
                'POST',
                self._user_playlist.format(base=self._base_api_path, user_id=self.tidal_id),
                data={'title': playlist_name, 'description': description},
                params={
                    'sessionId': self.session.session_id,
                    'countryCode': 'US',
                    'limit': '999'
                }
            )
        except requests.exceptions.RequestException as e:
            print('Error creating playlist: ' + e)
            # TODO: should add playlist name to CSV of failures
            return None

    def _parse_tracks(self, tidal_track: Track):
        return TidalTrack(
            name=tidal_track.name,
            album=tidal_track.album.name,
            artists=[x.name for x in tidal_track.artists],
            id=tidal_track.id
        )

    def get_favorites(self):
        all_tracks = []
        tracks = self.session.user.favorites.tracks()
        all_tracks.extend(tracks)
        offset = 1
        while len(tracks) == 1000:
            tracks = self.session.user.favorites.tracks(offset=offset * 1000)
            offset += 1
            all_tracks.extend(tracks)
        return [self._parse_tracks(x) for x in all_tracks]

    def add_track_to_playlist(self):
        raise NotImplemented


if __name__ == '__main__':
    service = TidalService(tidal_username, tidal_id)
    # playlist = service.get_all_playlist()[0]
    # pprint(playlist)
    # pprint(service.get_tracks_for_playlist(playlist_id=playlist.uuid)[0].name)

    favs = service.get_favorites()
    # favs = load_from_pickle('tidal_favs')
    pprint(len(favs))
    dump_to_pickle('tidal_favs', favs)
