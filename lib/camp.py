class Camp():
    '''
    Camp is the standard stop on the trail when travelling between towns, forts, and rivers
    '''
    
    def __init__(self, mile_marker):
        self.stop = {'name': 'camp',
                     'mile marker': mile_marker,
                     'type': 'camp',
                     'services': [{'hunt': {}}]
                     }
