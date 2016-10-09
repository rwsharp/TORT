from stop import Stop
from util import *
from numpy import power

class River(Stop):
    '''
    River is a special stop along the trail where the party must choose an alternate travel method
    '''

    def __init__(self, name='river', mile_marker=None, add_actions=None, rem_actions=None, properties=None):
        Stop.__init__(self)

        self.kind = 'river'

        if name == 'river':
            self.name = 'river ' + str(mile_marker)
        else:
            self.name = name

        self.mile_marker = mile_marker

        # default actions
        # if nothing passed, use these defaults
        if add_actions is None:
            add_actions = list()

        if rem_actions is None:
            rem_actions = ['travel']

        if properties is None:
            properties = dict()


        self.actions.update(set(add_actions))
        self.actions.difference_update(set(rem_actions))

        if 'travel' in self.actions:
            print 'WARNING - River stop allows "travel" action: ' + str(self)

        self.properties.update(properties)


    def initialize_river_state(self, year):

        # numpy.random.gamma has k,thetha parameterization
        # shape=k, scale=theta
        #
        # k*theta = mean
        # k*theta^2 = var
        #
        # k = mean/theta
        #
        # mean*theta = var
        #
        # theta = var/mean
        # k = mean^2/var

        # create flood crest / low point history for last year, this, and next
        self.history = dict()
        mean_flood_width, std_flood_width = map(float, self.properties['river']['flood width'])
        mean_flood_depth, std_flood_depth = map(float, self.properties['river']['flood depth'])
        mean_low_width,   std_low_width   = map(float, self.properties['river']['low width'])
        mean_low_depth,   std_low_depth   = map(float, self.properties['river']['low depth'])

        for i in [-1, 0, 1]:
            flood_width = sample_gamma(mean_flood_width, std_flood_width)
            flood_depth = sample_gamma(mean_flood_depth, std_flood_depth)
            flood = {'condition': 'flood',  'width': flood_width, 'depth': flood_depth}
            self.history[random_date_in_season(year + i, self.properties['river']['flood stage'])] = flood

            low_width = sample_gamma(mean_low_width, std_low_width)
            low_depth = sample_gamma(mean_low_depth, std_low_depth)
            low = {'condition': 'low',  'width': low_width, 'depth': low_depth}
            self.history[random_date_in_season(year + i, self.properties['river']['low stage'])] = low


    def river_state(self, date):
        last_stage_date = None
        last_stage = None
        for stage_date, stage in self.history:
            if last_stage_date is not None:
                if last_stage_date <= date <= stage_date:
                    # linear interpolation of conditions
                    fraction = float((date - last_stage_date).days) / float((stage_date - last_stage_date).days)
                    width = fraction * abs(stage['width'] - last_stage['width'])
                    depth = fraction * abs(stage['depth'] - last_stage['depth'])
                    break

            last_stage_date = date
            last_stage = stage

        # tempting fate here on purpose - there's a chance that the date isn't found in an interval in the history
        # hopfully this will cause an exception because widht and depth aren't defined here, and I can revisit
        # the river_state_initialization code.
        return (width, depth)


    def ford_failure_rate(self, date):
        # automaticall fails if above 5 feet, otherwise linear interpolate down to zero
        # every 100 feet of width increases failure rate by 10%
        (width, depth) = self.river_state(date)
        max_d = 5.0
        min_d = 0.0
        failure_rate = min((depth - min_d)/(max_d - min_d) * power(1.1, width/100.0), 1.0)
        
        return failure_rate        
        
        
    def ford_food_loss_fraction(self, date):
        # automaticall fails if above 5 feet, otherwise linear interpolate down to 1 foot
        # every 100 feet of width increases failure rate by 10%
        (width, depth) = self.river_state(date)
        max_d = 5.0
        min_d = 1.0
        if depth < 2.0:
            lost_food_fraction = 0.0
        else;
            lost_food_fraction = min((depth - min_d)/(max_d - min_d) * power(1.1, width/100.0), 1.0)
        
        return lost_food_fraction      
        




