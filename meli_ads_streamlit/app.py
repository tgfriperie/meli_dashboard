import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Importar módulos personalizados
from meli_ads_collector_module import run_collector
from data_processor_module import process_and_export, generate_summary_report, get_client_data

# Configuração da página
st.set_page_config(
    page_title="Analisador de Campanhas - Mercado Livre",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para os cards
st.markdown("""
<style>
.campaign-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    color: white;
    border-left: 5px solid #4CAF50;
}

.campaign-card h3 {
    color: #ffffff;
    margin-bottom: 1rem;
    font-size: 1.2rem;
    font-weight: bold;
}

.strategy-badge {
    background: rgba(255, 255, 255, 0.2);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    display: inline-block;
    margin: 0.5rem 0;
    font-weight: bold;
}

.metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 0.5rem 0;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}

.metric-label {
    font-weight: bold;
    opacity: 0.9;
}

.metric-value {
    font-size: 1.1rem;
    font-weight: bold;
}

.investment-recommendation {
    background: #4CAF50;
    padding: 1rem;
    border-radius: 10px;
    margin-top: 1rem;
    text-align: center;
    font-weight: bold;
    font-size: 1.1rem;
}

.investment-decrease {
    background: #f44336;
}

.investment-maintain {
    background: #ff9800;
}
</style>
""", unsafe_allow_html=True)

# Título principal
st.title("📊 Analisador de Campanhas do Mercado Livre")
st.markdown("---")

# Sidebar para configurações
st.sidebar.header("⚙️ Configurações do Cliente")

# Inputs para dados do cliente
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

# Botão para validar token
if st.sidebar.button("🔍 Validar Token"):
    if access_token:
        with st.spinner("Validando token..."):
            advertiser_id, advertiser_name = get_client_data(access_token)
            
            if advertiser_id:
                st.sidebar.success(f"✅ Token válido!")
                st.sidebar.info(f"**Anunciante:** {advertiser_name}")
                st.sidebar.info(f"**ID:** {advertiser_id}")
                
                # Armazenar dados na sessão
                st.session_state.advertiser_id = advertiser_id
                st.session_state.advertiser_name = advertiser_name
                st.session_state.token_valid = True
            else:
                st.sidebar.error("❌ Token inválido ou sem anunciantes encontrados")
                st.session_state.token_valid = False
    else:
        st.sidebar.warning("⚠️ Por favor, insira o Access Token")

# Função para criar cards de campanha
def create_campaign_card(campaign_data, strategy_data):
    """Cria um card visual para uma campanha com suas recomendações."""
    
    campaign_name = campaign_data.get("name", "Campanha sem nome")
    strategy_name = campaign_data.get("Estrategia_Recomendada", "Nenhuma estratégia")
    
    # Tratar valores nulos/NaN para ACOS e Budget
    # Usar os nomes corretos após a consolidação
    current_acos = campaign_data.get("ACOS", 0)  # Foi renomeado de metric_acos para ACOS
    if pd.isna(current_acos) or current_acos is None:
        current_acos = 0
    
    current_budget = campaign_data.get("Orçamento", 0)  # Foi renomeado de budget para Orçamento
    if pd.isna(current_budget) or current_budget is None:
        current_budget = 0
    
    # Buscar dados da estratégia recomendada
    strategy_acos = 0
    strategy_budget = 0
    
    if strategy_data is not None and not strategy_data.empty:
        strategy_row = strategy_data[strategy_data["Nome"] == strategy_name]
        if not strategy_row.empty:
            strategy_acos = strategy_row.iloc[0].get("ACOS", 0)
            strategy_budget = strategy_row.iloc[0].get("Orçamento", 0)
            
            # Tratar valores nulos da estratégia também
            if pd.isna(strategy_acos) or strategy_acos is None:
                strategy_acos = 0
            if pd.isna(strategy_budget) or strategy_budget is None:
                strategy_budget = 0
    
    # Calcular recomendação de investimento
    budget_diff = strategy_budget - current_budget
    if budget_diff > 0:
        investment_recommendation = f"💰 Aumentar investimento em R$ {budget_diff:.2f}"
        investment_class = "investment-recommendation"
    elif budget_diff < 0:
        investment_recommendation = f"💸 Diminuir investimento em R$ {abs(budget_diff):.2f}"
        investment_class = "investment-recommendation investment-decrease"
    else:
        investment_recommendation = "✅ Manter investimento atual"
        investment_class = "investment-recommendation investment-maintain"
    
    # HTML do card
    card_html = f"""
    <div class="campaign-card">
        <h3>🎯 {campaign_name}</h3>
        
        <div class="strategy-badge">
            📋 Estratégia Recomendada: {strategy_name}
        </div>
        
        <div class="metric-row">
            <span class="metric-label">ACOS Atual:</span>
            <span class="metric-value">{current_acos:.2f}%</span>
        </div>
        
        <div class="metric-row">
            <span class="metric-label">ACOS da Estratégia:</span>
            <span class="metric-value">{strategy_acos:.2f}%</span>
        </div>
        
        <div class="metric-row">
            <span class="metric-label">Orçamento Atual:</span>
            <span class="metric-value">R$ {current_budget:.2f}</span>
        </div>
        
        <div class="metric-row">
            <span class="metric-label">Orçamento Recomendado:</span>
            <span class="metric-value">R$ {strategy_budget:.2f}</span>
        </div>
        
        <div class="{investment_class}">
            {investment_recommendation}
        </div>
    </div>
    """
    
    return card_html

# Área principal
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🚀 Análise de Campanhas")
    
    if access_token and client_name:
        if st.button("▶️ Executar Análise Completa", type="primary"):
            if hasattr(st.session_state, "token_valid") and st.session_state.token_valid:
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Etapa 1: Coleta de dados
                    status_text.text("🔄 Coletando dados das campanhas...")
                    progress_bar.progress(25)
                    
                    campaigns_df = run_collector(access_token, st.session_state.advertiser_id)
                    
                    if campaigns_df.empty:
                        st.error("❌ Nenhuma campanha encontrada para este anunciante")
                    else:
                        # Etapa 2: Processamento e análise
                        status_text.text("🧠 Analisando campanhas e recomendando estratégias...")
                        progress_bar.progress(50)
                        
                        # Usar dados hardcoded (não precisa mais do caminho do arquivo)
                        filename, consolidated_df = process_and_export(
                            campaigns_df, client_name
                        )
                        
                        # Etapa 3: Geração do relatório
                        status_text.text("📋 Gerando relatório resumo...")
                        progress_bar.progress(75)
                        
                        summary = generate_summary_report(consolidated_df, client_name)
                        
                        # Etapa 4: Finalização
                        status_text.text("✅ Análise concluída!")
                        progress_bar.progress(100)
                        
                        # Exibir resultados
                        st.success(f"🎉 Análise concluída com sucesso!")
                        
                        # Download do arquivo
                        with open(filename, "rb") as file:
                            st.download_button(
                                label="📥 Baixar Planilha de Análise",
                                data=file.read(),
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        # Armazenar resultados na sessão
                        st.session_state.last_analysis = {
                            "summary": summary,
                            "consolidated_df": consolidated_df,
                            "filename": filename
                        }
                        
                        # Limpar progress bar e status
                        progress_bar.empty()
                        status_text.empty()
                        
                except Exception as e:
                    st.error(f"❌ Erro durante a análise: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()
            else:
                st.warning("⚠️ Por favor, valide o token primeiro")
    else:
        st.info("ℹ️ Preencha o Access Token e o Nome do Cliente na barra lateral para começar")

with col2:
    st.header("📈 Resumo da Análise")
    
    if hasattr(st.session_state, "last_analysis"):
        summary = st.session_state.last_analysis["summary"]
        
        # Métricas principais
        st.metric("Total de Campanhas", summary["total_campanhas"])
        st.metric("ACOS Médio", f"{summary["acos_medio"]:.2f}%")
        st.metric("Orçamento Total", f"R$ {summary["orcamento_total"]:,.2f}")
        
        # Estratégias recomendadas
        st.subheader("🎯 Estratégias Recomendadas")
        for strategy, count in summary["estrategias_recomendadas"].items():
            st.write(f"• **{strategy}**: {count} campanha(s)")
    else:
        st.info("Execute uma análise para ver o resumo aqui")

# Seção de cards de campanhas
if hasattr(st.session_state, "last_analysis"):
    st.markdown("---")
    st.header("📋 Detalhes das Campanhas")
    
    consolidated_df = st.session_state.last_analysis["consolidated_df"]
    
    # Carregar dados das estratégias para comparação
    from strategy_analyzer_module import hardcoded_strategy_model_data
    strategy_df = pd.DataFrame(hardcoded_strategy_model_data)
    
    # Criar cards para cada campanha
    for index, campaign in consolidated_df.iterrows():
        card_html = create_campaign_card(campaign, strategy_df)
        st.markdown(card_html, unsafe_allow_html=True)

# Seção de histórico
st.markdown("---")
st.header("📚 Histórico de Análises")

# Listar arquivos de análise existentes
analysis_files = [f for f in os.listdir(".") if f.endswith("_analise_campanhas_") and f.endswith(".xlsx")]

if analysis_files:
    st.write("Análises anteriores disponíveis:")
    for file in sorted(analysis_files, reverse=True)[:5]:  # Mostrar apenas os 5 mais recentes
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"📄 {file}")
        with col2:
            with open(file, "rb") as f:
                st.download_button(
                    label="⬇️",
                    data=f.read(),
                    file_name=file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=file
                )
else:
    st.info("Nenhuma análise anterior encontrada")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style=\'text-align: center; color: #666;\'>
        <p>Desenvolvido para análise de campanhas do Mercado Livre | Versão 1.0</p>
    </div>
    """,
    unsafe_allow_html=True
)

