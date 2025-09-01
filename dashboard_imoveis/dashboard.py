import streamlit as st
import plotly.express as px
import pandas as pd
import os # Importamos a biblioteca 'os' para lidar com caminhos de arquivos

# Importa a função principal do seu outro arquivo
from processamento import carregar_e_processar_dados

# --- Configuração da Página ---
# Usar o layout "wide" aproveita melhor o espaço da tela
st.set_page_config(layout="wide", page_title="Análise da Taxa de Lixo")

# --- Título do Dashboard ---
st.title("📊 Dashboard de Análise de Imóveis e Taxas")
st.markdown("Utilize os filtros na barra lateral para explorar os dados.")

# --- Carregamento dos Dados (COM A CORREÇÃO) ---
# Construímos um caminho que sempre funcionará, não importa de onde o script seja executado.
# 1. Pega o diretório onde o script 'dashboard.py' está localizado.
script_dir = os.path.dirname(__file__)
# 2. Junta esse diretório com o nome do arquivo de dados.
caminho_do_arquivo = os.path.join(script_dir, 'imoveis_relatorio.parquet')

# 3. Passa o caminho completo e correto para a função de carregamento.
df = carregar_e_processar_dados(caminho_do_arquivo)


# --- Barra Lateral de Filtros ---
st.sidebar.header("Filtros")

# Verifica se os dados foram carregados antes de criar os filtros
if not df.empty:
    # Filtro por Bairro
    bairros_disponiveis = sorted(df['nome_bairro'].dropna().unique())
    bairros_selecionados = st.sidebar.multiselect(
        "Selecione o(s) Bairro(s):",
        options=bairros_disponiveis,
        default=bairros_disponiveis # Por padrão, todos vêm selecionados
    )

    # Filtro por Uso do Imóvel
    usos_disponiveis = sorted(df['uso_imovel'].dropna().unique())
    usos_selecionados = st.sidebar.multiselect(
        "Selecione o Uso do Imóvel:",
        options=usos_disponiveis,
        default=usos_disponiveis
    )

    # Aplica os filtros ao DataFrame
    df_filtrado = df[
        df['nome_bairro'].isin(bairros_selecionados) &
        df['uso_imovel'].isin(usos_selecionados)
    ]

    # --- Corpo Principal do Dashboard ---

    # Mostra um aviso se o filtro resultar em zero imóveis
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        # --- Métricas Principais (KPIs) ---
        st.subheader("Resumo dos Dados Filtrados")
        
        col1, col2, col3 = st.columns(3)
        col1.metric(
            label="Total de Imóveis",
            value=f"{df_filtrado.shape[0]:,}".replace(",", ".")
        )
        col2.metric(
            label="Valor Venal Total (R$)",
            value=f"{df_filtrado['valor_total_lote'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        col3.metric(
            label="Taxa Total (PSEI Ajustado)",
            value=f"{df_filtrado['taxa_psei_ajustado'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        st.markdown("---")

        # --- Gráficos ---
        st.subheader("Análises Gráficas")
        
        # Gráfico 1: Total da Taxa por Bairro
        taxa_por_bairro = df_filtrado.groupby('nome_bairro')['taxa_psei_ajustado'].sum().sort_values(ascending=False).reset_index()
        
        fig_taxa_bairro = px.bar(
            taxa_por_bairro,
            x='nome_bairro',
            y='taxa_psei_ajustado',
            title='Total da Taxa (PSEI Ajustado) por Bairro',
            labels={'nome_bairro': 'Bairro', 'taxa_psei_ajustado': 'Taxa Total (R$)'},
            text_auto='.2s'
        )
        fig_taxa_bairro.update_traces(textangle=0, textposition="outside")
        st.plotly_chart(fig_taxa_bairro, use_container_width=True)

        # --- Tabela de Dados ---
        st.subheader("Amostra dos Dados Detalhados")
        st.info(f"A tabela completa contém {df_filtrado.shape[0]:,} registros. Para evitar lentidão no navegador, apenas as primeiras 1.000 linhas são exibidas abaixo.")
        st.dataframe(df_filtrado.head(1000))

else:
    st.error("Não foi possível carregar os dados. Verifique o arquivo de processamento e o caminho do Parquet.")
