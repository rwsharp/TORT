import json
from datetime import datetime, timedelta

from lib.camp import Camp

class Trail():
    """
    Defines the trail and simulates a party travelling it.
    """
    def __init__(self, trail_file_name=None, terrain_file_name=None):
        if trail_file_name is not None:
            with open(trail_file_name, 'r') as trail_file:
                self.stops = json.load(trail_file)
                self.set_mile_markers()
        else:
            self.stops = None

        if terrain_file_name is not None:
            with open(terrain_file_name, 'r') as terrain_file:
                self.terrain = json.load(terrain_file)
        else:
            self.terrain = None

        self.date = datetime.strptime('1846-03-01', '%Y-%m-%d')


    def set_date(self, date):
        self.date = date


    def get_terrain(self, mile_marker):
        section_found = False
        for section in self.terrain:
            if section['trail section'][0] <= mile_marker <= section['trail section'][1]:
                section_found = True
                break

        if section_found:
            return section
        else:
            raise ValueError('ERROR - no trail section found at mile marker ' + str(mile_marker))


    def next_stop(self, current_mile_marker):
        next_stop = None
        for i, stop in enumerate(self.stops):
            if stop['mile marker'] > current_mile_marker:
                next_stop = stop
                break

        return next_stop


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


    def start_of_trail(self):
        return self.stops[0]

    def end_of_trail(self):
        return self.stops[-1]


    def update(self, party, action):
        if action['type'] == 'travel':
            print self.travel(party, action['parameters'])
        else:
            raise ValueError('ERROR - Action not recognized: ' + str(action))

        return party.state()


    def get_season(self):
        # Crude, but close enough
        vernal_equinox = datetime(self.date.year, 3, 21)
        summer_solstice = datetime(self.date.year, 6, 21)
        autumnal_equinox = datetime(self.date.year, 9, 21)
        winter_solstice = datetime(self.date.year, 12, 21)

        if self.date < vernal_equinox:
            season = 'winter'
        elif vernal_equinox <= self.date < summer_solstice:
            season = 'spring'
        elif summer_solstice <= self.date < autumnal_equinox:
            season = 'summer'
        elif autumnal_equinox <= self.date < winter_solstice:
            season = 'fall'
        elif winter_solstice <= self.date:
            season = 'winter'
        else:
            raise ValueError('ERROR - Something is wrong with self.date; you should never get here.' )

        return season


    def travel(self, party, parameters):
        """
        Simulate one day's travel along the trail. Update's the condition of the party.

        Parameters
        ----------
        party: the party traveling the trail

        Returns
        -------
        """

        season = self.get_season()
        section = self.get_terrain(party.data['mile marker'])
        miles_per_day = party.get_min_speed() * section['travel speed modifier'][season]

        stop = None

        if party.data['mile marker'] + miles_per_day >= party.next_stop['mile marker']:
            # arrived at next stop
            print 'Arrived at ' + party.next_stop['name']
            party.data['mile marker'] = party.next_stop['mile marker']
            party.last_stop = party.next_stop
            party.next_stop = self.next_stop(party.data['mile marker'])

            stop = party.last_stop

        else:
            party.data['mile marker'] += miles_per_day

            stop = Camp(party.data['mile marker']).stop

        party.feed()
        party.update_health()
        self.date += timedelta(days=1)

        return stop
