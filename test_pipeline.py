import numpy as np
import pandas as pd
import pytest

import pipeline_fintech as p


@pytest.fixture
def df_exemplo():
    return pd.DataFrame({
        "id_cliente": ["C100", "C101", "C102", "C100", "C101", "C104"],
        "data_transacao": pd.to_datetime([
            "2026-09-01 10:00", "2026-09-02 11:00", "2026-09-03 12:00",
            "2026-09-04 13:00", "2026-10-01 14:00", "2026-09-05 15:00",
        ]),
        "valor": [6000.0, np.nan, 7000.0, 100.0, 9000.0, 8000.0],
        "estado_cliente": ["SP", "SP", "RJ", "MG", "SP", "RJ"],
        "origem": ["web", "atm", "web", "mobile_app", "web", "atm"],
    })


def test_imputacao_mediana_por_estado(df_exemplo):
    r = p.imputar_valor_mediana_por_estado(df_exemplo)
    assert r["valor"].isna().sum() == 0
    # SP tem 6000 e 9000 -> mediana 7500
    assert r.loc[1, "valor"] == 7500.0


def test_colunas_temporais_e_fuso(df_exemplo):
    r = p.adicionar_colunas_temporais(df_exemplo)
    assert str(r["data_transacao"].dt.tz) == "America/Sao_Paulo"
    assert r.loc[0, "dia_semana"] == "Tuesday"
    assert r.loc[4, "mes"] == 10


def test_filtro_bitwise(df_exemplo):
    d = p.adicionar_colunas_temporais(p.imputar_valor_mediana_por_estado(df_exemplo))
    r = p.filtrar_setembro_sp_rj(d)
    assert set(r["estado_cliente"]) <= {"SP", "RJ"}
    assert (r["valor"] > 5000).all()
    assert (r["mes"] == 9).all()
    assert len(r) == 4  # linhas 0, 1(7500), 2 e 5


def test_map_risco(df_exemplo):
    r = p.adicionar_risco(df_exemplo)
    assert r.loc[0, "nivel_risco"] == "Baixo"
    assert r.loc[1, "nivel_risco"] == "Alto"


def test_pivot_tem_margens(df_exemplo):
    d = p.adicionar_colunas_temporais(p.imputar_valor_mediana_por_estado(df_exemplo))
    pv = p.criar_pivot(p.adicionar_risco(d))
    assert "Total" in pv.index and "Total" in pv.columns
    assert pv.loc["Total", "Total"] == pytest.approx(d["valor"].sum())


def test_zscore_media_zero_por_grupo():
    df = pd.DataFrame({
        "estado_cliente": ["SP"] * 3 + ["RJ"] * 3,
        "valor": [10, 20, 30, 100, 200, 300],
    })
    z = p.zscore_por_grupo(df)
    assert np.allclose(z.groupby(df["estado_cliente"]).mean(), 0)


def test_detectar_anomalias():
    valores = [100.0] * 30 + [10000.0]
    df = pd.DataFrame({"estado_cliente": ["SP"] * 31, "valor": valores})
    r = p.detectar_anomalias(df)
    assert len(r) == 1
    assert r.iloc[0]["valor"] == 10000.0
    assert (r["zscore"] > 2.5).all()


def test_pipeline_completo(tmp_path, monkeypatch):
    """Teste de integração: gera os dados e roda o pipeline inteiro."""
    monkeypatch.chdir(tmp_path)
    import runpy, shutil
    from pathlib import Path
    shutil.copy(Path(__file__).parent / "criar_dados.py", tmp_path)
    runpy.run_path("criar_dados.py")

    res = p.main("transacoes.csv", "saida")
    df = res["df"]
    assert df["valor"].isna().sum() == 0
    assert (df["plataforma"] == "Mobile").all()
    assert len(df) == 1000  # 15 duplicatas removidas
    assert (tmp_path / "saida" / "grafico_transacoes.png").exists()
    assert (res["anomalias"]["zscore"] > 2.5).all()
