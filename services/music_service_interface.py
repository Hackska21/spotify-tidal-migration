import logging
import sys
from abc import ABC
from pprint import pprint
from typing import List

import Levenshtein


class TrackItemInterface(ABC):
    artists: List
    name: str
    album: str
    id: str


MAX_DISTANCE = 10

logging.basicConfig(filename='log_errors_match',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logger = logging.getLogger('best_track')


class MusicServiceSyncInterface(ABC):
    service_name: str
    _user_id: str

    def get_user_path_service(self):
        return f"user_data/{self.service_name}/{self._user_id}/"

    def get_all_playlist(self):
        raise NotImplemented

    def get_tracks_for_playlist(self, playlist_id):
        raise NotImplemented

    def add_track_to_playlist(self, track, playlist_id):
        raise NotImplemented

    def _distance_with_none(self, word_1, word_2):
        if word_1 is not None and word_2 is not None:
            dist = Levenshtein.distance(word_1, word_2)
            # print(dist, word_1, word_2)
            if dist == 0 and word_1 != word_2:
                return 10
            return dist
        else:
            return 0

    def _distance_of_two_tracks(self, track, x):
        if x.name == track.name and x.artists[0] == x.artists[0]:
            return 0

        return self._distance_with_none(x.album, track.album) * 1 + \
               self._distance_with_none(x.name, track.name) * 3 + \
               self._distance_with_none(x.artists[0], track.artists[0]) * 2

    def best_track_id(self, track: TrackItemInterface, options: List[TrackItemInterface]):
        try:
            if len(options) < 1:
                return None

            distances = [self._distance_of_two_tracks(track, x)
                         for x in options]
            min_distance = min(distances)
            best = distances.index(min(distances))
            # print(distances, track, options)
            if min_distance > MAX_DISTANCE:
                logger.error(
                    f'not found {track.name} {track.artists[0]} {track.album} posible: {options[best]} but: {min_distance}')
                return None
            return options[best]
        except Exception as e:
            logger.exception('whoops', exc_info=e)

    def get_favorites(self):
        raise NotImplemented

    def search_for_track_id(self, query=None, track_name=None, artist=None, album=None):
        raise NotImplemented

    def add_favorites(self, tracks_ids):
        raise NotImplemented
