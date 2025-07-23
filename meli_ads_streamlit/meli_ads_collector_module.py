
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MercadoLivreAdsCollector:
    """Coletor de dados de anúncios do Mercado Livre."""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.mercadolibre.com"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })
    
    def get_advertisers(self, product_id="PADS"):
        """Obtém a lista de anunciantes para um determinado tipo de produto."""
        try:
            headers = {"Api-Version": "1"}
            url = f"{self.base_url}/advertising/advertisers"
            params = {"product_id": product_id}
            
            response = self.session.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Encontrados {len(data.get('advertisers', []))} anunciantes")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter anunciantes: {e}")
            return None
    
    def get_campaigns_metrics(self, advertiser_id, date_from, date_to, 
                            metrics=None, limit=50, offset=0, filters=None):
        """Obtém as campanhas de um anunciante com suas métricas."""
        try:
            headers = {"Api-Version": "2"}
            url = f"{self.base_url}/advertising/advertisers/{advertiser_id}/product_ads/campaigns"
            
            params = {
                "limit": limit,
                "offset": offset,
                "date_from": date_from,
                "date_to": date_to
            }
            
            if metrics:
                params["metrics"] = ",".join(metrics)
            
            if filters:
                for key, value in filters.items():
                    params[f"filters[{key}]"] = value
            
            response = self.session.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Métricas obtidas para anunciante {advertiser_id}: {data.get('paging', {}).get('total', 0)} campanhas")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter métricas de campanhas: {e}")
            return None
    
    def get_all_campaigns_paginated(self, advertiser_id, date_from, date_to, 
                                  metrics=None, filters=None, max_pages=None):
        """Obtém todas as campanhas usando paginação."""
        all_campaigns = []
        offset = 0
        limit = 50
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            logger.info(f"Coletando página {page}...")
            data = self.get_campaigns_metrics(
                advertiser_id, date_from, date_to, 
                metrics=metrics, limit=limit, offset=offset, filters=filters
            )
            
            if not data or not data.get('results'):
                break
            
            all_campaigns.extend(data['results'])
            
            paging = data.get('paging', {})
            total = paging.get('total', 0)
            
            if offset + limit >= total:
                break
            
            offset += limit
            page += 1
            
            time.sleep(0.5)
        
        logger.info(f"Total de campanhas coletadas: {len(all_campaigns)}")
        return all_campaigns
    
    def campaigns_to_dataframe(self, campaigns_data):
        """Converte dados de campanhas para DataFrame do pandas."""
        if not campaigns_data:
            return pd.DataFrame()
        
        campaigns_list = []
        
        for campaign in campaigns_data:
            campaign_info = {
                'campaign_id': campaign.get('id'),
                'name': campaign.get('name'),
                'status': campaign.get('status'),
                'budget': campaign.get('budget'),
                'currency_id': campaign.get('currency_id'),
                'date_created': campaign.get('date_created'),
                'last_updated': campaign.get('last_updated'),
                'acos_target': campaign.get('acos_target'),
                'strategy': campaign.get('strategy'),
                'channel': campaign.get('channel')
            }
            
            metrics = campaign.get('metrics', {})
            for metric_name, metric_value in metrics.items():
                campaign_info[f'metric_{metric_name}'] = metric_value
            
            campaigns_list.append(campaign_info)
        
        df = pd.DataFrame(campaigns_list)
        logger.info(f"DataFrame criado com {len(df)} campanhas e {len(df.columns)} colunas")
        return df

def run_collector(access_token, advertiser_id):
    """Executa o coletor de dados para um anunciante específico."""
    collector = MercadoLivreAdsCollector(access_token)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    date_from = start_date.strftime('%Y-%m-%d')
    date_to = end_date.strftime('%Y-%m-%d')
    
    metrics = [
        "clicks", "prints", "ctr", "cost", "cpc", "acos",
        "organic_units_quantity", "direct_items_quantity",
        "indirect_items_quantity", "units_quantity",
        "direct_amount", "indirect_amount", "total_amount"
    ]
    
    campaigns = collector.get_all_campaigns_paginated(
        advertiser_id, date_from, date_to, 
        metrics=metrics, max_pages=5
    )
    
    if not campaigns:
        return pd.DataFrame()
    
    df_campaigns = collector.campaigns_to_dataframe(campaigns)
    return df_campaigns


