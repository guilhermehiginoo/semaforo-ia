import streamlit as st
import numpy as np
import random
from collections import deque, defaultdict
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os
import time
import matplotlib.pyplot as plt
from math import sqrt, ceil # Necessário para a nova lógica de movimento

# Configuração da página
st.set_page_config(page_title="Simulação de Tráfego", layout="wide")

# =========================
# Classes da simulação (Refatoradas para Cinemática)
# =========================

class Vehicle:
    def __init__(self, id, is_bus=False):
        self.id = id
        self.is_bus = is_bus
        # Posição negativa: veículos vêm de longe (-X) em direção à linha de parada (0)
        self.pos = -random.uniform(20, 40)
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
        self.total_wait = 0.0

    def add_vehicles(self, n, start_id, bus_prob=0.0):
        added_count = 0
        for i in range(n):
            is_bus = random.random() < bus_prob
            v = Vehicle(start_id + i, is_bus=is_bus)
            self.vehicles.append(v)
            added_count += 1
        return added_count

    def queue_length(self):
        # A fila é o número total de veículos
        return len(self.vehicles)

    def step_logic(self, is_green, dt, discharge_rate):
        passed_now = 0
        waited_sum = 0.0
        
        vehicles_to_remove = []

        # 1. Atualizar tempos de espera e aplicar movimento cinemático
        for i in range(len(self.vehicles)):
            veh = self.vehicles[i]
            
            # 1.1. Determinar Obstáculo e Distância
            # Linha de parada (0.0) ou carro da frente
            if i == 0:
                # Obstáculo: Linha de parada
                target_pos = 0.0
            else:
                # Obstáculo: Carro da frente (posição do carro i-1)
                target_pos = self.vehicles[i-1].pos
            
            # Distância ao obstáculo (sem contar o tamanho do carro)
            # Carros vêm de pos negativa em direção a 0, então dist_to_next é positivo
            dist_to_next = target_pos - veh.pos
            
            # === LÓGICA DE ACELERAÇÃO/DESACELERAÇÃO (IDM Simplificado) ===
            accel = veh.max_accel # Aceleração padrão (acelerar)
            
            # a) Parar no Sinal Vermelho
            if i == 0 and not is_green:
                if dist_to_next <= 1.0: # Muito perto da linha de parada
                    accel = veh.max_decel * 2.0 # Frenagem forte
                elif veh.speed > 0.0:
                    # Decelerar para parar em 0.0
                    # Deceleração necessária = (v^2) / (2 * s)
                    required_decel = -(veh.speed ** 2) / (2 * dist_to_next + 1e-6)
                    accel = max(veh.max_decel, required_decel)
                else:
                    accel = 0.0 # Parado
            
            # b) Acelerar/Seguir Carro da Frente
            elif i > 0:
                safe_gap = 2.0 # Distância de segurança mínima
                
                if dist_to_next <= safe_gap:
                    # Frear para manter distância mínima
                    accel = veh.max_decel 
                elif dist_to_next > veh.pos: # Livre para acelerar
                     accel = veh.max_accel
                else:
                    accel = 0.0 # Manter distância
            
            # c) Acelerar com Sinal Verde
            elif i == 0 and is_green:
                 # Se houver espaço, acelera até a velocidade máxima
                accel = veh.max_accel * (1 - (veh.speed / veh.max_speed)**4)


            # 2. Aplicar Limites e Atualizar Cinemática
            
            # Limitar aceleração e desaceleração
            accel = max(veh.max_decel, min(accel, veh.max_accel))
            
            # Atualizar velocidade e posição (Euler)
            veh.speed += accel * dt
            
            # Limitar velocidade
            veh.speed = max(0.0, min(veh.speed, veh.max_speed))

            # Movimento
            move = veh.speed * dt
            
            # Prevenir Colisão e Passagem (ajuste final de posição)
            if i > 0:
                # O carro não pode passar o carro da frente
                max_move = target_pos - veh.pos - 1.0 
                move = min(move, max_move)
                
            elif i == 0 and not is_green:
                # O primeiro carro não pode passar a linha de parada
                max_move = target_pos - veh.pos 
                if max_move < move:
                    veh.speed = 0.0
                    move = max_move
            
            veh.pos += move

            # 3. Atualizar Tempo de Espera
            if veh.speed < 0.1:
                veh.wait_time += dt
            
            # 4. Lógica de Escoamento (Saída do Carro)
            # O veículo 0 atinge uma posição de "saída" e o sinal está verde
            if i == 0 and veh.pos >= 5.0 and is_green:
                vehicles_to_remove.append(veh)

        
        # Remove veículos que saíram (escoamento)
        for v in vehicles_to_remove:
            # O escoamento depende da taxa, então fazemos a probabilidade aqui:
            if random.random() < (discharge_rate * dt):
                self.vehicles.remove(v)
                waited_sum += v.wait_time
                self.passed += 1
                passed_now += 1
        
        return passed_now, waited_sum

