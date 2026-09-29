"""Pipeline de limpeza, transformação e análise de transações financeiras."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sem janela: funciona em qualquer ambiente
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RISCO_DICT = {
    "C100": "Baixo",
    "C101": "Alto",
    "C102": "Médio",
    "C103": "Baixo",
    "C104": "Alto",
}


# ---------------------------------------------------------------
# 1. INGESTÃO E LIMPEZA
# ---------------------------------------------------------------
def carregar_transacoes(caminho: str) -> pd.DataFrame:
    """Lê o CSV (latin1) com dtypes otimizados para reduzir memória."""
    return pd.read_csv(
        caminho,
        encoding="latin1",
        dtype={
            "id_cliente": "category",
            "estado_cliente": "category",
            "origem": "category",
            "valor": "float32",
        },
        parse_dates=["data_transacao"],
    )


def imputar_valor_mediana_por_estado(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    mediana = df.groupby("estado_cliente", observed=True)["valor"].transform("median")
    df["valor"] = df["valor"].fillna(mediana)
    return df


# ---------------------------------------------------------------
# 2. ENGENHARIA TEMPORAL
# ---------------------------------------------------------------
def adicionar_colunas_temporais(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["data_transacao"] = pd.to_datetime(df["data_transacao"]).astype("datetime64[ns]")
    df["data_transacao"] = df["data_transacao"].dt.tz_localize("America/Sao_Paulo")
    df["dia_semana"] = df["data_transacao"].dt.day_name()
    df["mes"] = df["data_transacao"].dt.month
    return df


# ---------------------------------------------------------------
# 3. FILTRO BITWISE
# ---------------------------------------------------------------
def filtrar_setembro_sp_rj(df: pd.DataFrame, limite: float = 5000) -> pd.DataFrame:
    mask = (
        (df["mes"] == 9)
        & ((df["estado_cliente"] == "SP") | (df["estado_cliente"] == "RJ"))
        & (df["valor"] > limite)
    )
    return df[mask]


# ---------------------------------------------------------------
# 4. RISCO E PIVOT
# ---------------------------------------------------------------
def adicionar_risco(df: pd.DataFrame, risco_dict: dict = RISCO_DICT) -> pd.DataFrame:
    df = df.copy()
    df["nivel_risco"] = df["id_cliente"].astype(str).map(risco_dict)
    return df


def criar_pivot(df: pd.DataFrame) -> pd.DataFrame:
    return pd.pivot_table(
        df,
        values="valor",
        index="mes",
        columns="nivel_risco",
        aggfunc="sum",
        margins=True,
        margins_name="Total",
    )


# ---------------------------------------------------------------
# 5. Z-SCORE
# ---------------------------------------------------------------
def zscore_por_grupo(
    dados: pd.DataFrame, col: str = "valor", grupo: str = "estado_cliente"
) -> pd.Series:
    """Z = (x - média) / desvio, por grupo, totalmente vetorizado."""
    g = dados.groupby(grupo, observed=True)[col]
    return (dados[col] - g.transform("mean")) / g.transform("std")


def detectar_anomalias(df: pd.DataFrame, limite: float = 2.5) -> pd.DataFrame:
    df = df.copy()
    df["zscore"] = zscore_por_grupo(df)
    return df[df["zscore"] > limite]


# ---------------------------------------------------------------
# 6. GRÁFICO
# ---------------------------------------------------------------
def gerar_grafico(df: pd.DataFrame, caminho_saida: str) -> None:
    diario = df.set_index("data_transacao")["valor"].resample("D").sum()
    media_movel = diario.rolling(7).mean()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(diario.index, diario.values, label="Valor total diário", color="#1f77b4", alpha=0.6)
    ax.plot(media_movel.index, media_movel.values, label="Média móvel 7 dias",
            color="#d62728", linewidth=2.5)
    ax.set_ylim(bottom=0)
    ax.set_title("Valor Total de Transações Diárias e Média Móvel de 7 Dias")
    ax.set_xlabel("Data")
    ax.set_ylabel("Valor total (R$)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(caminho_saida, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------
# ORQUESTRAÇÃO
# ---------------------------------------------------------------
def main(entrada: str = "transacoes.csv", pasta_saida: str = "saida") -> dict:
    saida = Path(pasta_saida)
    saida.mkdir(parents=True, exist_ok=True)

    df = carregar_transacoes(entrada)
    df = imputar_valor_mediana_por_estado(df)
    df["plataforma"] = "Mobile"
    df = adicionar_colunas_temporais(df)

    n_antes = len(df)
    df = df.drop_duplicates(keep="first").reset_index(drop=True)
    print(f"Duplicatas removidas: {n_antes - len(df)}")

    filtrado = filtrar_setembro_sp_rj(df)
    print(f"Setembro, SP/RJ, valor > 5000: {len(filtrado)} transações")

    df = adicionar_risco(df)
    pivot = criar_pivot(df)
    print("\nPivot (soma do valor por mês x nível de risco):")
    print(pivot.round(2))

    df["zscore"] = zscore_por_grupo(df)
    anomalias = df[df["zscore"] > 2.5]
    print(f"\nAnomalias (Z > 2.5): {len(anomalias)}")

    gerar_grafico(df, str(saida / "grafico_transacoes.png"))
    df.to_csv(saida / "transacoes_tratadas.csv", index=False)
    anomalias.to_csv(saida / "anomalias.csv", index=False)
    filtrado.to_csv(saida / "filtro_setembro_sp_rj.csv", index=False)
    pivot.to_csv(saida / "pivot_mes_risco.csv")
    print(f"\nArquivos salvos em: {saida.resolve()}")

    return {"df": df, "filtrado": filtrado, "pivot": pivot, "anomalias": anomalias}


if __name__ == "__main__":
    main()
