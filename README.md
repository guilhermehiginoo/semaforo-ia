# Semaforo-IA

**Disciplina:** Introdução à Inteligência Artificial  
**Semestre:** 2025.2  
**Professor:** ANDRE LUIS FONSECA FAUSTINO
**Turma:** T03

## Integrantes do Grupo
* GUILHERME HIGINO DE ARAÚJO SILVA (20240018849)
* VITOR GABRIEL QUEIROZ DA COSTA (20240030861)
*  MAURÍCIO COSTA PIRES (20240010967)

## Descrição do Projeto
O projeto Semaforo-IA desenvolve um controlador de semáforo inteligente cujo objetivo principal é minimizar o tempo de espera dos veículos em um cruzamento. Utilizamos simulações baseadas em filas, sensores ruidosos e eventos de prioridade para comparar heurísticas tradicionais com abordagens orientadas por IA (ex.: aprendizado por reforço ou modelos preditivos). A simulação permite experimentar parâmetros como taxa de chegada, tempo mínimo/ máximo de verde, detecção de pedestres e eventos de prioridade (ambulância, ônibus).

A solução combina:
- Um ambiente de simulação discreto (filas e dinâmica simples de veículos).
- Controladores atuados (heurísticos adaptativos).
- Integração para treinar/avaliar agentes de IA visando reduzir o tempo médio de espera e aumentar a vazão.

## Guia de Instalação e Execução
[Descreva os passos para instalacao e execucao do projeto. Inclua um passo-a-passo claro de como utilizar a proposta desenvolvida. Veja o exemplo abaixo.]

### 1. Instalação das Dependências
Certifique-se de ter o **Python 3.x** instalado. Clone o repositório e instale as bibliotecas listadas no `requirements.txt`:

```bash
# Clone o repositório
git clone [https://github.com/guilhermehiginoo/semaforo-ia.git](https://github.com/guilhermehiginoo/semaforo-ia.git)

# Entre na pasta do projeto
cd semaforo-ia

# Instale as dependências
pip install -r requirements.txt
````

### 2. Como Executar

Execute o comando abaixo no terminal para iniciar o servidor local:

```bash
# Exemplo para Streamlit
streamlit run src/app.py
```

Se necessário, especifique a porta ou url de acesso, ex: http://localhost:8501

## Estrutura dos Arquivos

[Descreva brevemente a organização das pastas]

  * `src/`: Código-fonte da aplicação ou scripts de processamento.
  * `notebooks/`: Análises exploratórias, testes e prototipagem.
  * `data/`: Datasets utilizados (se o tamanho permitir o upload).
  * `assets/`: Imagens, logos ou gráficos de resultados.

## Resultados e Demonstração

O notebook gera:

métricas de desempenho (total de veículos atendidos, tempo médio de espera, eventos de prioridade),
série temporal do tamanho das filas e
distribuição dos tempos de verde adotados pelo controlador.

## Referências

  * [Link para o Dataset original]
  * [Artigo, Documentação ou Tutorial utilizado como base]