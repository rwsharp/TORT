from stop import Stop

class Camp(Stop):
    '''
    Camp is the standard stop on the trail when travelling between towns, forts, and rivers.
    A camp is the only type of stop where you can hunt, so hunting related items are contained in this class.
    '''
    
    def __init__(self, name='camp', mile_marker=None, add_actions=None, rem_actions=None, properties=None):

        Stop.__init__(self)

        self.kind = 'camp'

        if name == 'camp':
            self.name = 'camp ' + str(mile_marker)
        else:
            self.name = name

        self.mile_marker = mile_marker

        # default actions
        # if nothing passed, use these defaults
        if add_actions is None:
            add_actions = ['hunt']

        if rem_actions is None:
            rem_actions = list()

        if properties is None:
            properties = dict()

        self.actions.update(add_actions)
        self.actions.difference_update(rem_actions)

        self.properties.update(properties)


    """
    def hunt(self, shooter):
        # get game levels from self.trail.terrain

        # shooter has accuracy, ammo, target preference, stopping criteria

        # a hunting session consists of 100 time steps
        # at each, decide if there is a shot opportunity
        # decide if the shot opportunity is go/no go for the hunter (includes stop criteria)
        # if it's a go, decide if it'sa hit
        # advance the day by 1 - hunting takes 1 day
    """