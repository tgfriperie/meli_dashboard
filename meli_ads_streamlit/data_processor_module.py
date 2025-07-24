import pandas as pd
from datetime import datetime
import os

# Importar o coletor
from meli_ads_collector_module import MercadoLivreAdsCollector
from strategy_analyzer_module import analyze_and_recommend, consolidate_data

def process_and_export(campaigns_df, client_name):
    """Processa os dados das campanhas e gera a planilha final."""
    campaigns_with_recommendations = analyze_and_recommend(campaigns_df)
    consolidated_df = consolidate_data(campaigns_with_recommendations)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{client_name}_analise_campanhas_{timestamp}.xlsx"
    consolidated_df.to_excel(filename, index=False)
    return filename, consolidated_df

def get_client_data(access_token):
    """Obtém dados básicos do cliente através da API."""
    collector = MercadoLivreAdsCollector(access_token)
    advertisers_data = collector.get_advertisers()
    if not advertisers_data or not advertisers_data.get("advertisers"):
        return None, None
    first_advertiser = advertisers_data["advertisers"][0]
    advertiser_id = first_advertiser["advertiser_id"]
    advertiser_name = first_advertiser["advertiser_name"]
    return advertiser_id, advertiser_name

def get_business_metrics(access_token, date_from, date_to):
    """Obtém as métricas de negócio para um determinado período."""
    if not access_token: return None
    try:
        collector = MercadoLivreAdsCollector(access_token)
        seller_id = collector.get_user_id()
        if not seller_id:
            print("Não foi possível obter o ID do vendedor.")
            return None
        metrics = collector.get_orders_metrics(seller_id, date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d'))
        return metrics
    except Exception as e:
        print(f"Erro ao buscar métricas de negócio: {e}")
        return None

def get_ads_overview_metrics(access_token, advertiser_id, date_from, date_to):
    """Obtém as métricas de publicidade para um determinado período."""
    if not access_token or not advertiser_id: return None
    try:
        collector = MercadoLivreAdsCollector(access_token)
        metrics = collector.get_ads_summary_metrics(advertiser_id, date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d'))
        return metrics
    except Exception as e:
        print(f"Erro ao buscar métricas de publicidade: {e}")
        return None