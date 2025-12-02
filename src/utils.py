import numpy as np
import random

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
