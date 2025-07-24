import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Importar módulos personalizados
from meli_ads_collector_module import run_collector
from data_processor_module import process_and_export, get_client_data, get_business_metrics
from strategy_analyzer_module import hardcoded_strategy_model_data

# Configuração da página
st.set_page_config(
    page_title="Analisador de Campanhas - Mercado Livre",
    page_icon="bar_chart",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("Analisador de Campanhas do Mercado Livre")
st.markdown("---")

# --- BARRA LATERAL ---
st.sidebar.header("Configurações do Cliente")

access_token = st.sidebar.text_input(
    "Access Token do Mercado Livre",
    type="password",
    help="Token de acesso para a API do Mercado Livre"
)

client_name = st.sidebar.text_input(
    "Nome do Cliente",
    placeholder="Ex: McCoys Pickle Factory",
    help="Nome identificador do cliente"
)

if st.sidebar.button("Validar Token"):
    if access_token:
        with st.spinner("Validando token..."):
            advertiser_id, advertiser_name = get_client_data(access_token)
            if advertiser_id:
                st.sidebar.success("Token válido!")
                st.sidebar.info(f"**Anunciante:** {advertiser_name}")
                st.sidebar.info(f"**ID:** {advertiser_id}")
                st.session_state.advertiser_id = advertiser_id
                st.session_state.advertiser_name = advertiser_name
                st.session_state.token_valid = True
            else:
                st.sidebar.error("Token inválido ou sem anunciantes encontrados")
                st.session_state.token_valid = False
    else:
        st.sidebar.warning("Por favor, insira o Access Token")

# Filtros de Análise de Campanhas
st.sidebar.divider()
st.sidebar.header("Filtros de Análise de Campanhas")
status_filter = st.sidebar.radio(
    "Filtrar por Status da Campanha",
    ("Todas", "Ativas", "Inativas"),
    horizontal=True,
    key="status_filter"
)

# Filtros de Métricas Gerais
st.sidebar.divider()
st.sidebar.header("Filtros de Métricas Gerais")
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

date_range = st.sidebar.date_input(
    "Selecione o Período",
    (start_date, end_date),
    min_value=end_date - timedelta(days=365),
    max_value=end_date,
    format="DD/MM/YYYY"
)
# --- FIM DA BARRA LATERAL ---

# Função para criar cards de campanha
def create_campaign_card(campaign_data, strategy_data):
    """Cria um card visual para uma campanha usando componentes nativos do Streamlit."""
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
            st.metric(label="ACOS Atual", value=f"{current_acos:.2f}%")
            st.metric(label="Orçamento Atual", value=f"R$ {current_budget:,.2f}")
        with col2:
            st.metric(label="ACOS da Estratégia", value=f"{strategy_acos:.2f}%")
            st.metric(label="Orçamento Recomendado", value=f"R$ {strategy_budget:,.2f}")
        st.divider()
        if budget_diff > 0:
            st.success(f"Aumentar investimento em R$ {budget_diff:,.2f}")
        elif budget_diff < 0:
            st.error(f"Diminuir investimento em R$ {abs(budget_diff):,.2f}")
        else:
            st.info("Manter investimento atual")
    st.write("")

# --- ÁREA PRINCIPAL ---
col1, col2 = st.columns([2, 1])

# Coluna da esquerda para executar a análise de campanhas
with col1:
    st.header("Análise de Campanhas de Ads")
    if access_token and client_name:
        if st.button("Executar Análise de Campanhas", type="primary"):
            if hasattr(st.session_state, "token_valid") and st.session_state.token_valid:
                with st.spinner("Analisando campanhas..."):
                    try:
                        campaigns_df = run_collector(access_token, st.session_state.advertiser_id)
                        if campaigns_df.empty:
                            st.error("Nenhuma campanha encontrada para este anunciante")
                        else:
                            filename, consolidated_df = process_and_export(campaigns_df, client_name)
                            st.session_state.last_analysis = {
                                "consolidated_df": consolidated_df,
                                "filename": filename
                            }
                            st.success("Análise de campanhas concluída!")
                            with open(filename, "rb") as file:
                                st.download_button(
                                    label="Baixar Planilha de Campanhas",
                                    data=file.read(),
                                    file_name=filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                    except Exception as e:
                        st.error(f"Erro durante a análise de campanhas: {str(e)}")
            else:
                st.warning("Por favor, valide o token primeiro")
    else:
        st.info("Preencha o Access Token e o Nome do Cliente na barra lateral para começar")

# Coluna da direita para o resumo da análise de campanhas
with col2:
    st.header("Resumo da Análise de Campanhas")
    if hasattr(st.session_state, "last_analysis"):
        full_df = st.session_state.last_analysis["consolidated_df"]
        if status_filter == "Ativas":
            display_df = full_df[full_df['status'] == 'active'].copy()
        elif status_filter == "Inativas":
            display_df = full_df[full_df['status'] != 'active'].copy()
        else:
            display_df = full_df.copy()

        total_campaigns_display = len(display_df)
        acos_medio_display = display_df['ACOS'].dropna().mean() if not display_df.empty else 0
        orcamento_total_display = display_df['Orçamento'].dropna().sum() if not display_df.empty else 0
        estrategias_recomendadas_display = display_df["Estrategia_Recomendada"].value_counts().to_dict()

        st.metric(f"Total de Campanhas ({status_filter})", total_campaigns_display)
        st.metric(f"ACOS Médio ({status_filter})", f"{acos_medio_display:.2f}%")
        st.metric(f"Orçamento Total ({status_filter})", f"R$ {orcamento_total_display:,.2f}")
        
        st.subheader(f"Estratégias ({status_filter})")
        if estrategias_recomendadas_display:
            for strategy, count in estrategias_recomendadas_display.items():
                # CORREÇÃO: Substituído '•' por '-'
                st.write(f"- **{strategy}**: {count} campanha(s)")
        else:
            st.write("Nenhuma estratégia para a seleção atual.")
    else:
        st.info("Execute uma análise de campanhas para ver o resumo.")

# Seção de detalhes das campanhas (abaixo das colunas)
if hasattr(st.session_state, "last_analysis"):
    st.markdown("---")
    st.header(f"Detalhes das Campanhas ({status_filter})")
    strategy_df = pd.DataFrame(hardcoded_strategy_model_data)
    if display_df.empty:
        st.info(f"Nenhuma campanha encontrada com o status '{status_filter}'.")
    else:
        for index, campaign in display_df.iterrows():
            create_campaign_card(campaign, strategy_df)

# --- NOVA SEÇÃO DE MÉTRICAS GERAIS ---
st.markdown("---")
st.header("Métricas Gerais da Conta")

if len(date_range) == 2:
    start_date_filter, end_date_filter = date_range
    st.write(f"Período selecionado: **{start_date_filter.strftime('%d/%m/%Y')}** a **{end_date_filter.strftime('%d/%m/%Y')}**")

    if st.button("Buscar Métricas Gerais"):
        if hasattr(st.session_state, "token_valid") and st.session_state.token_valid:
            with st.spinner("Buscando métricas de vendas..."):
                metrics = get_business_metrics(access_token, start_date_filter, end_date_filter)
                st.session_state.business_metrics = metrics
        else:
            st.warning("Por favor, valide o token primeiro.")
else:
    st.warning("Por favor, selecione um intervalo de datas válido.")

if "business_metrics" in st.session_state and st.session_state.business_metrics:
    metrics = st.session_state.business_metrics
    
    st.write("##### Resumo de Desempenho")
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Vendas Brutas", f"R$ {metrics.get('vendas_brutas', 0):,.2f}")
    m_col2.metric("Unidades Vendidas", f"{metrics.get('unidades_vendidas', 0):,}")
    m_col3.metric("Preço Médio por Unidade", f"R$ {metrics.get('preco_medio_por_unidade', 0):,.2f}")

    m_col4, m_col5, m_col6 = st.columns(3)
    m_col4.metric("Quantidade de Vendas", f"{metrics.get('total_de_vendas', 0):,}")
    m_col5.metric("Preço Médio por Venda (Ticket)", f"R$ {metrics.get('ticket_medio', 0):,.2f}")
    m_col6.metric("Visitas", "N/A", help="Métrica indisponível via API de pedidos.")

    st.write("##### Vendas Canceladas")
    m_col7, m_col8 = st.columns(2)
    m_col7.metric("Quantidade de Vendas Canceladas", f"{metrics.get('qtd_vendas_canceladas', 0):,}")
    m_col8.metric("Valor de Vendas Canceladas", f"R$ {metrics.get('valor_vendas_canceladas', 0):,.2f}")


# Seção de histórico (sempre visível)
st.markdown("---")
st.header("Histórico de Análises")
if os.path.exists("."):
    try:
        analysis_files = [f for f in os.listdir(".") if "_analise_campanhas_" in f and f.endswith(".xlsx")]
        if analysis_files:
            st.write("Análises anteriores disponíveis:")
            for file in sorted(analysis_files, reverse=True)[:5]:
                col1_hist, col2_hist = st.columns([3, 1])
                with col1_hist:
                    st.write(f"{file}")
                with col2_hist:
                    with open(file, "rb") as f:
                        st.download_button(
                            label="Baixar",
                            data=f.read(),
                            file_name=file,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=file
                        )
        else:
            st.info("Nenhuma análise anterior encontrada.")
    except Exception as e:
        st.warning(f"Não foi possível listar o histórico de arquivos: {e}")
else:
    st.info("Diretório de trabalho não encontrado para listar o histórico.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Desenvolvido para análise de campanhas do Mercado Livre | Versão 1.5</p>
    </div>
    """,
    unsafe_allow_html=True
)
