import numpy as np
import random
from collections import defaultdict
import pickle
from .utils import ruido_sensor

class ActuatedController:
    """Controlador atuado (heurística inteligente)"""
    def __init__(self, laneA, laneB, params):
        self.laneA = laneA
        self.laneB = laneB
        self.phase = 'A'
        self.phase_time = 0
        self.params = params
        self.green_limit = params.get('g_max', 90)
        self.green_times_log = []

    def sense(self):
        return ruido_sensor(self.laneA.queue_length()), ruido_sensor(self.laneB.queue_length())

    def decide(self, **kwargs):
        detA, detB = self.sense()
        
        if 'YELLOW' in self.phase:
            if self.phase_time >= self.params.get('yellow_time', 3):
                return 'next_green'
            return 'hold'

        current_lane_q = detA if self.phase == 'A' else detB
        other_lane_q = detB if self.phase == 'A' else detA
        
        if current_lane_q <= 1 and self.phase_time >= self.params.get('g_min', 16) and other_lane_q > 0:
            return 'switch'
        if self.phase_time >= self.green_limit:
            return 'switch'

        return 'hold'

    def step(self, dt, **kwargs):
        action = self.decide(**kwargs)
        
        if action == 'hold':
            self.phase_time += dt
        elif action == 'switch':
            self.green_times_log.append((self.phase, self.phase_time))
            self.phase = f"YELLOW_{self.phase}"
            self.phase_time = 0
        elif action == 'next_green':
            self.phase = 'B' if self.phase == 'YELLOW_A' else 'A'
            self.phase_time = 0
            
            qA = max(1, self.laneA.queue_length())
            qB = max(1, self.laneB.queue_length())
            ratio = qA / (qA + qB) if self.phase == 'A' else qB / (qA + qB)
            self.green_limit = int(np.clip(self.params['ciclo'] * ratio, self.params['g_min'], self.params['g_max']))

        return self.phase

class QLearningController:
    """Controlador Q-Learning (RL)"""
    def __init__(self, laneA, laneB, params):
        self.laneA = laneA
        self.laneB = laneB
        self.phase = 'A'
        self.phase_time = 0
        
        # Hiperparâmetros
        self.alpha = params.get('alpha', 0.1)
        self.gamma = params.get('gamma', 0.95)
        self.epsilon = params.get('epsilon', 0.01)  # Baixo para modo teste
        
        # Q-Table
        self.q_table = defaultdict(lambda: np.zeros(2))
        
        # Parâmetros de controle
        self.g_min = params.get('g_min', 16)
        self.g_max = params.get('g_max', 90)
        self.yellow_time = params.get('yellow_time', 3)
        self.in_yellow = False
        self.yellow_timer = 0
        self.green_times_log = []

        # Carrega modelo pré-treinado se fornecido
        pretrained_path = params.get("pretrained_path")
        if pretrained_path:
            try:
                with open(pretrained_path, "rb") as f:
                    loaded = pickle.load(f)
                # aceita tanto objeto agente quanto só a q_table
                if hasattr(loaded, "q_table"):
                    q_src = loaded.q_table
                else:
                    q_src = loaded
                # garante defaultdict com shape correto
                if isinstance(q_src, defaultdict):
                    self.q_table = q_src
                else:
                    self.q_table = defaultdict(lambda: np.zeros(2))
                    self.q_table.update(q_src)
                # exploração praticamente desligada para uso em teste
                self.epsilon = params.get("epsilon", 0.0)
            except Exception as e:
                # Falha silenciosa mas controlada: usa Q-table vazia
                print(f"[QLearningController] Falha ao carregar modelo pré-treinado ({pretrained_path}): {e}")
        
    def discretize_state(self):
        qA = self.laneA.queue_length()
        qB = self.laneB.queue_length()
        
        def bin_queue(q):
            if q <= 2: return 0
            elif q <= 5: return 1
            elif q <= 10: return 2
            elif q <= 20: return 3
            else: return 4
        
        def bin_time(t):
            if t <= 15: return 0
            elif t <= 30: return 1
            elif t <= 60: return 2
            else: return 3
        
        qA_bin = bin_queue(qA)
        qB_bin = bin_queue(qB)
        phase_id = 0 if self.phase == 'A' else 1
        time_bin = bin_time(self.phase_time)
        
        return (qA_bin, qB_bin, phase_id, time_bin)

    def select_action(self, state, training=False):
        if training and random.random() < self.epsilon:
            return random.randint(0, 1)
        else:
            return np.argmax(self.q_table[state])

    def step(self, dt, training=False, **kwargs):
        # Gerencia amarelo
        if self.in_yellow:
            self.yellow_timer += dt
            if self.yellow_timer >= self.yellow_time:
                self.green_times_log.append((self.phase, self.phase_time))
                self.phase = 'B' if self.phase == 'A' else 'A'
                self.phase_time = 0
                self.in_yellow = False
                self.yellow_timer = 0
            return self.phase
        
        state = self.discretize_state()
        action = self.select_action(state, training=training)
        
        should_switch = (action == 1)
        
        if should_switch and self.phase_time >= self.g_min:
            self.in_yellow = True
            self.yellow_timer = 0
        elif self.phase_time >= self.g_max:
            self.in_yellow = True
            self.yellow_timer = 0
        else:
            self.phase_time += dt
        
        return self.phase