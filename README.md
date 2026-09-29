# Projeto Fintech – Limpeza, Análise e Detecção de Anomalias

Pipeline em Python/Pandas para tratar logs de transações financeiras, gerar
métricas (pivot por mês x risco), detectar anomalias por Z-Score e plotar o
valor diário com média móvel de 7 dias.

## Estrutura

| Arquivo | Função |
|---|---|
| `criar_dados.py` | Gera `transacoes.csv` e `cotacoes.csv` (dados de exemplo) |
| `pipeline_fintech.py` | Pipeline completo (funções + `main()`) |
| `test_pipeline.py` | Testes automatizados (pytest) |
| `requirements.txt` | Dependências |

## Instalação

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Execução

```bash
python criar_dados.py         # gera os CSVs de entrada
python pipeline_fintech.py    # roda o pipeline
```

Saídas na pasta `saida/`: `transacoes_tratadas.csv`, `anomalias.csv`,
`filtro_setembro_sp_rj.csv`, `pivot_mes_risco.csv` e `grafico_transacoes.png`.

## Testes

```bash
pytest -v
```

## Observações

- `risco_dict`: apenas C100 e C101 foram definidos no enunciado; os demais
  clientes têm valores fictícios em `RISCO_DICT` (ajuste conforme necessário).
- `plataforma` recebe o valor estático `'Mobile'` (rastreabilidade do pipeline).
- O Z-Score é calculado por estado sobre todas as transações tratadas.
