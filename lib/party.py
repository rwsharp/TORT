import json
from util import *
from datetime import datetime, timedelta

from member import Member
from stop import Stop
from camp import Camp
from river import River
from town import Town

from numpy import ceil, sign
from numpy.random import uniform, normal, randint, choice


class Party():
    """
    Defines the trail and simulates a party travelling it.
    """
    def __init__(self, party_file_name=None, trail=None):
        if party_file_name is not None:
            with open(party_file_name, 'r') as party_file:
                party_data = json.load(party_file)

            self.start_datetime = datetime.strptime(party_data['start time'], '%Y-%m-%d %H:%M')

        else:
            raise ValueError('ERROR - party config file required to initialize party.')

        if trail is not None:
            self.trail = trail
            self.destination = trail.end_of_trail()
            # initialize the rivers now that we have a date
            for stop in self.trail.path:
                if isinstance(stop, River):
                    stop.initialize_river_state(self.start_datetime.year)

        else:
            raise ValueError('ERROR - trail object required to initialize party.')

        self.members = dict()
        for id, member_def in enumerate(party_data['members']):
            self.members[id] = Member(member_def)

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
            strategies = {'greatest need': self.decide_greatest_need}
        except KeyError:
            raise ValueError('ERROR - requested strategy is not implemented: ' + str(strategy))

        return strategies[strategy]()


    def decide_greatest_need(self):
        available_actions = self.current_stop.actions

        # party needs are a balance between continue and survive
        # party high level needs are: continue and recover/resupply
        # continue actions: travel/ferry/ford/caulk
        # recover actions: rest/eat/drink/repair/trade/shop/hunt

        max_action, max_utility = None, None
        for action in available_actions:
            if action == 'travel':
                utility = self.utility_travel()
            elif action == 'ford':
                utility = self.utility_ford()
            elif action == 'caulk':
                utility = self.utility_caulk()
            else:
                # we haven't implemented this yet
                utility = None

            if utility is not None:
                if max_utility is None:
                    max_action, max_utility = action, utility
                elif utility > max_utility:
                    max_action, max_utility = action, utility

        if max_action is None:
            raise ValueError('ERROR - No action has a defined utility, connot continue.')

        return max_action


    def utility_travel(self):
        # conversion factors
        # the benefit of travelling 15 miles in a day is equal to the cost of having 3 days left of both food and health
        a = 1.0/15.0
        b = 3.1/2.0

        # nominal distance traveled in one day
        benefit = self.party_speed()
        # cost terms are both in number of days of remaining, so no need for yet another conversion factor
        # cost is geometric sum because 0 is very bad and large values are good
        parameters = {'days': 1}
        cost = 1.0/float(0.1 + self.remaining_food(action='travel', parameters=parameters)) + 1.0/float(0.1 + self.remaining_health(action='travel', parameters=parameters))
        return a*benefit - b*cost


    def utility_ford(self):
        # conversion factors
        # the benefit of crossing the river in a day is equal to the cost of having 3 days left of both food and health
        a = 1.0
        b = 3.1/2.0

        # fording a river runs the risk of a) failure - being forced to go back or b) loss of provisions

        # expected distance traveled in one day
        benefit = 1.0 * self.current_stop.ford_failure_rate(self.datetime)
        # cost terms are both in number of days of remaining, so no need for yet another conversion factor
        # cost is geometric sum because 0 is very bad and large values are good
        expected_food_loss = self.current_stop.ford_food_loss_fraction(self.datetime) * self.inventory['food']
        parameters = {'lost food': expected_food_loss}
        cost = 1.0/float(0.1 + self.remaining_food(action='ford', parameters=parameters)) + 1.0/float(0.1 + self.remaining_health(action='ford', parameters=parameters))
        return a*benefit - b*cost


    def utility_caulk(self):
        # conversion factors
        # the benefit of crossing the river in a day is equal to the cost of having 3 days left of both food and health
        a = 1.0
        b = 3.1/2.0

        # caulking and floating across a river runs the risk of a) failure - being forced to go back or b) loss of provisions

        # expected distance traveled in one day
        benefit = 1.0 * self.current_stop.caulk_failure_rate(self.datetime)
        # cost terms are both in number of days of remaining, so no need for yet another conversion factor
        # cost is geometric sum because 0 is very bad and large values are good
        expected_food_loss = self.current_stop.caulk_food_loss_fraction(self.datetime) * self.inventory['food']
        parameters = {'lost food': expected_food_loss}
        cost = 1.0/float(0.1 + self.remaining_food(action='ford', parameters=parameters)) + 1.0/float(0.1 + self.remaining_health(action='ford', parameters=parameters))
        return a*benefit - b*cost


    def inventory(self, item):
        amount = 0
        for member in self.members.values():
            if member.health > 0:
                amount += member.inventory.get(item, 0)

        return amount


    def remaining_food(self, action, parameters):
        # the estiamted amount of food remaining in terms of days remaining after the given action is carried out
        if action == 'travel':
            total_need = sum([member.food_need for member in self.members.values() if member.health > 0])
            remaining_food = self.inventory('food') - parameters['days'] * total_need
            remaining_days = remaining_food / float(total_need)
        elif action == 'ford':
            days = 1
            total_need = sum([member.food_need for member in self.members.values() if member.health > 0])
            remaining_food = self.inventory('food') - days * total_need - parameters.get('lost food', 0)
            remaining_days = remaining_food / float(total_need)
        else:
            raise ValueError('ERROR - action not implemented: ' + str(action))

        return max(remaining_days, 0.0)


    def feed(self):
        for id in self.living_members():
            ration = min(self.members[id].food_need, self.inventory('food'))
            self.update_food(-ration)

            if 0 < ration < self.members[id].food_need:
                severity = -5
            elif ration == 0:
                severity = -10
            else:
                severity = 0

            self.members[id].afflictions['hunger'].severity = severity


    def remaining_health(self, action, parameters):
        # todo: update this to hourly form daily
        member_health = []
        total_severity = []

        for i, member in self.members.iteritems():
            # only count values for living members
            if member.health > 0:
                sev = 0
                for name, affliction in member.afflictions.iteritems():
                    sev += affliction.severity
    
                total_severity.append(sev)
    
                if action == 'travel':
                    member_health.append(self.members[i].health + (parameters['days'] * sev))
                elif action == 'ford':
                    days = 1
                    member_health.append(self.members[i].health + (days * sev))
                else:
                    raise ValueError('ERROR - action not implemented: ' + str(action))
            
        remaining_days = [(100 if s == 0 else h/float(s)) for h, s in zip(member_health, total_severity)]

        return max(min(remaining_days), 0.0)


    def update(self, action, date_and_time):
        if action == 'travel':
            action_time = self.travel(date_and_time)
        elif action == 'ford':
            action_time = self.ford(date_and_time)
        elif action == 'caulk':
            action_time = self.caulk(date_and_time)
        else:
            raise ValueError('ERROR - Action not recognized: ' + str(action))

        self.update_condition()

        return action_time


    def set_destination(self, mile_marker):
        self.destination = mile_marker


    def number_alive(self):
        return sum([1 if member.health > 0 else 0 for member in self.members.values()])


    def party_speed(self):
        # the party can only travel as fast as its slowest member

        min_speed = min([member.weighted_speed() for member in self.members.values() if member.health > 0])

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
            terrain_modifier = travel_speeds[date_to_season(self.datetime)]
        else:
            terrain_modifier = 1.0

        return int(ceil(pace_modifier * terrain_modifier * min_speed))


    def party_travel_time(self):
        # travel_time is the time needed to cover the next mile of terrain
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

        # rule of thumb: add a mile for every 1000 feet elevation gain per mile
        elevation_gain = self.current_stop.properties.get('elevation gain per mile')
        added_distance = -0.2 if elevation_gain < -100 else (elevation_gain / 1000.0)

        terrain_modifier = self.current_stop.properties.get('surface speed modifier', 1.0)

        speed = pace_modifier * terrain_modifier * min_speed
        assert speed > 0, 'speed must be positive'
        travel_time = (1.0 + added_distance)/speed

        return travel_time


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


    def travel(self, date_and_time):
        """
        Simulate one mile's travel along the trail. Update the condition of the party.

        Returns
        -------
        """

        # simulate each mile of travel until we either hit a major stop or encounter a calamity
        travel_time = self.party_travel_time()

        progress = True
        travel_delay = 0

        for danger in self.current_stop.properties['dangers']:
            if uniform() < danger['probability']:
                # mon dieu! Disaster strikes!
                print 'Sacre bleu, disaster has struck!'
                print 'Bad news, it\'s ' + danger['name']
                victim = choice(self.living_members())
                print 'Poor ' + self.members[victim].name
                mu, sig = danger['severity']
                severity = int(round(sample_gamma(mu, sig)))
                travel_delay = danger['travel delay']
                if danger['affliction']:
                    # it's an affliction - give it to the victim and continue travel
                    if danger['affliction'] not in self.members[victim]['condition']['afflictions']:
                        self.members[victim].afflicitons[danger['name']] = severity
                    else:
                        print 'Lucky you, you can\'t get ' + danger['name'] + ' twice.'
                else:
                    # it's a one-time event, let the victim have it and delay the party
                    self.members[victim].health -= severity
                    progress = False
                    print 'Ouch!', self.members[victim].health
                    break

        if progress:
            mile_marker = self.current_stop.mile_marker
            self.current_stop = self.trail.path[mile_marker + 1]

            if isinstance(self.current_stop, (River, Town)):
                # arrived at next major stop
                print 'Arrived at ' + self.current_stop.name
                if isinstance(self.current_stop, River):
                    print 'River conditions (width, depth) = ' + str(self.current_stop.river_state(self.date))
                self.last_major_stop = self.current_stop
                self.next_major_stop = self.trail.next_major_stop(self.current_stop.mile_marker)

        elapsed_time = travel_time + travel_delay

        self.update_party(elapsed_time)

        return elapsed_time


    def update_party(self, elapsed_time):
        for member in self.members.values():
            member.update_health(elapsed_time)
            member.update_weariness(elapsed_time)

        self.update_condition()


    def living_members(self):
        return [id for member in self.members.iteritems() if member.health > 0]


    def random_member(self, status='any'):

        randint(0, len(self.members))

    def ford(self, date_and_time):
        """
        Simulate fording a river. It takes one day. Update the condition of the party.

        Returns
        -------
        """

        # fording can fail in which case the party does not advance and loses 1 day of food
        # fording can cause food to get wet and be considered lost
        # fording can succeed, in which case advacne one mile and take 1 day

        # decide if fording will succeed or fail
        ford_failure = True if uniform() < self.current_stop.ford_failure_rate(date_and_time) else False
        # decide how much food is lost by fording
        lost_food = self.inventory('food') * (1.0 if uniform() < self.current_stop.ford_food_loss_fraction(date_and_time) else 0.0)

        # made it across, so advance the party        
        if not ford_failure:            
            mile_marker = self.current_stop.mile_marker
            self.current_stop = self.trail.path[mile_marker + 1]           
            
            if isinstance(self.current_stop, (River, Town)):
                # arrived at next major stop
                print 'Arrived at ' + self.current_stop['name']
                self.last_major_stop = self.current_stop
                self.next_major_stop = self.trail.next_major_stop(self.current_stop.mile_marker)
        else:
            print 'You failed to ford the river!'
            
        if lost_food > 0:
            print 'Your provisions got wet and you lost '  + str(lost_food) + ' food!'

        self.update_food(-lost_food)
        self.feed()
        self.update_health()

        raise NotImplementedError('NEED TO RETURN ACTION TIME')

        return


    def update_food(self, amount):
        ids = self.living_members()
        # take it out a pound at a time round-robin style (stop at zero)
        delta = 0
        continue_update = True
        while continue_update:
            for id in ids:
                if sign(amount) > 0:
                    self.members[id].inventory['food'] += 1
                    delta += 1
                elif sign(amount) < 0:
                    if self.members[id].inventory['food'] > 0:
                        self.members[id].inventory['food'] += -1
                        delta += 1
                else:
                    # amount == 0
                    continue_update = False

                if delta == abs(amount):
                    continue_update = False
                    break


    def caulk(self):
        """
        Simulate caulking to cross a river. It takes one day. Update the condition of the party.

        Returns
        -------
        """

        # caulking can fail in which case the party does not advance and loses 1 day of food
        # caulking can cause food to get wet and be considered lost
        # caulking can succeed, in which case advacne one mile and take 1 day

        # decide if caulking will succeed or fail
        caulk_failure = True if uniform() < self.current_stop.caulk_failure_rate(self.date) else False
        # decide how much food is lost by fording
        lost_food = self.inventory['food'] * (1.0 if uniform() < self.current_stop.caulk_food_loss_fraction(self.date) else 0.0)

        # made it across, so advance the party        
        if not caulk_failure:            
            mile_marker = self.current_stop.mile_marker
            self.current_stop = self.trail.path[mile_marker + 1]           
            
            if isinstance(self.current_stop, (River, Town)):
                # arrived at next major stop
                print 'Arrived at ' + self.current_stop['name']
                self.last_major_stop = self.current_stop
                self.next_major_stop = self.trail.next_major_stop(self.current_stop.mile_marker)
        else:
            print 'You failed to cross the river by caulking!'
            
        if lost_food > 0:
            print 'Your provisions got wet and you lost '  + str(lost_food) + ' food!'

        self.inventory['food'] = max(self.inventory['food'] - lost_food, 0.0)
        self.feed()
        self.update_health()
        self.date += timedelta(days=1)

        raise NotImplementedError('NEED TO RETURN ACTION TIME')

        return
