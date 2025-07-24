import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Importar módulos personalizados
from meli_ads_collector_module import run_collector
from data_processor_module import process_and_export, get_client_data
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

# Adiciona o filtro de status na barra lateral
st.sidebar.divider()
st.sidebar.header("Filtros de Análise")
status_filter = st.sidebar.radio(
    "Filtrar por Status da Campanha",
    ("Todas", "Ativas", "Inativas"),
    horizontal=True,
    key="status_filter"
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

# Coluna da esquerda para executar a análise
with col1:
    st.header("Análise de Campanhas")
    if access_token and client_name:
        if st.button("Executar Análise Completa", type="primary"):
            if hasattr(st.session_state, "token_valid") and st.session_state.token_valid:
                progress_bar = st.progress(0, text="Iniciando análise...")
                try:
                    progress_bar.progress(25, text="Coletando dados das campanhas...")
                    campaigns_df = run_collector(access_token, st.session_state.advertiser_id)
                    
                    if campaigns_df.empty:
                        st.error("Nenhuma campanha encontrada para este anunciante")
                        progress_bar.empty()
                    else:
                        progress_bar.progress(50, text="Analisando e recomendando estratégias...")
                        filename, consolidated_df = process_and_export(campaigns_df, client_name)
                        
                        progress_bar.progress(100, text="Análise concluída!")
                        st.success("Análise concluída com sucesso!")
                        
                        with open(filename, "rb") as file:
                            st.download_button(
                                label="Baixar Planilha de Análise",
                                data=file.read(),
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        st.session_state.last_analysis = {
                            "consolidated_df": consolidated_df,
                            "filename": filename
                        }
                        progress_bar.empty()
                except Exception as e:
                    st.error(f"Erro durante a análise: {str(e)}")
                    if 'progress_bar' in locals():
                        progress_bar.empty()
            else:
                st.warning("Por favor, valide o token primeiro")
    else:
        st.info("Preencha o Access Token e o Nome do Cliente na barra lateral para começar")

# Lógica de exibição dos resultados (Resumo e Cards)
if hasattr(st.session_state, "last_analysis"):
    full_df = st.session_state.last_analysis["consolidated_df"]

    # Aplica o filtro para criar o dataframe de exibição
    if status_filter == "Ativas":
        display_df = full_df[full_df['status'] == 'active'].copy()
    elif status_filter == "Inativas":
        display_df = full_df[full_df['status'] != 'active'].copy()
    else:
        display_df = full_df.copy()

    # Coluna da direita para o resumo
    with col2:
        st.header("Resumo da Análise")
        
        # Recalcula as métricas com base no dataframe filtrado
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
                st.write(f"• **{strategy}**: {count} campanha(s)")
        else:
            st.write("Nenhuma estratégia para a seleção atual.")

    # Seção de detalhes das campanhas (abaixo das colunas)
    st.markdown("---")
    st.header(f"Detalhes das Campanhas ({status_filter})")
    
    strategy_df = pd.DataFrame(hardcoded_strategy_model_data)
    
    if display_df.empty:
        st.info(f"Nenhuma campanha encontrada com o status '{status_filter}'.")
    else:
        for index, campaign in display_df.iterrows():
            create_campaign_card(campaign, strategy_df)

else:
    # Estado inicial antes da primeira análise
    with col2:
        st.header("Resumo da Análise")
        st.info("Execute uma análise para ver o resumo aqui")

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
        <p>Desenvolvido para análise de campanhas do Mercado Livre | Versão 1.3</p>
    </div>
    """,
    unsafe_allow_html=True
)
