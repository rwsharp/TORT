from random import sample
from datetime import datetime, timedelta
#from numpy import power
from math import pow
#from numpy.random import randint, gamma
from random import randint, gammavariate

def date_to_season(date):
    # Crude, but close enough
    vernal_equinox = datetime(date.year, 3, 21)
    summer_solstice = datetime(date.year, 6, 21)
    autumnal_equinox = datetime(date.year, 9, 21)
    winter_solstice = datetime(date.year, 12, 21)

    if date < vernal_equinox:
        season = 'winter'
    elif vernal_equinox <= date < summer_solstice:
        season = 'spring'
    elif summer_solstice <= date < autumnal_equinox:
        season = 'summer'
    elif autumnal_equinox <= date < winter_solstice:
        season = 'fall'
    elif winter_solstice <= date:
        season = 'winter'
    else:
        raise ValueError('ERROR - Something is wrong with date; you should never get here.')

    return season


def random_date_in_season(year, season):
    vernal_equinox = datetime(year, 3, 21)
    summer_solstice = datetime(year, 6, 21)
    autumnal_equinox = datetime(year, 9, 21)
    winter_solstice = datetime(year, 12, 21)

    if season == 'spring':
        rd = random_date(vernal_equinox, summer_solstice)
    elif season == 'summer':
        rd = random_date(summer_solstice, autumnal_equinox)
    elif season == 'fall':
        rd = random_date(autumnal_equinox, winter_solstice)
    elif season == 'winter 1':
        rd = random_date(datetime(year, 1, 1), vernal_equinox)
    elif season == 'winter 2':
        rd = random_date(winter_solstice, datetime(year + 1, 1, 1))
    elif season == 'winter':
        rd1 = random_date(datetime(year, 1, 1), vernal_equinox)
        rd2 = random_date(winter_solstice, datetime(year + 1, 1, 1))
        rd = sample((rd1, rd2), 1)[0]
    else:
        raise ValueError('ERROR - unrecognized season: ' + str(season))

    return rd


def random_date(min_date, max_date):
    days_between = (max_date - min_date).days
    offset = randint(0, days_between-1)
    rd = min_date + timedelta(days=offset)

    return rd


def sample_gamma(mean, std, size=None):

    var = pow(std, 2)

    k = pow(mean, 2) / var
    theta = var / mean

    return [gammavariate(k, theta) for i in range(size)]
