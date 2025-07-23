
import pandas as pd
import os

# Dados da tabela_extraida.xlsx hardcoded
hardcoded_strategy_model_data = [{"Nome": "01A - Hig Perforrmance Stage1", "Orçamento": 8, "ACOS Objetivo": 4500, "ACOS": 8, "Tipo de Impressão": "Baixa Impressão", "% de impressões ganhas": 10, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 80, "Cliques": 1, "(Investimento / Receitas)": "10 á abaixo", "Unidades vendidas por publicidade": 10, "Quantidade": 1}, {"Nome": "01B - High Performance Stage2", "Orçamento": 8, "ACOS Objetivo": 1800, "ACOS": 7, "Tipo de Impressão": "Media Impressão", "% de impressões ganhas": 25, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 75, "Cliques": 1, "(Investimento / Receitas)": "10 á abaixo", "Unidades vendidas por publicidade": 10, "Quantidade": 5}, {"Nome": "01C - High Performance Stage3", "Orçamento": 8, "ACOS Objetivo": 2200, "ACOS": 8, "Tipo de Impressão": "Impressões elevadas", "% de impressões ganhas": 50, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 50, "Cliques": 0, "(Investimento / Receitas)": "10 á abaixo", "Unidades vendidas por publicidade": 10, "Quantidade": 0}, {"Nome": "Aceleração dinamica 20/8", "Orçamento": 10, "ACOS Objetivo": 20000, "ACOS": 8, "Tipo de Impressão": "Media Impressão", "% de impressões ganhas": 25, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 75, "Cliques": 50, "(Investimento / Receitas)": "10 á abaixo", "Unidades vendidas por publicidade": 10, "Quantidade": 100}, {"Nome": "Aceleração dinamica 850/22", "Orçamento": 1, "ACOS Objetivo": 850, "ACOS": 22, "Tipo de Impressão": "Media Impressão", "% de impressões ganhas": 15, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 85, "Cliques": 100, "(Investimento / Receitas)": "10 á abaixo", "Unidades vendidas por publicidade": 10, "Quantidade": 50}, {"Nome": "Aceleração dinamica 20/20", "Orçamento": 10, "ACOS Objetivo": 20000, "ACOS": 20, "Tipo de Impressão": "Baixa Impressão", "% de impressões ganhas": 50, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 50, "Cliques": 10, "(Investimento / Receitas)": "10 acima", "Unidades vendidas por publicidade": 20, "Quantidade": 1}, {"Nome": "Aceleração dinamica 10/08", "Orçamento": 10, "ACOS Objetivo": 10000, "ACOS": 8, "Tipo de Impressão": "Impressões elevadas", "% de impressões ganhas": 75, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 25, "Cliques": 100, "(Investimento / Receitas)": "10 á abaixo", "Unidades vendidas por publicidade": 10, "Quantidade": 0}, {"Nome": "Alavanca Full", "Orçamento": 5, "ACOS Objetivo": 1000, "ACOS": 45, "Tipo de Impressão": "Impressões elevadas", "% de impressões ganhas": 50, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 50, "Cliques": 100, "(Investimento / Receitas)": "10 acima", "Unidades vendidas por publicidade": 20, "Quantidade": 0}, {"Nome": "Anuncio Novo Stage1", "Orçamento": 1, "ACOS Objetivo": 5000, "ACOS": 8, "Tipo de Impressão": "Baixa Impressão", "% de impressões ganhas": 15, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 85, "Cliques": 500, "(Investimento / Receitas)": "10 á abaixo", "Unidades vendidas por publicidade": 10, "Quantidade": 50}, {"Nome": "Anuncio Novo Stage2", "Orçamento": 5, "ACOS Objetivo": 15000, "ACOS": 3, "Tipo de Impressão": "Media Impressão", "% de impressões ganhas": 50, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 50, "Cliques": 500, "(Investimento / Receitas)": "10 á abaixo", "Unidades vendidas por publicidade": 10, "Quantidade": 100}, {"Nome": "Anuncio Novo Stage3", "Orçamento": 8, "ACOS Objetivo": 10000, "ACOS": 8, "Tipo de Impressão": "Impressões elevadas", "% de impressões ganhas": 75, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 25, "Cliques": 1000, "(Investimento / Receitas)": "10 á abaixo", "Unidades vendidas por publicidade": 10, "Quantidade": 500}, {"Nome": "Acos Elevado", "Orçamento": 1, "ACOS Objetivo": 50, "ACOS": 6, "Tipo de Impressão": "Baixa Impressão", "% de impressões ganhas": 50, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 50, "Cliques": 1000, "(Investimento / Receitas)": "10 acima", "Unidades vendidas por publicidade": 20, "Quantidade": 500}, {"Nome": "Recorrencia de vendas", "Orçamento": 1, "ACOS Objetivo": 15, "ACOS": 5, "Tipo de Impressão": "Impressões elevadas", "% de impressões ganhas": 65, "% de impressões perdidas por orçamento": 0, "% de impressões perdidas por classificação": 35, "Cliques": 1000, "(Investimento / Receitas)": "10 á abaixo", "Unidades vendidas por publicidade": 10, "Quantidade": 1000}]

