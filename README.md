# Semaforo-IA

**Disciplina:** Introdução à Inteligência Artificial  
**Semestre:** 2025.2  
**Professor:** ANDRE LUIS FONSECA FAUSTINO  
**Turma:** T03

## Integrantes do Grupo
* GUILHERME HIGINO DE ARAÚJO SILVA (20240018849)
* VITOR GABRIEL QUEIROZ DA COSTA (20240030861)
* MAURÍCIO COSTA PIRES (20240010967)

## Descrição do Projeto
O projeto Semaforo-IA desenvolve um controlador de semáforo inteligente cujo objetivo principal é minimizar o tempo de espera dos veículos em um cruzamento. Utilizamos simulações baseadas em filas, sensores ruidosos e eventos de prioridade para comparar:

- Um **controlador atuado** (heurística adaptativa baseada em filas);
- Um **controlador de Q-Learning tabular** (aprendizado por reforço), com modelo pré-treinado.

A simulação permite experimentar parâmetros como taxa de chegada, tempo mínimo/máximo de verde, detecção de pedestres e eventos de prioridade (ambulância, ônibus).

A solução combina:
- Um ambiente de simulação discreto (filas e dinâmica simples de veículos);
- Controladores atuados (heurísticos adaptativos);
- Um agente de IA treinado para reduzir o tempo médio de espera e aumentar a vazão.

## Guia de Instalação e Execução

### 1. Pré-requisitos

- Python **3.10+** instalado;
- `pip` instalado e funcionando;
- Navegador web (para acessar a interface Streamlit).

### 2. Clonar o repositório

```bash
# Clone o repositório
git clone https://github.com/guilhermehiginoo/semaforo-ia.git

# Entre na pasta do projeto
cd semaforo-ia
```

### 3. (Opcional, mas recomendado) Criar ambiente virtual

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual no Linux/macOS
source .venv/bin/activate
```

### 4. Instalar as dependências

Todas as bibliotecas necessárias (NumPy, Streamlit, Plotly, Jupyter etc.) estão listadas em `requirements.txt`.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Executar a interface web (principal)

A forma principal de uso do projeto é via **interface web** em Streamlit.

```bash
# Na raiz do projeto
streamlit run app.py
```

Depois de rodar o comando acima, acesse no navegador:

- `http://localhost:8501`

Na interface você pode:

1. Ajustar os parâmetros na barra lateral:
   - duração da simulação (minutos);
   - demanda das vias A e B (veículos/minuto);
   - probabilidade de pedestres;
   - probabilidade de veículos prioritários.
2. Ajustar parâmetros avançados:
   - verde mínimo (`G_MIN`);
   - verde máximo (`G_MAX`);
   - ciclo base;
   - taxa de escoamento (veículos/s).
3. Clicar em **“▶️ Rodar Simulação”**.

A aplicação irá:

- Simular o cruzamento com:
  - **Controlador Atuado**;
  - **Controlador Q-Learning (pré-treinado)**;
- Mostrar métricas de desempenho de cada controlador:
  - veículos atendidos;
  - espera média;
  - espera máxima;
- Plotar:
  - evolução das filas ao longo do tempo;
  - distribuição dos tempos de verde;
- Exibir uma tabela de comparação final entre Atuado e Q-Learning.

> Observação: o modelo Q-Learning padrão é carregado automaticamente a partir de `models/qlearning_agent_20251202_103052_10k.pkl`.  
> Se esse arquivo não existir, o sistema tenta usar o último modelo `qlearning_agent_*.pkl` da pasta `models/`. Se nenhum modelo for encontrado, o controlador Q-Learning é inicializado com Q-table vazia (modo “não treinado”).

### 6. (Opcional) Executar simulações via Notebook

Além da interface web, é possível explorar e treinar o agente Q-Learning diretamente nos notebooks.

#### 6.1 Notebook de simulação heurística

```bash
jupyter notebook notebooks/simulacao-trafego.ipynb
```

Nesse notebook é possível:

- rodar a simulação apenas com o **controlador atuado**;
- visualizar métricas e gráficos em Matplotlib;
- ajustar manualmente parâmetros de simulação.

#### 6.2 Notebook de Q-Learning

```bash
jupyter notebook notebooks/02-simulacao-trafego-qlearning.ipynb
```

Esse notebook:

- define o ambiente de simulação;
- treina o agente de Q-Learning por milhares de episódios;
- salva modelos treinados em `models/` (por exemplo, `qlearning_agent_YYYYMMDD_HHMMSS_10k.pkl`);
- gera gráficos de aprendizado (tempo de espera, recompensa, robustez a ruído etc.).

Após treinar um novo modelo, basta salvar como:

```text
models/qlearning_agent_20251202_103052_10k.pkl
```

ou deixar com outro nome no padrão `qlearning_agent_*.pkl` para que o `app.py` possa encontrá-lo.

## Estrutura dos Arquivos

* `app.py`  
  Interface web em Streamlit. Faz a simulação com:
  - `ActuatedController` (heurístico);
  - `QLearningController` (modelo pré-treinado, carregado de `models/`).

* `src/`  
  * `controllers.py`: implementa `ActuatedController` e `QLearningController` (inclui lógica de carregar modelo pré-treinado).
  * `utils.py`: funções auxiliares (por exemplo, `ruido_sensor`).
  * Outros módulos de suporte à simulação.

* `models/`  
  Modelos de Q-Learning treinados (arquivos `.pkl`), por exemplo:
  - `qlearning_agent_20251202_103052_10k.pkl` (modelo padrão da entrega).

* `notebooks/`  
  * `simulacao-trafego.ipynb`: notebook principal de simulação heurística.
  * `02-simulacao-trafego-qlearning.ipynb`: notebook de treinamento/avaliação do Q-Learning.

* `assets/`  
  Imagens dos gráficos gerados pelos notebooks (`*.png`).

* `README.md`  
  Este arquivo.

* `requirements.txt`  
  Lista de dependências Python.

## Resultados e Demonstração

Usando a interface web (`streamlit run app.py`), o projeto gera, para cada controlador:

* **Métricas de desempenho**:
  * total de veículos atendidos;
  * tempo médio de espera (em segundos);
  * tempo máximo de espera.

* **Série temporal do tamanho das filas**:
  * gráfico de linhas com o número de veículos nas filas das vias A e B ao longo do tempo;
  * comparação lado a lado entre Atuado e Q-Learning.

* **Distribuição dos tempos de verde**:
  * histogramas da duração das fases verdes para via A e via B;
  * permite analisar o padrão de alocação de verde de cada estratégia de controle.

* **Tabela de comparação final**:
  * consolida as métricas de Atuado vs Q-Learning;
  * destaca automaticamente o melhor valor em cada métrica.

## Referências

* Os dados de tráfego utilizados são **sintéticos**, gerados pela própria simulação usando processos de Poisson para modelar a chegada de veículos.
* Materiais de apoio sobre:
  * materiais e orientações dados em aula;
  * controladores de semáforo atuados e adaptativos;
  * aprendizado por reforço (Q-Learning) aplicado a controle de tráfego;
  * documentação das bibliotecas utilizadas (NumPy, Streamlit, Plotly, Jupyter).