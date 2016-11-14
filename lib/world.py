import datetime
import math

class World():
    """
    The state of the world consists of a party, the trail, and the time (datetime). Each turn we update the state of the
    world.
    """
    def __init__(self, date_and_time, party=None, trail=None):
        self.party = party
        self.trail = trail
        self.date_and_time = date_and_time
        self.event_counter = dict()

    def update(self, strategy):
        # decide what action to take
        self.party.action = self.party.decide(strategy, self.date_and_time)
        # print self.party.action

        # update state based on action
        time_elapsed_in_hours, events = self.party.update(self.trail, self.date_and_time)

        for event, value in events.iteritems():
            self.event_counter.setdefault(event, dict())
            self.event_counter[event].setdefault(value, 0)
            self.event_counter[event][value] += 1

        minutes_elapsed, hours_elapsed = math.modf(time_elapsed_in_hours)
        hours_elapsed = int(hours_elapsed)
        minutes_elapsed = int(round(60 * minutes_elapsed))
        self.date_and_time += datetime.timedelta(hours=hours_elapsed, minutes=minutes_elapsed)