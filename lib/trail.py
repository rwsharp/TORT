import json
from datetime import datetime

from lib.camp  import Camp
from lib.river import River
from lib.town  import Town

class Trail():
    """
    Defines the trail and simulates a party travelling it.
    """
    def __init__(self, trail_file_name=None, terrain_file_name=None):
        if trail_file_name is not None:
            with open(trail_file_name, 'r') as trail_file:
                self.trail_data = json.load(trail_file)
        else:
            raise ValueError('ERROR - trail file required.')

        if terrain_file_name is not None:
            with open(terrain_file_name, 'r') as terrain_file:
                self.terrain_data = json.load(terrain_file)
        else:
            raise ValueError('ERROR - terrain file required')

        self.initialize_path()


    def initialize_path(self):
        self.path = dict()
        mile_marker = 0

        for i, trail_stop in enumerate(self.trail_data):
            # find the next mile marker
            if trail_stop.get('mile marker') is None:
                if trail_stop.get('miles beyond last marker') is None:
                    raise KeyError('ERROR - This stop on the trail has no location data: ' + str(trail_stop))
                else:
                    next_mile_marker = mile_marker + trail_stop.get('miles beyond last marker')
            else:
                next_mile_marker = trail_stop.get('mile marker')

            # make sure major stops are listed sequentially
            if i > 0:
                if next_mile_marker <= mile_marker:
                    raise ValueError('ERROR - List of trail stops is out of order: ' + str(i) + ' ' + str(trail_stop))

            # construct the path between trail_stops
            for mm in range(mile_marker + 1, next_mile_marker):
                # camp stops between trail stops
                self.path[mm] = Camp(mile_marker=mm, properties=self.get_terrain(mm))

            # trail stop at next_mile_marker
            add_actions = trail_stop.get('add actions')
            rem_actions = trail_stop.get('remove actions')
            properties  = trail_stop.get('properties')

            if trail_stop['kind'] == 'town':
                self.path[next_mile_marker] = Town(name=trail_stop.get('name', 'town'), mile_marker=next_mile_marker, add_actions=add_actions, rem_actions=rem_actions, properties=properties)
            elif trail_stop['kind'] == 'river':
                self.path[next_mile_marker] = River(name=trail_stop.get('name', 'river'), mile_marker=next_mile_marker, add_actions=add_actions, rem_actions=rem_actions, properties=properties)
            else:
                ValueError('ERROR - Trail stop kind ' + str(trail_stop['kind']) + ' not implemented.')

            mile_marker = next_mile_marker


    def get_terrain(self, mile_marker):
        section_found = False
        for section in self.terrain_data:
            if section['trail section'][0] <= mile_marker <= section['trail section'][1]:
                section_found = True
                break

        if section_found:
            return section
        else:
            raise ValueError('ERROR - no trail section found at mile marker ' + str(mile_marker))


    def next_major_stop(self, current_mile_marker):
        found_next_major_stop = False
        while(not found_next_major_stop):
            if isinstance(self.path[current_mile_marker], (River, Town)):
                found_next_major_stop = True
            else:
                current_mile_marker += 1

        return self.path[current_mile_marker]


    def last_major_stop(self, current_mile_marker):
        found_last_major_stop = False
        while (not found_last_major_stop):
            if isinstance(self.path[current_mile_marker], (River, Town)):
                found_last_major_stop = True
            else:
                current_mile_marker -= 1

        return self.path[current_mile_marker]


    """
    def set_mile_markers(self):
        mile_marker = 0

        for i, stop in enumerate(self.stops):
            if stop.get('mile marker') is None:
                if stop.get('miles beyond last marker') is None:
                     raise KeyError('ERROR - This stop on the trail has no location data: ' + str(stop))
                else:
                    mile_marker += stop.get('miles beyond last marker')
                    self.stops[i]['mile marker'] = mile_marker
            else:
                mile_marker = stop.get('mile marker')

            if i > 0:
                if stop['mile marker'] <= self.stops[i-1]['mile marker']:
                    raise ValueError('ERROR - List of trail stops is out of order.')
    """


    def start_of_trail(self):
        return self.path[min(self.path.keys())]


    def end_of_trail(self):
        return self.path[max(self.path.keys())]



