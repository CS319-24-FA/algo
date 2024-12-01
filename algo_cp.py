from ortools.sat.python import cp_model

class AlgorithmCP:
    def __init__(self, day_count, weekly_workload, max_slot_load):
        self.day_count = day_count
        self.guides = []
        self.tours = []
        self.tour_map = {}
        self.tour_count = 0
        self.guide_count = 0
        self.weekly_workload = weekly_workload
        self.max_slot_load = max_slot_load
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.variables = {}

    def add_tour(self, id, guide_count, priority, range, fixed_pos=None, fixed=False):
        self.tours.append({"id": id, "guide_count": guide_count, "priority": priority,
                           "range": range, "fixed_pos": fixed_pos, "fixed": fixed})
        self.tour_map[id] = len(self.tours) - 1
        self.tour_count += 1

    def add_guide(self, id, rating, availability, fixed_tour_ids=None):
        availability_arr = []
        index = 0
        for i in range(self.day_count * 4):
            availability_arr.append(availability[index % 28])
            index += 1
        if fixed_tour_ids is not None:
            for tour_id in fixed_tour_ids:
                tour_index = self.tour_map[tour_id]
                if self.tours[tour_index]["fixed"]:
                    availability_arr[self.tours[tour_index]["fixed_pos"]] = True

        self.guides.append({"id": id, "rating": rating, "availability": availability_arr,
                            "fixed_tour_ids": fixed_tour_ids})
        self.guide_count += 1

    def create_variables(self):
        self.guide_labels = range(self.guide_count)
        self.tour_labels = range(self.tour_count)
        self.slot_labels = range(self.day_count * 4)
        
        # Define decision variables
        self.variables["assign"] = {}
        self.variables["tours"] = {}
        
        for g in self.guide_labels:
            for t in self.tour_labels:
                for s in self.slot_labels:
                    self.variables["assign"][(g, t, s)] = self.model.NewBoolVar(f"assign_{g}_{t}_{s}")
                self.variables["tours"][(t, s)] = self.model.NewBoolVar(f"tour_{t}_{s}")
        
        # Force tours to be assigned to unique time slots
        for t in self.tour_labels:
            for s in self.slot_labels:
                self.model.Add(
                    sum(self.variables["assign"][(g, t, s)] for g in self.guide_labels)
                    == 5 * self.variables["tours"][(t, s)]
                )

    def add_fixed_constraints(self):
        # Adds manually made adjustments as constraints
        for t in self.tour_labels:
            if self.tours[t]["fixed"]:
                pos = self.tours[t]["fixed_pos"]
                for g in self.guide_labels:
                    for s in self.slot_labels:
                        if s != pos:
                            self.model.Add(self.variables["assign"][(g, t, s)] == 0)
                self.model.Add(
                    sum(self.variables["assign"][(g, t, pos)] for g in self.guide_labels)
                    == self.tours[t]["guide_count"]
                )

        for g in self.guide_labels:
            if self.guides[g]["fixed_tour_ids"] is not None:
                tour_ids = self.guides[g]["fixed_tour_ids"]
                for tour_id in tour_ids:
                    t = self.tour_map[tour_id]
                    self.model.Add(
                        sum(self.variables["assign"][(g, t, s)] for s in self.slot_labels) == 1
                    )

    def add_gcount_constraints(self):
        # Every tour must be assigned as many guides as it requires
        for t in self.tour_labels:
            self.model.Add(
                sum(self.variables["assign"][(g, t, s)] for g in self.guide_labels for s in self.slot_labels)
                == self.tours[t]["guide_count"]
            )

    def add_availability_constraints(self):
        # Adds availability constraints
        for g in self.guide_labels:
            for s in self.slot_labels:
                if not self.guides[g]["availability"][s]:
                    for t in self.tour_labels:
                        self.model.Add(self.variables["assign"][(g, t, s)] == 0)

    def add_slotload_constraints(self):
        # Only a certain amount of tours can start in the same slot
        for s in self.slot_labels:
            self.model.Add(
                sum(self.variables["assign"][(g, t, s)] for g in self.guide_labels for t in self.tour_labels)
                <= self.max_slot_load
            )

    def add_workload_constraints(self):
        # A guide can only work a certain number of times per week
        for g in self.guide_labels:
            for week_start in range(0, self.day_count * 4, 7 * 4):
                week_slots = range(week_start, week_start + min(7 * 4, self.day_count * 4))
                self.model.Add(
                    sum(self.variables["assign"][(g, t, s)] for t in self.tour_labels for s in week_slots)
                    <= self.weekly_workload
                )

    def add_assignonce_constraints(self):
        # A guide cannot be assigned to multiple tours in a single time slot
        for g in self.guide_labels:
            for s in self.slot_labels:
                self.model.Add(
                    sum(self.variables["assign"][(g, t, s)] for t in self.tour_labels) <= 1
                )

    def initialize(self):
        self.create_variables()
        self.add_fixed_constraints()
        self.add_gcount_constraints()
        self.add_availability_constraints()
        self.add_slotload_constraints()
        self.add_workload_constraints()
        self.add_assignonce_constraints()
        self.model.Maximize(
            sum(self.variables["assign"][(g, t, s)] * self.guides[g]["rating"] * self.tours[t]["priority"]
                for g in self.guide_labels for t in self.tour_labels for s in self.slot_labels)
        )

    def solve(self):
        status = self.solver.Solve(self.model)
        guide_ret = {}
        tours_ret = {}
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            for (g, t, s), var in self.variables["assign"].items():
                if self.solver.Value(var) == 1:
                    guide_id = self.guides[g]["id"]
                    if guide_id not in guide_ret:
                        guide_ret[guide_id] = []
                    tour_id = self.tours[t]["id"]
                    guide_ret[guide_id].append(tour_id)
                    tours_ret[tour_id] = s
        return guide_ret, tours_ret