def find_best_strategy(campaign, strategy_model):
    best_match_strategy = "Nenhuma estratégia recomendada"
    min_diff = float("inf")

    impression_mapping = {
        "Baixa Impressão": ["Baixa Impressão"],
        "Media Impressão": ["Media Impressão"],
        "Impressões elevadas": ["Impressões elevadas"]
    }

    for index, strategy in strategy_model.iterrows():
        acos_diff = abs(campaign["metric_acos"] - strategy["Estrategia_ACOS"])

        campaign_impression_type = str(campaign.get("Tipo de Impressão", "")).strip()
        strategy_impression_type = str(strategy.get("Estrategia_Tipo_Impressao", "")).strip()

        impression_match = False
        for key, values in impression_mapping.items():
            if strategy_impression_type == key and campaign_impression_type in values:
                impression_match = True
                break

        clicks_match = False
        if pd.notna(campaign["metric_clicks"]) and pd.notna(strategy["Estrategia_Cliques"]):
            if strategy["Estrategia_Cliques"] == 0:
                if campaign["metric_clicks"] < 5:
                    clicks_match = True
            elif abs(campaign["metric_clicks"] - strategy["Estrategia_Cliques"]) <= 10:
                clicks_match = True
        else:
            clicks_match = False

        current_diff = acos_diff
        if not impression_match:
            current_diff += 100
        if not clicks_match:
            current_diff += 50

        if current_diff < min_diff:
            min_diff = current_diff
            best_match_strategy = strategy["Estrategia_Nome"]

    return best_match_strategy

def analyze_and_recommend(campaigns_df):
    strategy_model_df = pd.DataFrame(hardcoded_strategy_model_data)

    strategy_model_df = strategy_model_df.rename(columns={
        "Nome": "Estrategia_Nome",
        "Orçamento": "Estrategia_Orcamento",
        "ACOS Objetivo": "Estrategia_ACOS_Objetivo",
        "ACOS": "Estrategia_ACOS",
        "Tipo de Impressão": "Estrategia_Tipo_Impressao",
        "% de impressões ganhas": "Estrategia_Impressoes_Ganhas",
        "% de impressões perdidas por orçamento": "Estrategia_Impressoes_Perdidas_Orcamento",
        "% de impressões perdidas por classificação": "Estrategia_Impressoes_Perdidas_Classificacao",
        "Cliques": "Estrategia_Cliques",
        "(Investimento / Receitas)": "Estrategia_Investimento_Receitas",
        "Unidades vendidas por publicidade": "Estrategia_Unidades_Vendidas",
        "Quantidade": "Estrategia_Quantidade"
    })

    campaigns_df["Estrategia_Recomendada"] = campaigns_df.apply(
        lambda row: find_best_strategy(row, strategy_model_df), axis=1
    )

    return campaigns_df

def consolidate_data(campaigns_df):
    strategy_model_original_df = pd.DataFrame(hardcoded_strategy_model_data)

    column_mapping = {
        "name": "Nome",
        "budget": "Orçamento",
        "acos_target": "ACOS Objetivo",
        "metric_acos": "ACOS",
        "metric_clicks": "Cliques",
        "metric_units_quantity": "Unidades vendidas por publicidade",
    }

    for campaign_col, model_col in column_mapping.items():
        if model_col not in campaigns_df.columns:
            campaigns_df[model_col] = campaigns_df[campaign_col]
        else:
            campaigns_df[model_col] = campaigns_df[campaign_col]

    if "Tipo de Impressão" not in campaigns_df.columns:
        campaigns_df["Tipo de Impressão"] = ""

    if "% de impressões ganhas" not in campaigns_df.columns:
        campaigns_df["% de impressões ganhas"] = campaigns_df["metric_prints"]

    campaigns_df["(Investimento / Receitas)"] = campaigns_df.apply(
        lambda row: row["metric_total_amount"] / row["metric_cost"] if row["metric_cost"] != 0 else pd.NA,
        axis=1
    )

    model_columns_order = strategy_model_original_df.columns.tolist()

    for col in model_columns_order:
        if col not in campaigns_df.columns:
            campaigns_df[col] = pd.NA

    campaign_original_cols_not_mapped = [
        col for col in campaigns_df.columns 
        if col not in column_mapping.keys() and col != "name"
    ]

    final_columns = ["name"] + model_columns_order + campaign_original_cols_not_mapped + ["Estrategia_Recomendada"]

    final_columns_unique = []
    seen = set()
    for col in final_columns:
        if col not in seen:
            final_columns_unique.append(col)
            seen.add(col)

    campaigns_df = campaigns_df[final_columns_unique]

    return campaigns_df


