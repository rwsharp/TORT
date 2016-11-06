import datetime
import math

class World():
    """
    The state of the world consists of a party, the trail, and the time (datetime). Each turn we update the state of the
    world.
    """
    def __init__(self, party=None, trail=None, dt=None):
        self.party = party
        self.trail = trail
        self.dt = dt

    def update(self, strategy):
        # decide what action to take
        self.party.action = self.party.decide(strategy)
        print self.party.action

        # update state based on action
        time_elapsed_in_hours = self.party.update(self.trail, self.dt)

        minutes_elapsed, hours_elapsed = math.modf(time_elapsed_in_hours)
        hours_elapsed = int(hours_elapsed)
        minutes_elapsed = int(round(60 * minutes_elapsed))
        self.dt += datetime.timedelta(hours=hours_elapsed, minutes=minutes_elapsed)