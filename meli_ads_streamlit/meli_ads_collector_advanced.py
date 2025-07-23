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
    
    def get_ad_details(self, item_id):
        """Obtém os detalhes de um anúncio específico."""
        try:
            headers = {"Api-Version": "2"}
            url = f"{self.base_url}/advertising/product_ads/items/{item_id}"
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Detalhes obtidos para o item {item_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter detalhes do anúncio {item_id}: {e}")
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
            
            # Verificar se há mais páginas
            paging = data.get('paging', {})
            total = paging.get('total', 0)
            
            if offset + limit >= total:
                break
            
            offset += limit
            page += 1
            
            # Pequena pausa para evitar rate limiting
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
            
            # Adicionar métricas se disponíveis
            metrics = campaign.get('metrics', {})
            for metric_name, metric_value in metrics.items():
                campaign_info[f'metric_{metric_name}'] = metric_value
            
            campaigns_list.append(campaign_info)
        
        df = pd.DataFrame(campaigns_list)
        logger.info(f"DataFrame criado com {len(df)} campanhas e {len(df.columns)} colunas")
        return df
    
    def export_to_csv(self, data, filename):
        """Exporta dados para arquivo CSV."""
        try:
            if isinstance(data, pd.DataFrame):
                data.to_csv(filename, index=False, encoding='utf-8')
            else:
                df = pd.DataFrame(data)
                df.to_csv(filename, index=False, encoding='utf-8')
            
            logger.info(f"Dados exportados para {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar para CSV: {e}")
            return False
    
    def export_to_json(self, data, filename):
        """Exporta dados para arquivo JSON."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if isinstance(data, pd.DataFrame):
                    data.to_json(f, orient='records', indent=2, force_ascii=False)
                else:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Dados exportados para {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar para JSON: {e}")
            return False

def main():
    """Função principal de exemplo."""
    # Substitua pelo seu ACCESS_TOKEN real
    ACCESS_TOKEN = "APP_USR-7315198634179578-072211-86ac0e7620022d9cd3924a2adba68ad9-2312240624"
    
    if ACCESS_TOKEN == "YOUR_ACCESS_TOKEN":
        print("ATENÇÃO: Você precisa substituir 'YOUR_ACCESS_TOKEN' pelo seu token de acesso real.")
        print("Para obter um token de acesso:")
        print("1. Acesse https://developers.mercadolivre.com.br/")
        print("2. Crie uma aplicação")
        print("3. Siga o fluxo de autenticação OAuth 2.0")
        print("4. Consulte a documentação oficial para mais detalhes")
        return
    
    # Inicializar o coletor
    collector = MercadoLivreAdsCollector(ACCESS_TOKEN)
    
    try:
        # 1. Obter anunciantes
        print("1. Obtendo lista de anunciantes...")
        advertisers_data = collector.get_advertisers()
        
        if not advertisers_data or not advertisers_data.get('advertisers'):
            print("Nenhum anunciante encontrado ou erro na requisição.")
            return
        
        # Usar o primeiro anunciante como exemplo
        first_advertiser = advertisers_data['advertisers'][0]
        advertiser_id = first_advertiser['advertiser_id']
        print(f"Usando anunciante: {first_advertiser['advertiser_name']} (ID: {advertiser_id})")
        
        # 2. Definir período de análise (últimos 30 dias)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        date_from = start_date.strftime('%Y-%m-%d')
        date_to = end_date.strftime('%Y-%m-%d')
        
        print(f"Período de análise: {date_from} a {date_to}")
        
        # 3. Definir métricas desejadas
        metrics = [
            "clicks", "prints", "ctr", "cost", "cpc", "acos",
            "organic_units_quantity", "direct_items_quantity",
            "indirect_items_quantity", "units_quantity",
            "direct_amount", "indirect_amount", "total_amount"
        ]
        
        # 4. Coletar dados de campanhas
        print("2. Coletando dados de campanhas...")
        campaigns = collector.get_all_campaigns_paginated(
            advertiser_id, date_from, date_to, 
            metrics=metrics, max_pages=5
        )
        
        if not campaigns:
            print("Nenhuma campanha encontrada.")
            return
        
        # 5. Converter para DataFrame
        print("3. Processando dados...")
        df_campaigns = collector.campaigns_to_dataframe(campaigns)
        
        # 6. Exibir resumo
        print(f"\nResumo dos dados coletados:")
        print(f"- Total de campanhas: {len(df_campaigns)}")
        print(f"- Colunas disponíveis: {list(df_campaigns.columns)}")
        
        if not df_campaigns.empty:
            print(f"\nPrimeiras 5 campanhas:")
            print(df_campaigns[['campaign_id', 'name', 'status', 'budget']].head())
        
        # 7. Exportar dados
        print("\n4. Exportando dados...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Exportar para CSV
        csv_filename = f"mercado_livre_campaigns_{timestamp}.csv"
        collector.export_to_csv(df_campaigns, csv_filename)
        
        # Exportar para JSON
        json_filename = f"mercado_livre_campaigns_{timestamp}.json"
        collector.export_to_json(campaigns, json_filename)
        
        print(f"\nDados exportados com sucesso!")
        print(f"- CSV: {csv_filename}")
        print(f"- JSON: {json_filename}")
        
    except Exception as e:
        logger.error(f"Erro na execução principal: {e}")

if __name__ == "__main__":
    main()

