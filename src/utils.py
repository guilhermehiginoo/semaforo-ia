import numpy as np
import random

class TrafficSimulator:
    """Gerencia o estado e avança a simulação passo a passo."""
    # (Copiar e adaptar o código da antiga run_simulation para dentro desta classe)
    
    def __init__(self, controller_cls, params, seed=42):
        # ... (Configuração inicial: random.seed, laneA, laneB, controller, params)
        self.t = 0.0
        self.vehicle_id = 0
        self.total_passed = 0
        self.total_wait_passed = 0.0
        self.max_wait_seen = 0.0
        self.duration = params.get('duracao', 3600)
        self.is_running = True
        
        # Geração inicial de tráfego para preencher as filas
        self.add_initial_traffic(10, 10)

    def add_initial_traffic(self, nA, nB):
        # Lógica para adicionar nA e nB veículos em A e B
        self.laneA.add_vehicles(nA, self.vehicle_id, self.params.get('prob_prioridade', 0.0))
        self.vehicle_id += nA
        self.laneB.add_vehicles(nB, self.vehicle_id, self.params.get('prob_prioridade', 0.0))
        self.vehicle_id += nB

    def step(self, dt):
        """Avança a simulação em um passo de tempo (dt)."""
        if self.t >= self.duration:
            self.is_running = False
            return self.get_current_state()

        # 1. Geração de Chegadas (usando dt como tempo decorrido)
        chegA = gerar_fluxo_carros(self.params['media_a'], dt)
        chegB = gerar_fluxo_carros(self.params['media_b'], dt)
        self.laneA.add_vehicles(chegA, self.vehicle_id, self.params.get('prob_prioridade', 0.0))
        self.vehicle_id += chegA
        self.laneB.add_vehicles(chegB, self.vehicle_id, self.params.get('prob_prioridade', 0.0))
        self.vehicle_id += chegB

        # 2. Controlador Decide e Atua
        self.controller.step(dt)
        current_phase = self.controller.phase

        # 3. Processa Movimento (chama o novo step_logic)
        is_green_A = (current_phase == 'A')
        is_green_B = (current_phase == 'B')

        pA, wA = self.laneA.step_logic(is_green_A, dt, self.params['taxa_escoamento'])
        pB, wB = self.laneB.step_logic(is_green_B, dt, self.params['taxa_escoamento'])

        # 4. Atualiza Métricas Globais
        self.total_passed += pA + pB
        self.total_wait_passed += wA + wB
        # ... (Atualiza max_wait_seen, etc.)
        self.t += dt
        
        # Retorna o estado completo para o app.py
        return self.get_current_state()
        
    def get_current_state(self):
        # ... (Lógica para calcular avg_wait e retornar o dicionário de estado)
        # IMPORTANTE: Incluir as listas de veículos (pos, speed, is_bus) no retorno:
        return {
            # ... (qA, qB, t, phase, total_passed, avg_wait, max_wait_seen)
            'vehicles_A': [{'pos': v.pos, 'is_bus': v.is_bus, 'speed': v.speed} for v in self.laneA.vehicles],
            'vehicles_B': [{'pos': v.pos, 'is_bus': v.is_bus, 'speed': v.speed} for v in self.laneB.vehicles],
            'phase': self.controller.phase,
        }

def ruido_sensor(valor_real, erro_max=0.15):
    """Simula erro de leitura do sensor"""
    if valor_real <= 0: return 0
    fator = 1 + random.uniform(-erro_max, erro_max)
    return max(0, int(valor_real * fator))

def gerar_fluxo_carros(taxa_media_minuto, tempo_decorrido_sec):
    """Gera chegadas baseado em Poisson"""
    lambda_poisson = (taxa_media_minuto / 60) * tempo_decorrido_sec
    return np.random.poisson(lambda_poisson)

def run_simulation(controller_cls, params, seed=42):
    """Executa uma simulação completa"""
    from .simulation import Lane
    
    random.seed(seed)
    np.random.seed(seed)

    laneA = Lane("A")
    laneB = Lane("B")
    controller = controller_cls(laneA, laneB, params)

    t = 0
    vehicle_id = 0
    snapshots = []
    total_passed = 0
    total_wait_passed = 0.0
    max_wait_seen = 0.0

    while t < params['duracao_sec']:
        # Gera chegadas
        chegA = gerar_fluxo_carros(params['media_a'], params['dt'])
        chegB = gerar_fluxo_carros(params['media_b'], params['dt'])
        laneA.add_vehicles(chegA, vehicle_id, bus_prob=params.get('prob_prioridade', 0.0))
        vehicle_id += chegA
        laneB.add_vehicles(chegB, vehicle_id, bus_prob=params.get('prob_prioridade', 0.0))
        vehicle_id += chegB

        # Controlador decide
        current_phase = controller.step(params['dt'])

        # Processa movimento
        green_A = (current_phase == 'A')
        green_B = (current_phase == 'B')

        pA, wA = laneA.step_logic(green_A, params['dt'], params['taxa_escoamento'])
        pB, wB = laneB.step_logic(green_B, params['dt'], params['taxa_escoamento'])

        total_passed += pA + pB
        total_wait_passed += wA + wB
        
        wait_times = [v.wait_time for v in laneA.vehicles] + [v.wait_time for v in laneB.vehicles]
        if wait_times:
            max_wait_seen = max(max_wait_seen, max(wait_times))

        if t % params.get('sample_rate', 1) == 0:
            snapshots.append({
                "t": t,
                "qA": laneA.queue_length(),
                "qB": laneB.queue_length(),
                "phase": current_phase,
            })
        t += params['dt']

    return {
        "total_passed": total_passed,
        "avg_wait": total_wait_passed / max(1, total_passed),
        "max_wait": max_wait_seen,
        "snapshots": snapshots,
        "green_log": controller.green_times_log,
    }