# =========================
# Funções auxiliares (Mantidas)
# =========================
# Importa apenas Atuado e Q-Learning
try:
    from src.controllers import ActuatedController, QLearningController
except ImportError:
    # Se rodando app.py isoladamente, define classes placeholder ou usa um mock
    class ControllerMock:
        def __init__(self, *args, **kwargs):
            self.phase = "A"
            self.green_times_log = []
            self.phase_time = 0
            self.yellow_time = 3
        def step(self, dt, **kwargs):
            self.phase_time += dt
            if self.phase == "A" and self.phase_time > 15: self.phase = "YELLOW B"; self.phase_time = 0
            elif self.phase == "YELLOW B" and self.phase_time > self.yellow_time: self.phase = "B"; self.phase_time = 0
            elif self.phase == "B" and self.phase_time > 15: self.phase = "YELLOW A"; self.phase_time = 0
            elif self.phase == "YELLOW A" and self.phase_time > self.yellow_time: self.phase = "A"; self.phase_time = 0
            return self.phase
        
    ActuatedController = ControllerMock
    QLearningController = ControllerMock
    st.warning("Não foi possível importar controllers. Usando Controlador Mock Simples.")


def ruido_sensor(valor_real, erro_max=0.15):
    if valor_real <= 0: return 0
    fator = 1 + random.uniform(-erro_max, erro_max)
    return max(0, int(valor_real * fator))

def gerar_fluxo_carros(taxa_media_minuto, tempo_decorrido_sec):
    lambda_poisson = (taxa_media_minuto / 60) * tempo_decorrido_sec
    return np.random.poisson(lambda_poisson)

def detectar_prioridade(probabilidade):
    return random.random() < probabilidade

def detectar_pedestre(probabilidade):
    return random.random() < probabilidade

# =========================
# Classe TrafficSimulator (Substituindo run_simulation)
# =========================

class TrafficSimulator:
    def __init__(self, controller_cls, params, seed=42):
        random.seed(seed)
        np.random.seed(seed)
        
        self.params = params
        self.laneA = Lane("A")
        self.laneB = Lane("B")
        self.controller = controller_cls(self.laneA, self.laneB, params)

        self.t = 0.0
        self.vehicle_id = 0
        self.total_passed = 0
        self.total_wait_passed = 0.0
        self.max_wait_seen = 0.0
        self.duration = params.get('duracao_sec', 600)
        self.is_running = True
        
        # Geração inicial de tráfego para preencher as filas
        self.laneA.add_vehicles(15, self.vehicle_id, self.params.get('prob_prioridade', 0.0))
        self.vehicle_id += 15
        self.laneB.add_vehicles(15, self.vehicle_id, self.params.get('prob_prioridade', 0.0))
        self.vehicle_id += 15

    def step(self, dt):
        """Avança a simulação em um passo de tempo (dt)."""
        if self.t >= self.duration:
            self.is_running = False
            return self.get_current_state()

        # 1. Geração de Chegadas
        chegA = gerar_fluxo_carros(self.params['media_a'], dt)
        chegB = gerar_fluxo_carros(self.params['media_b'], dt)
        self.laneA.add_vehicles(chegA, self.vehicle_id, self.params.get('prob_prioridade', 0.0))
        self.vehicle_id += chegA
        self.laneB.add_vehicles(chegB, self.vehicle_id, self.params.get('prob_prioridade', 0.0))
        self.vehicle_id += chegB

        # 2. Detecção de Eventos
        ped_A = detectar_pedestre(self.params['prob_pedestre'] * dt)
        ped_B = detectar_pedestre(self.params['prob_pedestre'] * dt)
        v2i_A = detectar_prioridade(self.params['prob_prioridade'] * dt)
        v2i_B = detectar_prioridade(self.params['prob_prioridade'] * dt)

        # 3. Controlador Decide e Atua
        current_phase = self.controller.step(
            dt, ped_A=ped_A, ped_B=ped_B, v2i_A=v2i_A, v2i_B=v2i_B, training=False,
        )

        # 4. Processa Movimento
        is_green_A = (current_phase == 'A')
        is_green_B = (current_phase == 'B')

        pA, wA = self.laneA.step_logic(is_green_A, dt, self.params['taxa_escoamento'])
        pB, wB = self.laneB.step_logic(is_green_B, dt, self.params['taxa_escoamento'])

        # 5. Atualiza Métricas Globais
        self.total_passed += pA + pB
        self.total_wait_passed += wA + wB
        
        wait_times = [v.wait_time for v in self.laneA.vehicles] + [v.wait_time for v in self.laneB.vehicles]
        if wait_times:
            self.max_wait_seen = max(self.max_wait_seen, max(wait_times))
            
        self.t += dt
        
        return self.get_current_state()
        
    def get_current_state(self):
        avg_wait = self.total_wait_passed / max(1, self.total_passed)
        
        # Estrutura de dados para o visualizador
        return {
            't': self.t,
            'qA': self.laneA.queue_length(),
            'qB': self.laneB.queue_length(),
            'phase': self.controller.phase,
            'total_passed': self.total_passed,
            'avg_wait': avg_wait,
            'max_wait': self.max_wait_seen,
            'vehicles_A': [{'pos': v.pos, 'is_bus': v.is_bus, 'speed': v.speed} for v in self.laneA.vehicles],
            'vehicles_B': [{'pos': v.pos, 'is_bus': v.is_bus, 'speed': v.speed} for v in self.laneB.vehicles],
        }

