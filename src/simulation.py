# No arquivo 'simulation.py'
import numpy as np
import random
from collections import deque
from math import sqrt, ceil # Importar sqrt e ceil

class Vehicle:
    def __init__(self, id, is_bus=False):
        self.id = id
        self.is_bus = is_bus
        self.pos = random.uniform(5, 25)
        self.wait_time = 0.0
        
        # NOVOS ATRIBUTOS para cinemática
        self.speed = 0.0          # Velocidade atual (m/s)
        self.max_speed = 12.0     # ~43 km/h
        self.max_accel = 2.0      # Aceleração máxima (m/s^2)
        self.max_decel = -4.0     # Desaceleração máxima (Frenagem)

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
        
        # 1. Atualizar tempos de espera e aplicar movimento cinemático
        for i, veh in enumerate(self.vehicles):
            veh.wait_time += dt

            # Determinar obstáculo (Linha de Parada ou Carro da Frente)
            if i == 0:
                # Obstáculo: Linha de parada (pos=0)
                target_pos = 0.0
            else:
                # Obstáculo: Carro da frente
                target_pos = self.vehicles[i-1].pos
            
            dist_to_next = target_pos - veh.pos
            
            # === LÓGICA DE ACELERAÇÃO/DESACELERAÇÃO (IDM Simplificado) ===
            accel = 0.0
            
            if i == 0 and not is_green:
                # Frear para o sinal
                safe_dist = 5.0 # Distância de segurança para parar
                
                if veh.pos > safe_dist:
                    accel = veh.max_accel # Acelerar até perto da linha de parada
                elif veh.pos <= safe_dist:
                    # Calcular frenagem necessária para parar em 0.0
                    required_decel = (veh.speed ** 2) / (2 * veh.pos + 1e-6)
                    accel = max(veh.max_decel, -required_decel)

            elif i == 0 and is_green:
                # Acelerar livremente (sinal verde)
                accel = veh.max_accel * (1 - (veh.speed / veh.max_speed)**4)
            
            elif i > 0:
                # Seguir o carro da frente
                if dist_to_next > 5.0:
                    accel = veh.max_accel * 0.5 # Acelerar moderadamente
                elif dist_to_next < 2.0:
                    accel = veh.max_decel # Frear forte
                else:
                    accel = 0.0 # Manter
                    
            # Limitar aceleração e desaceleração
            accel = max(veh.max_decel, min(accel, veh.max_accel))
            
            # Atualizar cinemática (Velocidade e Posição)
            veh.speed += accel * dt
            veh.speed = max(0.0, min(veh.speed, veh.max_speed)) # Limitar min 0 e max
            
            veh.pos += veh.speed * dt
            
            # Evitar ultrapassagem/colisão
            if i > 0 and veh.pos >= self.vehicles[i-1].pos:
                veh.pos = self.vehicles[i-1].pos - 1.0
                veh.speed = self.vehicles[i-1].speed
            elif i == 0 and veh.pos > target_pos and not is_green:
                veh.pos = 0.0
                veh.speed = 0.0
            
        # 2. Lógica de Escoamento (Saída do Carro)
        # Sai quando o veículo 0 atinge uma posição de "saída" e o sinal está verde
        if self.vehicles and self.vehicles[0].pos >= 5.0 and is_green:
            v = self.vehicles.popleft()
            waited_sum += v.wait_time
            self.passed += 1
            passed_now = 1 # Apenas 1 carro sai por passo para visualização

        return passed_now, waited_sum
