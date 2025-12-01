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
O projeto Semaforo-IA desenvolve um controlador de semáforo inteligente cujo objetivo principal é minimizar o tempo de espera dos veículos em um cruzamento. Utilizamos simulações baseadas em filas, sensores ruidosos e eventos de prioridade para comparar heurísticas tradicionais com abordagens orientadas por IA (ex.: aprendizado por reforço ou modelos preditivos). A simulação permite experimentar parâmetros como taxa de chegada, tempo mínimo/ máximo de verde, detecção de pedestres e eventos de prioridade (ambulância, ônibus).

A solução combina:
- Um ambiente de simulação discreto (filas e dinâmica simples de veículos).
- Controladores atuados (heurísticos adaptativos).
- Integração para treinar/avaliar agentes de IA visando reduzir o tempo médio de espera e aumentar a vazão.

## Guia de Instalação e Execução

### 1. Pré-requisitos

- Python **3.10+** instalado.
- `pip` instalado e funcionando;
- Jupyter Notebook ou Jupyter Lab (já incluído no `requirements.txt`).

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

Todas as bibliotecas necessárias (NumPy, Matplotlib, Jupyter etc.) estão listadas em `requirements.txt`.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Executar a simulação

A simulação é executada via notebook Jupyter, **não há interface web**.

```bash
# Na raiz do projeto
jupyter notebook notebooks/simulacao-trafego.ipynb

No Jupyter:

1. **Célula 1–2 (imports)**: garante que as bibliotecas estão carregadas.
2. **Célula de parâmetros**: ajuste, se desejar, por exemplo:
   - `DURACAO_SIMULACAO_MIN`: duração total da simulação (em minutos);
   - `MEDIA_CARROS_A`, `MEDIA_CARROS_B`: taxa média de chegada de veículos por minuto;
   - `G_MIN`, `G_MAX`: limites mínimo/máximo do tempo de verde;
   - `PROB_PEDESTRE`, `PROB_PRIORIDADE`: probabilidade de pedestres e eventos de prioridade.
3. **Células de definição de funções/classes**: execute uma vez (não precisam ser alteradas).
4. **Última célula**: roda a simulação, exibe as métricas no console e gera os gráficos.

Execute as células **de cima para baixo** .
### 6. Gráficos e saída em `/assets`

Ao final da execução da última célula:

- Os gráficos são exibidos na interface do Jupyter;
- UUma imagem com os resultados encontrados é gerado em `assets/`.

```text
assets/resultados_simulacao.png
```

A pasta `assets/` é criada automaticamente se não existir.

## Estrutura dos Arquivos

* `notebooks/`  
  * `simulacao-trafego.ipynb`: notebook principal com a simulação, cálculo de métricas e geração de gráficos.
* `README.md`  
  Descrição geral do projeto.
* `requirements.txt`  
  Lista de dependências Python.
* `assets/`  
  Imagens dos gráficos gerados pela simulação.

## Resultados e Demonstração

Executando `notebooks/simulacao-trafego.ipynb`, o projeto gera:

* **Métricas de desempenho**:
  * total de veículos atendidos pelo cruzamento;
  * tempo médio de espera (em segundos) dos veículos atendidos;
  * contagem de eventos de prioridade (V2I) ao longo da simulação.
* **Série temporal do tamanho das filas** em cada via:
  * gráfico de linhas com o número de veículos nas filas das vias A e B ao longo do tempo;
  * permite observar se as filas se estabilizam ou crescem sem limite.
* **Distribuição dos tempos de verde**:
  * histograma da duração das fases verdes para a via A e para a via B;
  * evidencia como o controlador ajusta dinamicamente os tempos de verde de acordo com a demanda.

## Referências

* Os dados de tráfego utilizados são **sintéticos**, gerados pela própria simulação usando processos de Poisson para modelar a chegada de veículos.
* Materiais de apoio sobre:
  * controladores de semáforo atuados e adaptativos;
  * documentação das bibliotecas utilizadas (NumPy, Matplotlib, Jupyter Notebook).