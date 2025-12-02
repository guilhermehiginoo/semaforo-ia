import numpy as np
import random
from collections import deque

class Vehicle:
    def __init__(self, id, is_bus=False):
        self.id = id
        self.is_bus = is_bus
        self.pos = -random.uniform(5, 25)
        self.wait_time = 0.0

class Lane:
    def __init__(self, name):
        self.name = name
        self.vehicles = deque()
        self.passed = 0

    def add_vehicles(self, n, start_id, bus_prob=0.0):
        for i in range(n):
            is_bus = random.random() < bus_prob
            v = Vehicle(start_id + i, is_bus=is_bus)
            self.vehicles.append(v)
        return n

    def queue_length(self):
        return len(self.vehicles)

    def step_logic(self, is_green, dt, discharge_rate):
        passed_now = 0
        waited_sum = 0.0
        
        if is_green:
            expected = discharge_rate * dt
            base = int(np.floor(expected))
            extra = 1 if random.random() < (expected - base) else 0
            capacity = base + extra

            for _ in range(capacity):
                if not self.vehicles: break
                if self.vehicles[0].pos > -2: 
                    v = self.vehicles.popleft()
                    waited_sum += v.wait_time
                    self.passed += 1
                    passed_now += 1
        
        for i, veh in enumerate(self.vehicles):
            # ...existing movement logic...
            dist_to_next = 100
            if i > 0:
                dist_to_next = self.vehicles[i-1].pos - veh.pos - 2

            if is_green:
                move = min(1.5 * dt, 5.0)
            else:
                target = 0 if i == 0 else (self.vehicles[i-1].pos - 2)
                dist = target - veh.pos
                move = max(0, min(dist, 1.5 * dt))
            
            if i > 0 and move > dist_to_next:
                move = max(0, dist_to_next)
                
            veh.pos += move
            
            if move < 0.1:
                veh.wait_time += dt

        return passed_now, waited_sum
