import streamlit as st
import numpy as np
import random
from collections import deque, defaultdict
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Simulação de Tráfego", layout="wide")

# =========================
# Classes da simulação
# =========================

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
                if not self.vehicles:
                    break
                if self.vehicles[0].pos > -2: 
                    v = self.vehicles.popleft()
                    waited_sum += v.wait_time
                    self.passed += 1
                    passed_now += 1
        
        for i, veh in enumerate(self.vehicles):
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

# Funções auxiliares
def ruido_sensor(valor_real, erro_max=0.15):
    if valor_real <= 0:
        return 0
    fator = 1 + random.uniform(-erro_max, erro_max)
    return max(0, int(valor_real * fator))

def gerar_fluxo_carros(taxa_media_minuto, tempo_decorrido_sec):
    lambda_poisson = (taxa_media_minuto / 60) * tempo_decorrido_sec
    return np.random.poisson(lambda_poisson)

def detectar_prioridade(probabilidade):
    return random.random() < probabilidade

def detectar_pedestre(probabilidade):
    return random.random() < probabilidade

# Importa apenas Atuado e Q-Learning
from src.controllers import ActuatedController, QLearningController

# Função de simulação
def run_simulation(controller_cls, params, run_seed):
    random.seed(run_seed)
    np.random.seed(run_seed)

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

    while t < params['duracao_sec']:
        chegA = gerar_fluxo_carros(params['media_a'], params['dt'])
        chegB = gerar_fluxo_carros(params['media_b'], params['dt'])
        laneA.add_vehicles(chegA, vehicle_id, bus_prob=params['prob_prioridade'])
        vehicle_id += chegA
        laneB.add_vehicles(chegB, vehicle_id, bus_prob=params['prob_prioridade'])
        vehicle_id += chegB

        ped_A = detectar_pedestre(params['prob_pedestre'] * params['dt'])
        ped_B = detectar_pedestre(params['prob_pedestre'] * params['dt'])
        v2i_A = detectar_prioridade(params['prob_prioridade'] * params['dt'])
        v2i_B = detectar_prioridade(params['prob_prioridade'] * params['dt'])
        if v2i_A or v2i_B:
            priority_events += 1

        # chamada compatível com todos os controladores
        current_phase = controller.step(
            params['dt'],
            ped_A=ped_A,
            ped_B=ped_B,
            v2i_A=v2i_A,
            v2i_B=v2i_B,
            training=False,  # ignorado por Actuated/FixedTime
        )

        green_A = current_phase == "A"
        green_B = current_phase == "B"

        pA, wA = laneA.step_logic(green_A, params['dt'], params['taxa_escoamento'])
        pB, wB = laneB.step_logic(green_B, params['dt'], params['taxa_escoamento'])

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
        t += params['dt']

    return {
        "total_passed": total_passed,
        "avg_wait": total_wait_passed / max(1, total_passed),
        "max_wait": max_wait_seen,
        "priority_events": priority_events,
        "snapshots": snapshots,
        "green_log": controller.green_times_log,
    }

# =========================
# Interface Streamlit
# =========================

st.title("🚦 Simulação de Cruzamento Semaforizado")
st.markdown("Comparação entre **Controlador Atuado** e **Q-Learning (pré-treinado)**")

# Sidebar com parâmetros
st.sidebar.header("⚙️ Parâmetros da Simulação")

duracao_min = st.sidebar.slider("Duração (minutos)", 1, 60, 10)
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

params = {
    'duracao_sec': duracao_min * 60,
    'media_a': media_a,
    'media_b': media_b,
    'prob_pedestre': prob_pedestre,
    'prob_prioridade': prob_prioridade,
    'dt': 1,
    'sample_rate': 1,
    'g_min': g_min,
    'g_max': g_max,
    'ciclo': ciclo,
    'yellow_time': 3,
    'taxa_escoamento': taxa_escoamento,
}

# Caminho do modelo Q-Learning pré-treinado (commitado no repo)
# raiz do projeto = diretório pai de app.py
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

# Nome do modelo *padrão* que você quer usar
DEFAULT_MODEL_NAME = "qlearning_agent_20251202_103052_10k.pkl"
default_model_path = os.path.join(MODELS_DIR, DEFAULT_MODEL_NAME)

pretrained_path = None

# 1) Tenta usar o modelo padrão fixo
if os.path.exists(default_model_path):
    pretrained_path = default_model_path
else:
    # 2) Se o padrão não existir, tenta achar o último modelo qlearning_agent_*.pkl
    if os.path.isdir(MODELS_DIR):
        candidate_files = [
            f for f in os.listdir(MODELS_DIR)
            if f.startswith("qlearning_agent_") and f.endswith(".pkl")
        ]
        if candidate_files:
            candidate_files.sort()  # assumindo timestamp no nome, o último é o mais recente
            latest_model = candidate_files[-1]
            pretrained_path = os.path.join(MODELS_DIR, latest_model)

# Monta params_q dependendo do que foi encontrado
if pretrained_path and os.path.exists(pretrained_path):
    params_q = {**params, "pretrained_path": pretrained_path, "epsilon": 0.0}
    st.sidebar.success(f"Usando modelo Q-Learning pré-treinado: {os.path.basename(pretrained_path)}")
else:
    params_q = {**params}
    st.sidebar.warning(
        "Nenhum modelo Q-Learning pré-treinado encontrado em 'models/'. "
        "Usando Q-table vazia."
    )

# Botão para rodar simulação
if st.sidebar.button("▶️ Rodar Simulação", type="primary"):
    with st.spinner("Simulando..."):
        metrics_act = run_simulation(ActuatedController, params, seed)
        metrics_qlearn = run_simulation(QLearningController, params_q, seed)
        
        st.session_state['metrics_act'] = metrics_act
        st.session_state['metrics_qlearn'] = metrics_qlearn
        st.session_state['simulated'] = True
    st.success("✅ Simulação concluída!")

# Mostrar resultados
if st.session_state.get('simulated'):
    metrics_act = st.session_state['metrics_act']
    metrics_qlearn = st.session_state['metrics_qlearn']
    
    # Métricas principais
    st.subheader("📊 Métricas de Desempenho")
    
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

else:
    st.info("👈 Configure os parâmetros na barra lateral e clique em 'Rodar Simulação'")
    st.markdown("### Como funciona?")
    st.markdown("""
    1. **Ajuste os parâmetros** na barra lateral (demanda das vias, probabilidades, etc.)
    2. **Clique em 'Rodar Simulação'** para executar
    3. **Compare os resultados** entre:
    
    - 🟢 **Atuado**: Heurística inteligente com detecção de filas
    - 🟣 **Q-Learning**: Controlador treinado por reforço
    
    O sistema simula um cruzamento com duas vias e mostra como cada estratégia afeta:
    - ⏱️ Tempo de espera dos veículos
    - 🚗 Número de veículos atendidos
    - 📊 Formação de filas ao longo do tempo
    """)
