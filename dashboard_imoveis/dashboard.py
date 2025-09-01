import streamlit as st
import plotly.express as px
import pandas as pd
import os # Importamos a biblioteca 'os' para lidar com caminhos de arquivos

# Importa a função principal do seu outro arquivo
from processamento import carregar_e_processar_dados

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Análise da Taxa de Lixo")

# --- Funções Auxiliares ---
@st.cache_data
def convert_df_to_csv(df):
    """Converte o DataFrame para CSV, otimizado para o botão de download."""
    # Garante que a geometria não seja exportada para o CSV
    df_sem_geometria = df.drop(columns=['geometry'], errors='ignore')
    return df_sem_geometria.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')

# --- Título do Dashboard ---
st.title("📊 Dashboard de Análise de Imóveis e Taxas")
st.markdown("Utilize os filtros na barra lateral para explorar os dados.")

# --- Carregamento dos Dados (COM A CORREÇÃO) ---
script_dir = os.path.dirname(__file__)
caminho_do_arquivo = os.path.join(script_dir, 'imoveis_relatorio.parquet')
df = carregar_e_processar_dados(caminho_do_arquivo)

# --- Barra Lateral de Filtros ---
st.sidebar.header("Filtros")

if not df.empty:
    # Filtro por Bairro
    bairros_disponiveis = sorted(df['nome_bairro'].dropna().unique())
    bairros_selecionados = st.sidebar.multiselect(
        "Selecione o(s) Bairro(s):",
        options=bairros_disponiveis,
        default=bairros_disponiveis
    )

    # Filtro por Uso do Imóvel
    usos_disponiveis = sorted(df['uso_imovel'].dropna().unique())
    usos_selecionados = st.sidebar.multiselect(
        "Selecione o Uso do Imóvel:",
        options=usos_disponiveis,
        default=usos_disponiveis
    )

    # FILTRO: Categoria de Uso (PSEI)
    categorias_disponiveis = sorted(df['categoria_uso_psei'].dropna().unique())
    categorias_selecionadas = st.sidebar.multiselect(
        "Selecione a Categoria de Uso (PSEI):",
        options=categorias_disponiveis,
        default=categorias_disponiveis
    )

    # Aplica todos os filtros ao DataFrame
    df_filtrado = df[
        df['nome_bairro'].isin(bairros_selecionados) &
        df['uso_imovel'].isin(usos_selecionados) &
        df['categoria_uso_psei'].isin(categorias_selecionadas)
    ]

    # --- Corpo Principal do Dashboard ---
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        # --- Métricas Principais (KPIs) ---
        st.subheader("Resumo dos Dados Filtrados")
        
        # Calculando os totais das taxas
        total_taxa_ajustado = df_filtrado['taxa_psei_ajustado'].sum()
        total_taxa_parc_corr = df_filtrado['taxa_psei_parcelamento_corrigido'].sum()
        diferenca_taxas = total_taxa_ajustado - total_taxa_parc_corr

        # Layout das métricas em duas linhas para melhor organização
        col1, col2 = st.columns(2)
        col1.metric("Total de Imóveis", f"{df_filtrado.shape[0]:,}".replace(",", "."))
        col2.metric("Valor Venal Total (R$)", f"{df_filtrado['valor_total_lote'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("---")
        st.subheader("Comparativo de Arrecadação por Cenário")
        col3, col4, col5 = st.columns(3)
        col3.metric("Total Taxa (PSEI Ajustado)", f"{total_taxa_ajustado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col4.metric("Total Taxa (Parc. Corrigido)", f"{total_taxa_parc_corr:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col5.metric("Diferença (Ajustado - Corrigido)", f"{diferenca_taxas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("---")

        # --- Gráficos ---
        st.subheader("Análises Gráficas")
        
        gcol1, gcol2 = st.columns(2)
        with gcol1:
            # Gráfico 1: Distribuição por Uso do Imóvel
            uso_counts = df_filtrado['uso_imovel'].value_counts().reset_index()
            fig_uso_imovel = px.pie(uso_counts, names='uso_imovel', values='count', title='Distribuição por Uso do Imóvel')
            st.plotly_chart(fig_uso_imovel, use_container_width=True)

        with gcol2:
            # Gráfico 2: Top 10 Bairros por Arrecadação (PSEI Ajustado)
            taxa_por_bairro = df_filtrado.groupby('nome_bairro')['taxa_psei_ajustado'].sum().nlargest(10).reset_index()
            fig_taxa_bairro = px.bar(
                taxa_por_bairro, x='nome_bairro', y='taxa_psei_ajustado',
                title='Top 10 Bairros por Arrecadação (PSEI Ajustado)',
                labels={'nome_bairro': 'Bairro', 'taxa_psei_ajustado': 'Taxa Total (R$)'}, text_auto='.2s'
            )
            st.plotly_chart(fig_taxa_bairro, use_container_width=True)
            
        # NOVO GRÁFICO: Comparativo de Taxas por Bairro
        st.markdown("---")
        st.subheader("Análise Comparativa de Taxas por Bairro")
        
        taxas_comparativas = df_filtrado.groupby('nome_bairro')[['taxa_psei_ajustado', 'taxa_psei_parcelamento_corrigido']].sum().reset_index()
        taxas_comparativas_melted = taxas_comparativas.melt(
            id_vars='nome_bairro', value_vars=['taxa_psei_ajustado', 'taxa_psei_parcelamento_corrigido'],
            var_name='Tipo de Taxa', value_name='Valor Total (R$)'
        )
        fig_comparativa = px.bar(
            taxas_comparativas_melted, x='nome_bairro', y='Valor Total (R$)', color='Tipo de Taxa',
            barmode='group', title='Comparativo de Taxas por Bairro', labels={'nome_bairro': 'Bairro'}, text_auto='.2s'
        )
        st.plotly_chart(fig_comparativa, use_container_width=True)

        # --- Tabela de Dados ---
        st.subheader("Amostra dos Dados Detalhados")
        st.info(f"A tabela completa contém {df_filtrado.shape[0]:,} registros. Apenas as primeiras 1.000 linhas são exibidas.")
        st.dataframe(df_filtrado.head(1000).drop(columns=['geometry'], errors='ignore'))

        # BOTÃO de Download
        csv_data = convert_df_to_csv(df_filtrado)
        st.download_button(
            label="📥 Download dos Dados Filtrados (CSV)", data=csv_data,
            file_name='dados_filtrados.csv', mime='text/csv',
        )
else:
    st.error("Não foi possível carregar os dados. Verifique o arquivo de processamento e o caminho do Parquet.")

