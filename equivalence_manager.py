from typing import TypedDict, Dict

from services.music_service_interface import TrackItemInterface


class EquivalenceValuesDict(TypedDict):
    target_key: str
    track: TrackItemInterface


class EquivalenceManager:
    service_1_tracks_dict: Dict[str, EquivalenceValuesDict] = {}
    service_2_tracks_dict: Dict[str, EquivalenceValuesDict] = {}

    # def __init__(self, service_name):

    def _add_to_origin(self, origin, target):
        self.service_1_tracks_dict[origin.id] = EquivalenceValuesDict(target_key=target.id,
                                                                      track=target)

    def _add_to_target(self, origin, target):
        self.service_2_tracks_dict[target.id] = EquivalenceValuesDict(target_key=origin.id,
                                                                      track=origin)

    def add_conflictive(self, origin, target, old_origin, old_target):
        print("missmatch: ", origin, target, old_origin, old_target)

    def add_track_equivalence(self, origin: TrackItemInterface, target: TrackItemInterface):
        # Already Have one?
        old_target = self.get_track_from_origin(origin)
        old_origin = self.get_track_from_target(target)

        if old_origin and old_target:
            if old_origin.id == origin.id and old_target.id == target.id:
                return
            return self.add_conflictive(origin, target, old_origin, old_target)
        elif old_origin or old_target:
            if old_origin and origin.id == old_origin.id:
                self._add_to_origin(origin, target)
                return

            elif old_target and target.id == old_target.id:
                self._add_to_target(origin, target)
                return

            else:
                return self.add_conflictive(origin, target, old_origin, old_target)

        # Add to equivalence
        self._add_to_origin(origin, target)
        self._add_to_target(origin, target)

    def get_track_from_origin(self, origin_track: TrackItemInterface) -> TrackItemInterface:
        item = self.service_2_tracks_dict.get(origin_track.id, None)
        return item['track'] if item else None

    def get_track_from_target(self, origin_track: TrackItemInterface) -> TrackItemInterface:
        item = self.service_1_tracks_dict.get(origin_track.id, None)
        return item['track'] if item else None
