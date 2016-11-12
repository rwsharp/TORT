import datetime
import numpy

def main():

    # test the hunger / thirst / fatigue formula
    format = '%Y-%m-%d %H:%M'
    T0 = datetime.datetime.strptime('2016-11-12 06:00', format)
    health = 100.0
    hunger = 0.0
    a = 0.039
    delta = 1.0 # hours

    T = T0
    print health, hunger
    for t in range(10000):
        health = health - hunger * delta
        if health <= 0:
            print 'Time of death:', datetime.datetime.strftime(T, format)
            print 'Lifetime:', (T - T0)
            break
        hunger = hunger  + a*delta
        T = T + datetime.timedelta(hours=delta)
        # print health, hunger

    # test the pack weight modified formula
    bw = 190.
    mph = 4.0
    for pw in range(10, 200, 5):
        print pw, (pw/bw*100*6), 1.0 / (((3600/mph) + (pw/bw*100*6))/3600.0)



if __name__ == '__main__':
    main()