# =========================
# Função de Visualização (Matplotlib 2D)
# =========================

def plot_simulation_state(state):
    """Gera o gráfico 2D do cruzamento e dos veículos."""
    fig, ax = plt.subplots(figsize=(7, 7))
    
    # Parâmetros Geométricos
    LANE_WIDTH = 4.0 # Largura da via
    LANE_START = -50.0 # Onde os carros começam
    LANE_END = 0.0     # Linha de parada
    
    # 1. Desenhar Vias (Horizontal A e Vertical B)
    # Via A (Horizontal)
    ax.plot([LANE_START, LANE_END], [LANE_WIDTH / 2, LANE_WIDTH / 2], 'k-', alpha=0.5)
    ax.plot([LANE_START, LANE_END], [-LANE_WIDTH / 2, -LANE_WIDTH / 2], 'k-', alpha=0.5)
    
    # Via B (Vertical)
    ax.plot([LANE_WIDTH / 2, LANE_WIDTH / 2], [LANE_START, LANE_END], 'k-', alpha=0.5)
    ax.plot([-LANE_WIDTH / 2, -LANE_WIDTH / 2], [LANE_START, LANE_END], 'k-', alpha=0.5)
    
    # Área do Cruzamento
    ax.fill_between([LANE_END, LANE_WIDTH/2], [-LANE_WIDTH/2, -LANE_WIDTH/2], [LANE_WIDTH/2, LANE_WIDTH/2], color='gray', alpha=0.1)
    ax.fill_between([-LANE_WIDTH/2, LANE_END], [-LANE_WIDTH/2, -LANE_WIDTH/2], [LANE_WIDTH/2, LANE_WIDTH/2], color='gray', alpha=0.1)
    
    # 2. Semáforos
    phase = state['phase']
    
    # Cores
    color_A = 'green' if phase == 'A' else ('orange' if 'YELLOW A' in phase else 'red')
    color_B = 'green' if phase == 'B' else ('orange' if 'YELLOW B' in phase else 'red')
    
    # Semáforo A (na direita, para quem vem da esquerda)
    ax.scatter(LANE_END, LANE_WIDTH/2 + 1.5, s=250, color=color_A, marker='o', edgecolors='black')
    # Semáforo B (no topo, para quem vem de baixo)
    ax.scatter(-LANE_WIDTH/2 - 1.5, LANE_END, s=250, color=color_B, marker='o', edgecolors='black')
    
    # 3. Desenhar Veículos (Mapeamento 1D -> 2D)
    
    # Via A (Horizontal): pos [0 a -50] -> x [0 a -50]
    for veh in state['vehicles_A']:
        x_pos = veh['pos']
        y_pos = LANE_WIDTH / 4 # Posição na faixa
        color = '#1f77b4' if not veh['is_bus'] else '#d62728'
        marker = 's' if not veh['is_bus'] else 'D' 
        ax.scatter(x_pos, y_pos, color=color, marker=marker, s=50, alpha=0.9)

    # Via B (Vertical): pos [0 a -50] -> y [0 a -50]
    for veh in state['vehicles_B']:
        x_pos = LANE_WIDTH / 4
        y_pos = veh['pos']
        color = '#ff7f0e' if not veh['is_bus'] else '#8c564b'
        marker = 's' if not veh['is_bus'] else 'D'
        ax.scatter(x_pos, y_pos, color=color, marker=marker, s=50, alpha=0.9)
        
    # 4. Configurações Finais
    ax.set_xlim(LANE_START - 5, 5.0)
    ax.set_ylim(LANE_START - 5, 5.0)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title(f"Visualização da Simulação | Tempo: {state['t']:.1f}s")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    
    return fig

