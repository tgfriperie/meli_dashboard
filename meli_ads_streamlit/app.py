import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Importar módulos personalizados
from meli_ads_collector_module import run_collector
from data_processor_module import process_and_export, get_client_data, get_business_metrics, get_ads_overview_metrics
from strategy_analyzer_module import hardcoded_strategy_model_data

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Performance - Mercado Livre",
    page_icon="bar_chart",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Funções de Renderização de Páginas (Abas) ---
def render_overview_page(access_token, advertiser_id, date_range):
    """Renderiza a página de Visão Geral com métricas gerais e de publicidade."""
    st.header("Visão Geral de Performance")

    if len(date_range) != 2:
        st.warning("Por favor, selecione um intervalo de datas válido na barra lateral.")
        return

    start_date, end_date = date_range
    st.write(f"Período selecionado: **{start_date.strftime('%d/%m/%Y')}** a **{end_date.strftime('%d/%m/%Y')}**")

    # --- Métricas Gerais da Conta ---
    st.subheader("Métricas Gerais da Conta")
    with st.spinner("Buscando métricas gerais..."):
        business_metrics = get_business_metrics(access_token, start_date, end_date)
    
    if business_metrics:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Faturamento (Vendas Brutas)", f"R$ {business_metrics.get('vendas_brutas', 0):,.2f}")
        col2.metric("Quantidade de Vendas", f"{business_metrics.get('total_de_vendas', 0):,}")
        col3.metric("Unidades Vendidas", f"{business_metrics.get('unidades_vendidas', 0):,}")
        col4.metric("Ticket Médio", f"R$ {business_metrics.get('ticket_medio', 0):,.2f}")
    else:
        st.error("Não foi possível carregar as métricas gerais da conta.")

    st.divider()

    # --- Métricas de Publicidade ---
    st.subheader("Métricas de Publicidade")
    with st.spinner("Buscando métricas de publicidade..."):
        ads_metrics = get_ads_overview_metrics(access_token, advertiser_id, start_date, end_date)

    if ads_metrics:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Investimento", f"R$ {ads_metrics.get('cost', 0):,.2f}")
        col2.metric("Receita", f"R$ {ads_metrics.get('total_amount', 0):,.2f}")
        col3.metric("Impressões", f"{ads_metrics.get('prints', 0):,}")
        col4.metric("Cliques", f"{ads_metrics.get('clicks', 0):,}")
        
        acos_value = ads_metrics.get('acos')
        acos_display = f"{acos_value * 100:.2f}%" if acos_value is not None else "0.00%"
        col5.metric("ACOS", acos_display)
    else:
        st.error("Não foi possível carregar as métricas de publicidade.")

def render_ads_page(access_token, advertiser_id):
    """Renderiza a página de Análise de Campanhas (antiga funcionalidade)."""
    st.header("Análise Detalhada de Campanhas de Ads")

    status_filter = st.radio(
        "Filtrar por Status da Campanha:",
        ("Todas", "Ativas", "Inativas"),
        horizontal=True,
        key="status_filter_campaigns"
    )

    if st.button("Executar Análise de Campanhas", type="primary"):
        with st.spinner("Analisando campanhas..."):
            try:
                campaigns_df = run_collector(access_token, advertiser_id)
                if campaigns_df.empty:
                    st.error("Nenhuma campanha encontrada para este anunciante.")
                else:
                    filename, consolidated_df = process_and_export(campaigns_df, st.session_state.client_name)
                    st.session_state.last_analysis = {"consolidated_df": consolidated_df, "filename": filename}
                    st.success("Análise de campanhas concluída!")
            except Exception as e:
                st.error(f"Erro durante a análise de campanhas: {str(e)}")
    
    if "last_analysis" in st.session_state:
        full_df = st.session_state.last_analysis["consolidated_df"]
        
        if status_filter == "Ativas": display_df = full_df[full_df['status'] == 'active'].copy()
        elif status_filter == "Inativas": display_df = full_df[full_df['status'] != 'active'].copy()
        else: display_df = full_df.copy()

        st.markdown(f"#### Exibindo {len(display_df)} de {len(full_df)} campanhas.")
        
        if display_df.empty:
            st.info(f"Nenhuma campanha encontrada com o status '{status_filter}'.")
        else:
            strategy_df = pd.DataFrame(hardcoded_strategy_model_data)
            for _, campaign in display_df.iterrows():
                create_campaign_card(campaign, strategy_df)

