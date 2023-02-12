from time import sleep
from typing import List

from equivalence_manager import EquivalenceManager
from services.music_service_interface import MusicServiceSyncInterface, TrackItemInterface
from persistance import load_from_pickle, dump_to_pickle
from services.spotify import SpotifyService
from services.tidal import TidalService


class ImporterClass:
    _favourites_file_name = "favorites"

    def __init__(self, from_service: MusicServiceSyncInterface, to_service: MusicServiceSyncInterface):
        self.from_service = from_service
        self.to_service = to_service
        self.origin_favorites = []
        self.target_favorites = []
        self.equivalence_manager = self._load_manager()

    def _load_favorites_from_service_file(self, service: MusicServiceSyncInterface):
        favs = load_from_pickle(self._favourites_file_name, service.get_user_path_service())
        return favs

    def _dump_favorites(self, service: MusicServiceSyncInterface, favorites):
        dump_to_pickle(self._favourites_file_name, favorites, path=service.get_user_path_service())

    def _load_favorites_for_service(self, service: MusicServiceSyncInterface, using_cache):
        favorites = None
        if using_cache:
            favorites = self._load_favorites_from_service_file(service)
        if not favorites:
            favorites = service.get_favorites()
        if using_cache:
            self._dump_favorites(service, favorites)
        return favorites

    def load_favorites(self, using_cache=True):
        self.origin_favorites = self._load_favorites_for_service(self.from_service, using_cache)
        self.target_favorites = self._load_favorites_for_service(self.to_service, using_cache)

    def _dump_manager(self):
        dump_to_pickle("manager", self.equivalence_manager)

    def _load_manager(self):
        manager = load_from_pickle("manager")
        if manager is None:
            manager = EquivalenceManager()
        return manager

    def temp(self):
        """
                for origin_key, target_key in equivalent_dict.items():
            origin = origin_favorites_by_id.get(origin_key,None)
            target = target_favorites_by_id.get(target_key, None)

            if origin and target:
                self.equivalence_manager.add_track_equivalence(
                    origin, target
                )
            else:
                print("No ta:", origin, target)
        :return:
        """

    def compare_favorites(self):
        """
            check if has the same elements
        :return:
        """
        origin_favorites_by_id = {x.id: x for x in self.origin_favorites}
        target_favorites_by_id = {x.id: x for x in self.target_favorites}

        for track_origin in self.origin_favorites:
            target_track = self.equivalence_manager.get_track_from_origin(track_origin)
            if not target_track:
                # print("not have eq", track_origin)
                pass
            else:
                if not target_track.name == track_origin.name and target_track.artists[0] == track_origin.artists[0]:
                    print("posible missMatch ?", track_origin, target_track)
                else:
                    if target_track.id not in target_favorites_by_id:
                        print("this song is not in target favorites", target_track)

        dummy = 0

        pass

    def import_favorites(self):
        self.load_favorites()
        self.compare_favorites()

        return
        # from_favs = self.from_service.get_favorites()
        # dump_to_pickle('tidal_favs', from_favs)
        from_favs = load_from_pickle('tidal_favs')
        # track = from_favs[0]
        # print(from_favs[0:1])
        # target_equivalents, errors, equivalent_dict = self._get_equivalents(from_favs[105:])
        # pprint(target_equivalents)
        print("finishhhhh")
        # dump_to_pickle('tidal_favs_equivalent2', target_equivalents)
        # dump_to_pickle('errors', errors)
        # dump_to_pickle('equivalent_dict', equivalent_dict)
        target_equivalents = load_from_pickle('tidal_favs_equivalent2')
        equivalent_dict = load_from_pickle('equivalent_dict')
        errors = load_from_pickle('errors')
        # pprint(errors)
        ##pprint(target_equivalents)
        step = 50
        i = 50
        # sleep(60*10)
        ids = list(equivalent_dict.values())
        while i < len(target_equivalents):
            print(i)
            self.to_service.add_favorites(ids[i:step + i])
            i += step
            sleep(30)

    def _get_equivalents(self, items: List[TrackItemInterface]):
        founded = []
        error = []
        orgin_target_dict = {}
        for track in items:
            target_track = self.equivalence_manager.get_track_from_origin(track)
            if target_track is None:
                target_track = self.to_service.search_for_track_id(query=track.name, artist=track.artists[0],
                                                                   album=track.album)
                self.equivalence_manager.add_track_equivalence(track, target_track)

            if target_track is not None:
                founded.append(target_track)
                orgin_target_dict[track.id] = target_track.id
            else:
                error.append(track)
        return founded, error, orgin_target_dict


if __name__ == '__main__':
    spotify = SpotifyService()
    tidal = TidalService()
    # tidal = None
    instance = ImporterClass(tidal, spotify)
    instance.import_favorites()