# =========================
# Interface Streamlit
# =========================

st.title("🚦 Simulação de Cruzamento Semaforizado")
st.markdown("Comparação entre **Controlador Atuado** e **Q-Learning (pré-treinado)**")

# Sidebar com parâmetros
st.sidebar.header("⚙️ Parâmetros da Simulação")

# Parâmetros principais (mantidos)
duracao_min = st.sidebar.slider("Duração (minutos)", 1, 30, 5) # Reduzido para real-time
media_a = st.sidebar.slider("Demanda Via A (veíc/min)", 5, 50, 20)
media_b = st.sidebar.slider("Demanda Via B (veíc/min)", 5, 50, 10)
prob_pedestre = st.sidebar.slider("Prob. Pedestre", 0.0, 1.0, 0.3)
prob_prioridade = st.sidebar.slider("Prob. Veículo Prioritário", 0.0, 0.2, 0.05)
seed = st.sidebar.number_input("Semente (seed)", 0, 10000, 42)

# Parâmetros avançados
with st.sidebar.expander("Parâmetros Avançados"):
    g_min = st.slider("Verde Mínimo (s)", 10, 60, 16)
    g_max = st.slider("Verde Máximo (s)", 30, 120, 90)
    ciclo = st.slider("Ciclo Padrão (s)", 30, 120, 60)
    taxa_escoamento = st.slider("Taxa Escoamento (veíc/s)", 0.3, 1.5, 0.6)

# Parâmetros da Simulação (mantidos)
params = {
    'duracao_sec': duracao_min * 60,
    'media_a': media_a,
    'media_b': media_b,
    'prob_pedestre': prob_pedestre,
    'prob_prioridade': prob_prioridade,
    'dt': 1, # O dt da simulação (será usado no step), mantido em 1s para o loop
    'sample_rate': 1,
    'g_min': g_min,
    'g_max': g_max,
    'ciclo': ciclo,
    'yellow_time': 3,
    'taxa_escoamento': taxa_escoamento,
}

# Lógica de carregamento do modelo Q-Learning (mantida)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
DEFAULT_MODEL_NAME = "qlearning_agent_20251202_103052_10k.pkl"
default_model_path = os.path.join(MODELS_DIR, DEFAULT_MODEL_NAME)
pretrained_path = None
# ... (lógica de busca de modelo omitida por brevidade, mas mantida no código)
if os.path.exists(default_model_path):
    pretrained_path = default_model_path
else:
    if os.path.isdir(MODELS_DIR):
        candidate_files = [f for f in os.listdir(MODELS_DIR) if f.startswith("qlearning_agent_") and f.endswith(".pkl")]
        if candidate_files:
            candidate_files.sort()
            latest_model = candidate_files[-1]
            pretrained_path = os.path.join(MODELS_DIR, latest_model)

if pretrained_path and os.path.exists(pretrained_path):
    params_q = {**params, "pretrained_path": pretrained_path, "epsilon": 0.0}
    st.sidebar.success(f"Usando Q-Learning pré-treinado: {os.path.basename(pretrained_path)}")
else:
    params_q = {**params}
    st.sidebar.warning("Nenhum modelo Q-Learning pré-treinado encontrado. Usando Q-table vazia.")

# =========================================================
# Seção de Simulação em Tempo Real (NOVA)
# =========================================================
st.subheader("📺 Visualizador em Tempo Real")
col_vis, col_speed = st.columns([3, 1])

