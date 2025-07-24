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
    """Coletor de dados de anúncios e métricas do Mercado Livre."""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.mercadolibre.com"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })

    def get_user_id(self):
        """Obtém o ID do usuário logado."""
        try:
            url = f"{self.base_url}/users/me"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"ID de usuário obtido: {data.get('id')}")
            return data.get('id')
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter ID do usuário: {e}")
            return None

    def get_orders_metrics(self, seller_id, date_from, date_to):
        """Busca pedidos em um intervalo de datas e calcula as métricas de negócio."""
        all_orders = []
        offset = 0
        limit = 50
        
        date_from_str = f"{date_from}T00:00:00.000-03:00"
        date_to_str = f"{date_to}T23:59:59.999-03:00"

        while True:
            logger.info(f"Buscando pedidos... offset: {offset}")
            url = f"{self.base_url}/orders/search"
            params = {
                "seller": seller_id,
                "order.date_created.from": date_from_str,
                "order.date_created.to": date_to_str,
                "limit": limit,
                "offset": offset,
                "sort": "date_desc"
            }
            
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                if not results:
                    break
                
                all_orders.extend(results)
                
                paging = data.get('paging', {})
                total = paging.get('total', 0)
                
                if offset + limit >= total or len(all_orders) >= total:
                    break
                
                offset += limit
                time.sleep(0.2)

            except requests.exceptions.RequestException as e:
                logger.error(f"Erro ao buscar pedidos: {e}")
                break
        
        logger.info(f"Total de {len(all_orders)} pedidos encontrados.")

        # Calcular métricas a partir dos pedidos
        if not all_orders:
            return {
                "vendas_brutas": 0, "unidades_vendidas": 0, "total_de_vendas": 0, "ticket_medio": 0,
                "preco_medio_por_unidade": 0, "qtd_vendas_canceladas": 0, "valor_vendas_canceladas": 0
            }

        # Filtra pedidos para cálculos corretos
        valid_orders = [
            order for order in all_orders if order.get('status') in ['paid', 'shipped', 'delivered']
        ]
        cancelled_orders = [
            order for order in all_orders if order.get('status') == 'cancelled'
        ]

        # Calcula métricas de vendas com base nos pedidos válidos
        vendas_brutas = sum(order['total_amount'] for order in valid_orders if 'total_amount' in order)
        unidades_vendidas = sum(item['quantity'] for order in valid_orders for item in order.get('order_items', []))
        total_de_vendas = len(valid_orders)
        ticket_medio = vendas_brutas / total_de_vendas if total_de_vendas > 0 else 0
        preco_medio_por_unidade = vendas_brutas / unidades_vendidas if unidades_vendidas > 0 else 0
        
        # Calcula métricas de cancelamento
        qtd_vendas_canceladas = len(cancelled_orders)
        valor_vendas_canceladas = sum(order['total_amount'] for order in cancelled_orders if 'total_amount' in order)

        metrics = {
            "vendas_brutas": vendas_brutas,
            "unidades_vendidas": unidades_vendidas,
            "total_de_vendas": total_de_vendas,
            "ticket_medio": ticket_medio,
            "preco_medio_por_unidade": preco_medio_por_unidade,
            "qtd_vendas_canceladas": qtd_vendas_canceladas,
            "valor_vendas_canceladas": valor_vendas_canceladas
        }
        logger.info(f"Métricas de negócio calculadas: {metrics}")
        return metrics

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
                
            logger.info(f"Coletando página de campanhas {page}...")
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
        logger.info(f"DataFrame de campanhas criado com {len(df)} linhas")
        return df

def run_collector(access_token, advertiser_id):
    """Executa o coletor de dados de campanhas para um anunciante específico."""
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
