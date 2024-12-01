import pulp as pl

class AlgorithmIP:
    def __init__(self, day_count, weekly_workload, max_slot_load):
        self.day_count = day_count
        self.guides = []
        self.tours = []
        self.tour_map = {}
        self.tour_count = 0
        self.guide_count = 0
        self.weekly_workload = weekly_workload
        self.max_slot_load = max_slot_load
        self.problem = LpProblem("Scheduler", pl.LpMaximize)

    def add_tour(self, id, guide_count, priority, range, fixed_pos=None, fixed=False):
        self.tours.append({"id":id, "guide_count":guide_count, "priority":priority,
             "range":range, "fixed_pos":fixed_pos, "fixed":fixed})
        self.tour_map[id] = len(self.tours)-1
        self.tour_count += 1
    
    def add_guide(self, id, rating, availability, fixed_tour_ids = None):
        availability_arr = []
        index = 0
        for i in range(self.day_count*4):
            availability_arr.append(availability[index%28])
            index += 1
        if fixed_tour_ids != None:
            for tour_id in fixed_tour_ids:
                tour_index = self.tour_map[tour_id]
                if self.tours[tour_index]["fixed"]:
                    availability_arr[tours[tour_index]["fixed_pos"]] = True
        
        self.guides.append({"id": id, "rating":rating, "availability":availability_arr,
                         "fixed_tour_ids":fixed_tour_ids})
        self.guide_count += 1

    def create_variables():
        self.guide_labels = range(guide_count)
        self.tour_labels = range(tours_count)
        self.slot_labels = range(day_count*4)
        self.assign_vars = pulp.LpVariable.dicts("assign", (guide_labels,tour_labels,slot_labels), cat="Binary")
        self.tour_vars = pulp.LpVariable.dicts("tours", (tour_labels,slot_labels), cat="Binary")

        #forces tours to be assigned to unique time slots
        for tour_i in self.tour_labels:
            for slot_i in self.tour_labels:
                self.problem += lpSum(self.assign_vars[guide_i][tour_i][slot_i]\
                     for guide_i in guide_labels) == 5 * self.tour_vars[tour_i][slot_i]

    def add_fixed_constraints():
        #adds manually made adjustments as constraints
        for tour_i in self.tour_labels:
            if self.tours[tour_i]["fixed"]:
                pos = self.tours[tour_i]["fixed_pos"]
                for guide_i in self.guide_labels:
                    for slot_i in self.slot_labels:
                        if slot_i != pos:
                            self.problem += self.assign_vars[guide_i][tour_i][slot_i] == 0
                        else:
                            pass
                self.problem += pl.lpSum(self.assign_vars[guide_i][tour_i][pos] \
                    for guide_i in self.guide_labels) == self.tours[tour_i]["guide_count"]
        for guide_i in self.guide_labels:
            if self.guides[guide_i]["fixed_tour_ids"] != None:
                tour_ids = self.guides[guide_i]["fixed_tour_ids"]
                for tour_id in tour_ids:
                    tour_index = self.tour_map[tour_id]
                    self.problem += \
                        pl.lpSum(self.assign_vars[guide_i][tour_index][slot_i]\
                             for slot_i in self.slot_labels) == 1
    
    def add_gcount_constraints():
        #every tour must be assigned as many guides as it requires
        for tour_i in self.tour_labels:
            self.problem += pl.lpSum(self.assign_vars[guide_i][tour_i][slot_i]\
                    for guide_i in self.guide_labels \
                        for slot_i in self.slot_labels) == self.tours[tour_i]["guide_count"]
    
    def add_availability_constraints():
        #adds availability constraints
        for guide_i in self.guide_labels:
            nonavailability = []
            for slot_i in self.slot_labels:
                if not self.guides[guide_i]["availability"][slot_i]:
                    nonavailability.append(slot_i)
            for tour_i in self.tour_labels:
                for slot_i in nonavailability:
                    problem += self.assign_vars[guide_i][tour_i][slot_i] == 0
    
    def add_slotload_constraints():
        #only a certain amount of tours can start in the same tour
        for slot_i in self.slot_labels:
            self.problem += \
                pl.lpSum(self.assign_vars[guide_i][tour_i][slot_i] \
                    for slot_i in self.slot_labels for guide_i in self.guide_labels) \
                <= self.max_slot_load
    
    def add_workload_constraints():
        #a guide can only work a certain amount of times per week
        for guide_i in self.guide_labels:
            for week_start in range(0, self.day_count*4, 7*4):
                week_range = range(week_start,week_start+7*24)
                self.problem += \
                    pl.lpSum(self.assign_vars[guide_i][tour_i][slot_i] \
                        for tour_i in self.tour_labels for slot_i in week_range) \
                    <= self.weekly_workload
    
    def add_assignonce_constraints():
        #a guide can not be assigned to multiple tours in a single time slot
        for guide_i in self.guide_labels:
            for slot_i in self.slot_labels:
                self.problem += pl.lpSum(self.assign_vars[guide_i][tour_i][slot_1] \
                    for tour_i in self.tour_labels) <= 1

    def initialize():
        #adds all the constraints
        self.create_variables()
        self.add_fixed_constraints()
        self.add_gcount_constraints()
        self.add_availability_constraints()
        self.add_slotload_constraints()
        self.add_workload_constraints()
        self.add_assignonce_constraints()

        problem += lpSum(self.assign_vars[guide_i][tour_i][slot_i] * self.guides[guide_i]["rating"] * self.tours[tour_i]["priority"]\
                    for guide_i in self.guide_labels for tours_i in self.tour_labels\
                         for slot_i in self.slot_labels), "Objective"

    def solve():
        self.problem.solve()
        guide_ret = {}
        tours_ret = {}
        for guide_i in self.guide_labels:
            for tour_i in self.tour_labels:
                for slot_i in self.slot_labels:
                    var_value = value(self.assign_vars[guide_i][tour_i][slot_i])
                    if var_value == 0:
                        continue
                    guide_id = self.guides[guide_i]["id"]
                    if guide_id not in guide_ret:
                        guide_ret[guide_id] = []
                    tour_id = self.tours[tour_i]["id"]
                    guide_ret[guide_id].append(tour_id)
                    tours_ret[tour_id] = slot_i
        return guide_ret, tours_ret
