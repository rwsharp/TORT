class Stop():
    '''
    A Stop exists at each mile marker along the trail. Most of these are a generic Camp, but special stops like rivers
     and towns are also to be found. The party makes a decision at each stop, depending the actions available to it.
     Typically these are to travel on or to rest, but others may be available. Sometimes you will encounter a malady
     or comfort at a stop, such as disease, snake bite, bear attack, food, water, abandoned provisions, etc.
    '''

    def __init__(self):
        self.name = None
        self.kind = None
        self.mile_marker = None
        self.actions = set(['travel', 'rest'])
        self.properties = dict()
        self.malady = None
        self.comfort = None
