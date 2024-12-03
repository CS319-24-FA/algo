from algo_ip import *
import random

def generate_tour(day_count):
    guide_count = random.choice([1,1,1,1,1,1,2,2,2,3])
    priority = random.choice(64*[5] + 16*[6,4] + 8*[7,3] + 4*[8,2] + 2*[9,1] + [10])
    range_width = random.randint(10,20)
    start_day = random.randint(0,day_count-range_width-1)
    end_day = start_day + range_width

    return (guide_count, priority, (start_day*4,end_day*4))

def generate_guide():
    rating = random.choice(64*[5] + 16*[6,4] + 8*[7,3] + 4*[8,2] + 2*[9,1] + [10])
    availability = []
    while True:
        availability = [random.choice([True,False]) for i in range(28)]
        if availability.count(True) < 10:
            continue
        break
    return (rating,availability)

algo = AlgorithmIP(60, 2, 2)
for i in range(100):
    algo.add_tour(i, *generate_tour(60))
for i in range(50):
    algo.add_guide(i, *generate_guide())

algo.initialize()
print("initialized")
print(algo.solve())
