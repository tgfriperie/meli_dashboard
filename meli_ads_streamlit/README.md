# Analisador de Campanhas do Mercado Livre

## Descrição

Este aplicativo Streamlit automatiza a coleta de dados de campanhas do Mercado Livre, realiza análise comparativa com um modelo de estratégia e gera recomendações personalizadas para múltiplos clientes.

## Funcionalidades

- 🔍 **Coleta Automática de Dados**: Conecta-se à API do Mercado Livre para coletar dados de campanhas
- 🧠 **Análise Inteligente**: Compara campanhas com modelo de estratégias ideais
- 📊 **Recomendações Personalizadas**: Sugere a melhor estratégia para cada campanha
- 📥 **Exportação de Planilhas**: Gera arquivo Excel com análise completa
- 👥 **Multi-cliente**: Suporte para múltiplos clientes com diferentes tokens de acesso

## Estrutura do Projeto

```
meli_ads_streamlit/
├── app.py                          # Interface principal do Streamlit
├── meli_ads_collector_module.py    # Módulo de coleta de dados da API
├── strategy_analyzer_module.py     # Módulo de análise e recomendação
├── data_processor_module.py        # Módulo de processamento e exportação
├── tabela_extraida.xlsx           # Modelo de estratégias ideais
├── requirements.txt               # Dependências do projeto
└── README.md                      # Documentação
```

## Instalação

1. Clone ou baixe o projeto
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Como Usar

1. **Executar o aplicativo**:
```bash
streamlit run app.py
```

2. **Configurar cliente**:
   - Insira o Access Token do Mercado Livre
   - Digite o nome do cliente
   - Clique em "Validar Token"

3. **Executar análise**:
   - Clique em "Executar Análise Completa"
   - Aguarde o processamento
   - Baixe a planilha gerada

## Obtenção do Access Token

Para obter um Access Token do Mercado Livre:

1. Acesse https://developers.mercadolivre.com.br/
2. Crie uma aplicação
3. Siga o fluxo de autenticação OAuth 2.0
4. Consulte a documentação oficial para mais detalhes

## Modelo de Estratégia

O arquivo `tabela_extraida.xlsx` contém o modelo de estratégias ideais com as seguintes colunas:

- **Nome**: Nome da estratégia
- **Orçamento**: Orçamento ideal
- **ACOS Objetivo**: ACOS alvo
- **ACOS**: ACOS ideal
- **Tipo de Impressão**: Classificação (Baixa, Média, Elevada)
- **% de impressões ganhas**: Percentual ideal
- **Cliques**: Número de cliques ideal
- E outras métricas relevantes

## Lógica de Recomendação

O sistema compara cada campanha com as estratégias do modelo usando:

1. **ACOS**: Diferença absoluta (peso maior)
2. **Tipo de Impressão**: Correspondência qualitativa
3. **Cliques**: Faixa de tolerância

A estratégia com menor "diferença" é recomendada.

## Saída

O aplicativo gera:

- **Planilha Excel**: Dados consolidados com recomendações
- **Resumo**: Métricas principais e distribuição de estratégias
- **Histórico**: Análises anteriores disponíveis para download

## Exemplo de Cliente

**McCoys Pickle Factory** é o cliente de exemplo já configurado no sistema.

## Suporte

Para dúvidas ou problemas, consulte a documentação da API do Mercado Livre ou entre em contato com o desenvolvedor.

