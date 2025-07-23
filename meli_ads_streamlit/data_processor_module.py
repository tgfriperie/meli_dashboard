import pandas as pd
from datetime import datetime
import os

def process_and_export(campaigns_df, client_name):
    """Processa os dados das campanhas e gera a planilha final."""
    
    # Analisar e recomendar estratégias
    from strategy_analyzer_module import analyze_and_recommend, consolidate_data
    
    campaigns_with_recommendations = analyze_and_recommend(campaigns_df)
    
    # Consolidar dados
    consolidated_df = consolidate_data(campaigns_with_recommendations)
    
    # Gerar nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{client_name}_analise_campanhas_{timestamp}.xlsx"
    
    # Salvar arquivo Excel
    consolidated_df.to_excel(filename, index=False)
    
    return filename, consolidated_df

def generate_summary_report(consolidated_df, client_name):
    """Gera um relatório resumo da análise."""
    
    total_campaigns = len(consolidated_df)
    strategies_count = consolidated_df["Estrategia_Recomendada"].value_counts()
    
    summary = {
        "cliente": client_name,
        "total_campanhas": total_campaigns,
        "estrategias_recomendadas": strategies_count.to_dict(),
        "acos_medio": consolidated_df["metric_acos"].mean() if "metric_acos" in consolidated_df.columns else 0,
        "orcamento_total": consolidated_df["budget"].sum() if "budget" in consolidated_df.columns else 0
    }
    
    return summary

def get_client_data(access_token):
    """Obtém dados básicos do cliente através da API."""
    
    from meli_ads_collector_module import MercadoLivreAdsCollector
    
    collector = MercadoLivreAdsCollector(access_token)
    advertisers_data = collector.get_advertisers()
    
    if not advertisers_data or not advertisers_data.get("advertisers"):
        return None, None
    
    first_advertiser = advertisers_data["advertisers"][0]
    advertiser_id = first_advertiser["advertiser_id"]
    advertiser_name = first_advertiser["advertiser_name"]
    
    return advertiser_id, advertiser_name