def create_campaign_card(campaign_data, strategy_data):
    """Cria um card visual para uma campanha."""
    campaign_name = campaign_data.get("name", "Campanha sem nome")
    strategy_name = campaign_data.get("Estrategia_Recomendada", "Nenhuma estratégia")
    current_acos = campaign_data.get("ACOS", 0)
    if pd.isna(current_acos): current_acos = 0
    current_budget = campaign_data.get("Orçamento", 0)
    if pd.isna(current_budget): current_budget = 0
    
    strategy_acos = 0
    strategy_budget = 0
    if strategy_data is not None and not strategy_data.empty:
        strategy_row = strategy_data[strategy_data["Nome"] == strategy_name]
        if not strategy_row.empty:
            strategy_acos = strategy_row.iloc[0].get("ACOS", 0)
            if pd.isna(strategy_acos): strategy_acos = 0
            strategy_budget = strategy_row.iloc[0].get("Orçamento", 0)
            if pd.isna(strategy_budget): strategy_budget = 0
    
    budget_diff = strategy_budget - current_budget

    with st.container(border=True):
        st.subheader(f"Campanha: {campaign_name}")
        st.markdown(f"**Estratégia Recomendada:** `{strategy_name}`")
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("ACOS Atual", f"{current_acos:.2f}%")
            st.metric("Orçamento Atual", f"R$ {current_budget:,.2f}")
        with col2:
            st.metric("ACOS da Estratégia", f"{strategy_acos:.2f}%")
            st.metric("Orçamento Recomendado", f"R$ {strategy_budget:,.2f}")
        st.divider()
        if budget_diff > 0: st.success(f"Aumentar investimento em R$ {budget_diff:,.2f}")
        elif budget_diff < 0: st.error(f"Diminuir investimento em R$ {abs(budget_diff):,.2f}")
        else: st.info("Manter investimento atual")
    st.write("")

# --- BARRA LATERAL (Sidebar) ---
with st.sidebar:
    st.header("Configurações do Cliente")
    access_token = st.text_input("Access Token do Mercado Livre", type="password")
    client_name = st.text_input("Nome do Cliente", placeholder="Ex: McCoys Pickle Factory")

    if st.button("Validar Token"):
        if access_token and client_name:
            with st.spinner("Validando token..."):
                advertiser_id, advertiser_name = get_client_data(access_token)
                if advertiser_id:
                    st.success("Token válido!")
                    st.session_state.token_valid = True
                    st.session_state.access_token = access_token
                    st.session_state.client_name = client_name
                    st.session_state.advertiser_id = advertiser_id
                    st.session_state.advertiser_name = advertiser_name
                    st.info(f"**Anunciante:** {advertiser_name}")
                else:
                    st.error("Token inválido ou sem anunciantes encontrados.")
                    st.session_state.token_valid = False
        else:
            st.warning("Por favor, preencha todos os campos.")
    
    st.divider()
    st.header("Filtros de Período")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6) # Padrão para 7 dias
    date_range = st.date_input(
        "Selecione o Período", (start_date, end_date),
        min_value=end_date - timedelta(days=365), max_value=end_date,
        format="DD/MM/YYYY"
    )

# --- Conteúdo Principal com Abas ---
st.title("Dashboard de Performance")

if "token_valid" in st.session_state and st.session_state.token_valid:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Visão Geral", "Ads", "Acompanhamento Diário", "Estrela Guia", "Projeção"
    ])

    with tab1:
        render_overview_page(st.session_state.access_token, st.session_state.advertiser_id, date_range)

    with tab2:
        render_ads_page(st.session_state.access_token, st.session_state.advertiser_id)

    with tab3:
        st.header("Acompanhamento Diário")
        st.info("Funcionalidade em desenvolvimento.")

    with tab4:
        st.header("Estrela Guia")
        st.info("Funcionalidade em desenvolvimento.")

    with tab5:
        st.header("Projeção")
        st.info("Funcionalidade em desenvolvimento.")
else:
    st.info("Por favor, insira e valide as credenciais do cliente na barra lateral para começar.")

# Footer
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; color: #666;'>Desenvolvido para análise de campanhas | Versão 2.0</div>",
    unsafe_allow_html=True
)