# Seleção do Controlador para Visualização
controller_options = {'Atuado': (ActuatedController, params), 'Q-Learning': (QLearningController, params_q)}
selected_controller_name = col_vis.selectbox(
    "Escolha o Controlador para Visualizar", 
    options=list(controller_options.keys())
)
controller_cls, controller_params = controller_options[selected_controller_name]

# Fator de Aceleração Visual
VISUAL_SPEED_FACTOR = col_speed.slider(
    "Fator de Aceleração Visual (x)", 
    0.1, 5.0, 1.0, 
    help="1.0 é 'tempo real'. Fatores maiores aceleram a visualização."
)
TIME_STEP = params['dt'] # dt da simulação
SLEEP_TIME = TIME_STEP / VISUAL_SPEED_FACTOR # Pausa para visualização

# Botão para iniciar a visualização
if st.button("▶️ Iniciar Visualização em Tempo Real", type="primary"):
    
    # 1. Inicializa o Simulador
    simulator = TrafficSimulator(controller_cls, controller_params, seed)
    
    # 2. Cria Placeholders
    st.subheader(f"Simulação do Controlador: {selected_controller_name}")
    visualization_placeholder = st.empty() 
    metrics_placeholder = st.empty()

    # 3. Loop de Simulação
    with st.spinner(f"Rodando simulação {selected_controller_name} em tempo real..."):
        
        while simulator.is_running:
            
            # Avança a simulação no tempo
            state = simulator.step(TIME_STEP)
            
            # ATUALIZAÇÃO DA VISUALIZAÇÃO
            with visualization_placeholder.container():
                fig = plot_simulation_state(state)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig) # Importante para liberar memória
                
            # ATUALIZAÇÃO DAS MÉTRICAS
            with metrics_placeholder.container():
                st.markdown(f"**Tempo de Simulação:** `{state['t']:.1f}s` | **Fase:** `{state['phase']}`")
                st.markdown(f"**Filas (A/B):** `{state['qA']}` / `{state['qB']}` | **Veículos Atendidos:** `{state['total_passed']}`")
                st.markdown(f"**Tempo Médio de Espera:** `{state['avg_wait']:.2f}s` | **Espera Máxima:** `{state['max_wait']:.2f}s`")
                st.markdown("---")
                
            # Pausa para controle de FPS/Velocidade
            time.sleep(SLEEP_TIME)

    st.success(f"✅ Simulação em Tempo Real Concluída! Métricas Finais:")
    
    # Exibe métricas finais após o loop
    st.metric(f"Total de Veículos Atendidos ({selected_controller_name})", f"{state['total_passed']}")
    st.metric(f"Tempo Médio de Espera ({selected_controller_name})", f"{state['avg_wait']:.2f}s")
    st.metric(f"Tempo Máximo de Espera ({selected_controller_name})", f"{state['max_wait']:.2f}s")
    
    st.markdown("---")
    
    # Opcional: Salvar os resultados da simulação real-time para comparação futura (ou seções abaixo)
    st.session_state['realtime_metrics'] = state


# =========================================================
# Seção de Simulação em Lote (Batch) e Comparação (EXISTENTE)
# =========================================================

st.sidebar.markdown("---")
st.sidebar.header("Comparação em Lote")

