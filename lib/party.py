import json
from util import *
from datetime import datetime, timedelta
from stop import Stop
from camp import Camp
from river import River
from town import Town

class Party():
    """
    Defines the trail and simulates a party travelling it.
    """
    def __init__(self, party_file_name=None, trail=None):
        if party_file_name is not None:
            with open(party_file_name, 'r') as party_file:
                self.party_data = json.load(party_file)

            self.date = datetime.strptime(self.party_data['start date'], '%Y-%m-%d')

        else:
            raise ValueError('ERROR - party config file required to initialize party.')

        if trail is not None:
            self.trail = trail
            self.destination = trail.end_of_trail()
            # initialize the rivers now that we have a date
            for stop in self.trail.path:
                if isinstance(stop, River):
                    stop.initialize_river_state(self.date.year)

        else:
            raise ValueError('ERROR - trail object required to initialize party.')

        self.members = self.party_data['members']
        self.inventory = self.party_data['inventory']

        self.current_stop = trail.start_of_trail()
        self.last_major_stop = self.current_stop
        self.next_major_stop = trail.next_major_stop(self.last_major_stop.mile_marker)

        self.pace = 'normal'

        self.update_condition()


    def decide(self, strategy):
        """
        Make decisions according to the current strategy. Update the party according to the outcome of the decisions.

        Returns: action to take (travel (pace), cross river (method), trade (to buy, to sell), hunt, rest (length),
        repair, replace)
        -------

        """

        try:
            strategies = {'greatest need', self.decide_greatest_need}
        except KeyError:
            raise ValueError('ERROR - requested strategy is not implemented: ' + str(strategy))

        return strategies[strategy]


    def decide_greatest_need(self):
        available_actions = self.current_stop.actions

        # party needs are a balance between continue and survive
        # party high level needs are: continue and recover/resupply
        # continue actions: travel/ferry/ford/caulk
        # recover actions: rest/eat/drink/repair/trade/shop/hunt

        max_utility = None
        for action in available_actions:
            if action == 'travel':
                utility = self.utility_travel()
            elif action == 'ford':
                utility = self.utility_ford()
            else:
                # we haven't implemented this yet, so it's really bad
                utility = None

            if utility is not None:
                if max_utility is None:
                    max_utility = (action, utility)
                elif utility > max_utility[1]:
                    max_utility = (action, utility)

        return max_utility[0]


    def utility_travel(self):
        # conversion factors
        # the benefit of travelling 15 miles in a day is equal to the cost of having 3 days left of both food and health
        a = 1.0/15.0
        b = 3.0/2.0

        # nominal distance traveled in one day
        benefit = self.party_speed()
        # cost terms are both in number of days of remaining, so no need for yet another conversion factor
        # cost is geometric sum because 0 is very bad and large values are good
        cost = 1.0/float(self.remaining_food(action='travel', days=1)) + 1.0/float(self.remaining_health(action='travel', days=1))
        return a*benefit - b*cost


    def remaining_food(self, action, days):
        # the estiamted amount of food remaining in terms of days under the given action
        if action == 'travel':
            total_need = sum([member['needs']['food'] for member in self.members if member['condition']['health'] > 0])
            remaining_food = self.inventory['food'] - days * total_need
            remaining_days = remaining_food / float(total_need)
        else:
            raise ValueError('ERROR - action not implemented: ' + str(action))

        return max(remaining_days, 0.0)


    def feed(self):
        for i, member in enumerate(self.data['members']):
            ration = min(member['needs']['food'], self.data['inventory']['food'])
            self.data['inventory']['food'] -= ration

            if 0 < ration < member['needs']['food']:
                severity = -5
            elif ration == 0:
                severity = -10
            else:
                severity = 0

            self.data['members'][i]['condition'].setdefault('afflictions', dict())
            self.data['members'][i]['condition']['afflictions']['hunger'] = severity


    def remaining_health(self, action, days):
        member_health = []
        total_severity = []

        for i, member in enumerate(self.members):
            sev = 0
            for affliction, severity in member['condition'].get('afflictions', dict()).iteritems():
                sev += severity

            total_severity.append(sev)
            member_health.append(self.members[i]['condition']['health'] + sev)

        remaining_days = [h/float(s) for h, s in zip(member_health, total_severity)]

        return max(min(remaining_days), 0.0)


    def update_health(self):
            for i, member in enumerate(self.data['members']):
                for affliction, severity in member['condition'].get('afflictions', dict()).iteritems():
                    self.data['members'][i]['condition']['health'] += severity
                    if self.data['members'][i]['condition']['health'] <= 0:
                        print member['name'] + ' has died of ' + affliction


    def update(self, party, action):
        if action['type'] == 'travel':
            self.travel(party, action['parameters'])
        else:
            raise ValueError('ERROR - Action not recognized: ' + str(action))

        return party.state()


    def set_destination(self, mile_marker):
        self.destination = mile_marker


    def number_alive(self):
        return sum([1 if member['condition']['health'] > 0 else 0 for member in self.members])


    def party_speed(self):
        # the party can only travel as fast as its slowest member

        min_speed = min([member['abilities']['speed'] for member in self.members if member['condition']['health'] > 0])

        if self.pace == 'normal':
            pace_modifier = 1.0
        elif self.pace == 'easy':
            pace_modifier = 0.75
        elif self.pace == 'hard':
            pace_modifier = 1.25
        else:
            raise ValueError('ERROR - Unknown pace: ' + str(self.pace))

        travel_speeds = self.current_stop.properties.get('travel speed modifier')
        if travel_speeds is not None:
            terrain_modifier = travel_speeds[season(self.date)]
        else:
            terrain_modifier = 1.0

        return pace_modifier * terrain_modifier * min_speed


    def arrived(self):
        return True if self.current_stop.mile_marker >= self.destination.mile_marker else False


    def update_condition(self):

        if self.number_alive() == 0:
            self.condition = 'dead'
        elif self.arrived():
            # it's implicit here that number_alive > 0
            self.condition = 'arrived'
        else:
            self.condition = 'on the trail'


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
        section = self.get_terrain(party.current_stop.mile_marker)
        miles_per_day = party.get_min_speed() * section['travel speed modifier'][season]

        stop = None

        if party.current_stop.mile_marker + miles_per_day >= party.next_major_stop.mile_marker:
            # arrived at next major stop
            print 'Arrived at ' + party.next_major_stop['name']
            party.current_stop.mile_marker = party.next_major_stop.mile_marker
            party.last_major_stop = party.next_major_stop
            party.next_major_stop = self.next_major_stop(party.current_stop.mile_marker)

            stop = party.last_major_stop

        else:
            party.current_stop.mile_marker += miles_per_day

            stop = Camp(party.current_stop.mile_marker).stop

        party.current_stop = stop
        party.feed()
        party.update_health()
        self.date += timedelta(days=1)

        return
