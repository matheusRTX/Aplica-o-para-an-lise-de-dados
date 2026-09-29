

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