# O botão para rodar simulação em batch (mantido na sidebar)
if st.sidebar.button("▶️ Rodar Simulação (Batch)", type="secondary"):
    
    # É necessário definir a função run_simulation novamente para a versão Batch, 
    # ou adaptar a classe TrafficSimulator.
    # Vamos manter a função run_simulation original, mas renomeá-la para BatchRun,
    # pois a classe TrafficSimulator agora tem a lógica de step.
    
    # Para simplicidade e evitar confusão, vamos rodar a simulação em lote usando a antiga lógica
    # que o usuário tinha (função run_simulation). Se o usuário não tiver o run_simulation original
    # (pois eu pedi para remover), este bloco dará erro. 
    # Eu vou recriar a função run_simulation aqui para compatibilidade:
    
    # ================
    # Recriação da função de batch (run_simulation)
    # ================
    def run_simulation_batch(controller_cls, params, run_seed):
        random.seed(run_seed)
        np.random.seed(run_seed)

        # Usando as classes Lane e Vehicle do app.py (agora cinemáticas)
        laneA = Lane("A")
        laneB = Lane("B")
        controller = controller_cls(laneA, laneB, params)

        t = 0
        vehicle_id = 0
        snapshots = []
        total_passed = 0
        total_wait_passed = 0.0
        max_wait_seen = 0.0
        priority_events = 0
        
        # Otimizando para batch: usar um dt maior para desempenho se necessário
        dt = params['dt'] # 1 segundo

        while t < params['duracao_sec']:
            chegA = gerar_fluxo_carros(params['media_a'], dt)
            chegB = gerar_fluxo_carros(params['media_b'], dt)
            laneA.add_vehicles(chegA, vehicle_id, bus_prob=params['prob_prioridade'])
            vehicle_id += chegA
            laneB.add_vehicles(chegB, vehicle_id, bus_prob=params['prob_prioridade'])
            vehicle_id += chegB

            ped_A = detectar_pedestre(params['prob_pedestre'] * dt)
            ped_B = detectar_pedestre(params['prob_pedestre'] * dt)
            v2i_A = detectar_prioridade(params['prob_prioridade'] * dt)
            v2i_B = detectar_prioridade(params['prob_prioridade'] * dt)

            current_phase = controller.step(
                dt, ped_A=ped_A, ped_B=ped_B, v2i_A=v2i_A, v2i_B=v2i_B, training=False,
            )

            green_A = current_phase == "A" or "YELLOW A" in current_phase
            green_B = current_phase == "B" or "YELLOW B" in current_phase

            pA, wA = laneA.step_logic(green_A, dt, params['taxa_escoamento'])
            pB, wB = laneB.step_logic(green_B, dt, params['taxa_escoamento'])

            total_passed += pA + pB
            total_wait_passed += wA + wB
            
            wait_times = [v.wait_time for v in laneA.vehicles] + [v.wait_time for v in laneB.vehicles]
            if wait_times:
                max_wait_seen = max(max_wait_seen, max(wait_times))

            if t % params['sample_rate'] == 0:
                snapshots.append({
                    "t": t,
                    "qA": laneA.queue_length(),
                    "qB": laneB.queue_length(),
                    "phase": current_phase,
                })
            t += dt

        return {
            "total_passed": total_passed,
            "avg_wait": total_wait_passed / max(1, total_passed),
            "max_wait": max_wait_seen,
            "priority_events": priority_events,
            "snapshots": snapshots,
            "green_log": controller.green_times_log,
        }
    # ================
    
    with st.spinner("Simulando em lote..."):
        metrics_act = run_simulation_batch(ActuatedController, params, seed)
        metrics_qlearn = run_simulation_batch(QLearningController, params_q, seed)
        
        st.session_state['metrics_act'] = metrics_act
        st.session_state['metrics_qlearn'] = metrics_qlearn
        st.session_state['simulated'] = True
    st.success("✅ Simulação em lote concluída! Role para baixo para ver a comparação.")


# Mostrar resultados (Mantido o código de visualização em lote)
if st.session_state.get('simulated'):
    metrics_act = st.session_state['metrics_act']
    metrics_qlearn = st.session_state['metrics_qlearn']
    
    st.subheader("📊 Métricas de Desempenho (Comparação em Lote)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Controlador Atuado**")
        st.metric("Veículos Atendidos", f"{metrics_act['total_passed']}")
        st.metric("Espera Média", f"{metrics_act['avg_wait']:.1f}s")
        st.metric("Espera Máxima", f"{metrics_act['max_wait']:.1f}s")
    
    with col2:
        st.markdown("**Q-Learning**")
        st.metric("Veículos Atendidos", f"{metrics_qlearn['total_passed']}")
        st.metric("Espera Média", f"{metrics_qlearn['avg_wait']:.1f}s")
        st.metric("Espera Máxima", f"{metrics_qlearn['max_wait']:.1f}s")
    
    # Código dos gráficos Plotly (Evolução das Filas e Distribuição de Tempos de Verde)
    # ... (O código Plotly original do usuário foi omitido aqui para brevidade, mas está subentendido)
    # [Start of original Plotly code]
    
    # Gráfico de filas
    st.subheader("📈 Evolução das Filas ao Longo do Tempo")
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Controlador Atuado", "Q-Learning"),
        shared_xaxes=True
    )
    
    # Atuado
    times_act = [s['t'] for s in metrics_act['snapshots']]
    qA_act = [s['qA'] for s in metrics_act['snapshots']]
    qB_act = [s['qB'] for s in metrics_act['snapshots']]
    # cores com bom contraste
    fig.add_trace(
        go.Scatter(
            x=times_act,
            y=qA_act,
            name="Via A (atuado)",
            line=dict(color="#1f77b4")  # azul
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=times_act,
            y=qB_act,
            name="Via B (atuado)",
            line=dict(color="#ff7f0e")  # laranja
        ),
        row=1, col=1
    )
    
    # Q-Learning
    times_qlearn = [s['t'] for s in metrics_qlearn['snapshots']]
    qA_qlearn = [s['qA'] for s in metrics_qlearn['snapshots']]
    qB_qlearn = [s['qB'] for s in metrics_qlearn['snapshots']]
    fig.add_trace(
        go.Scatter(
            x=times_qlearn,
            y=qA_qlearn,
            name="Via A (Q-Learning)",
            line=dict(color="#2ca02c", dash="dot")  # verde
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=times_qlearn,
            y=qB_qlearn,
            name="Via B (Q-Learning)",
            line=dict(color="#9467bd", dash="dot")  # roxo
        ),
        row=2, col=1
    )
    
    fig.update_xaxes(title_text="Tempo (s)", row=2, col=1)
    fig.update_yaxes(title_text="Fila (veículos)", row=1, col=1)
    fig.update_yaxes(title_text="Fila (veículos)", row=2, col=1)
    fig.update_layout(height=700, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    
    # Histograma de tempos de verde
    st.subheader("⏱️ Distribuição dos Tempos de Verde")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Controlador Atuado**")
        verdes_A_act = [t for p, t in metrics_act['green_log'] if p == 'A']
        verdes_B_act = [t for p, t in metrics_act['green_log'] if p == 'B']
        fig_act = go.Figure()
        fig_act.add_trace(
            go.Histogram(
                x=verdes_A_act,
                name="Via A",
                marker_color="#1f77b4",  # azul
                opacity=0.75
            )
        )
        fig_act.add_trace(
            go.Histogram(
                x=verdes_B_act,
                name="Via B",
                marker_color="#ff7f0e",  # laranja
                opacity=0.75
            )
        )
        fig_act.update_layout(
            barmode="overlay",
            xaxis_title="Duração (s)",
            yaxis_title="Frequência",
            height=400
        )
        st.plotly_chart(fig_act, use_container_width=True)
    
    with col2:
        st.markdown("**Q-Learning**")
        verdes_A_qlearn = [t for p, t in metrics_qlearn['green_log'] if p == 'A']
        verdes_B_qlearn = [t for p, t in metrics_qlearn['green_log'] if p == 'B']
        fig_qlearn = go.Figure()
        fig_qlearn.add_trace(
            go.Histogram(
                x=verdes_A_qlearn,
                name="Via A",
                marker_color="#2ca02c",  # verde
                opacity=0.75
            )
        )
        fig_qlearn.add_trace(
            go.Histogram(
                x=verdes_B_qlearn,
                name="Via B",
                marker_color="#9467bd",  # roxo
                opacity=0.75
            )
        )
        fig_qlearn.update_layout(
            barmode="overlay",
            xaxis_title="Duração (s)",
            yaxis_title="Frequência",
            height=400
        )
        st.plotly_chart(fig_qlearn, use_container_width=True)

    # Comparação final
    st.subheader("🏆 Comparação de Desempenho")

    comparison_df = pd.DataFrame({
        'Método': ['Atuado', 'Q-Learning'],
        'Veículos Atendidos': [
            metrics_act['total_passed'],
            metrics_qlearn['total_passed']
        ],
        'Espera Média (s)': [
            round(metrics_act['avg_wait'], 1),
            round(metrics_qlearn['avg_wait'], 1)
        ],
        'Espera Máxima (s)': [
            round(metrics_act['max_wait'], 1),
            round(metrics_qlearn['max_wait'], 1)
        ]
    })

    # DataFrame simples, sem highlight em verde
    st.dataframe(comparison_df, use_container_width=True)
    # [End of original Plotly code]

else:
    st.info("👈 Configure os parâmetros na barra lateral e clique em 'Iniciar Visualização em Tempo Real' ou 'Rodar Simulação (Batch)'.")
    st.markdown("### Como funciona?")
    st.markdown("""
    1. **Ajuste os parâmetros** na barra lateral (demanda das vias, probabilidades, etc.)
    2. **Clique em 'Iniciar Visualização em Tempo Real'** para ver a animação do tráfego.
    3. **Clique em 'Rodar Simulação (Batch)'** para calcular as métricas dos dois controladores de uma vez e comparar.
    """)