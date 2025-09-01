import streamlit as st
import plotly.express as px
import pandas as pd
import os # Importamos a biblioteca 'os' para lidar com caminhos de arquivos

# Importa a função principal do seu outro arquivo
from processamento import carregar_e_processar_dados

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Análise da Taxa de Lixo")

# --- Funções Auxiliares ---
def convert_df_to_csv(df):
    """Converte o DataFrame para CSV, otimizado para o botão de download."""
    # Esta função agora recebe um DataFrame normal, sem geometria.
    return df.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')

# --- Título do Dashboard ---
st.title("📊 Dashboard de Análise de Imóveis e Taxas")
st.markdown("Utilize os filtros na barra lateral para explorar os dados.")

# --- Carregamento dos Dados (COM A CORREÇÃO) ---
script_dir = os.path.dirname(__file__)
caminho_do_arquivo = os.path.join(script_dir, 'imoveis_relatorio.parquet')
gdf = carregar_e_processar_dados(caminho_do_arquivo) # Renomeado para 'gdf' para clareza (GeoDataFrame)

# --- Barra Lateral de Filtros ---
st.sidebar.header("Filtros")

if not gdf.empty:
    # Filtro por Bairro
    bairros_disponiveis = sorted(gdf['nome_bairro'].dropna().unique())
    bairros_selecionados = st.sidebar.multiselect(
        "Selecione o(s) Bairro(s):",
        options=bairros_disponis,
        default=bairros_disponis
    )

    # Filtro por Uso do Imóvel
    usos_disponiveis = sorted(gdf['uso_imovel'].dropna().unique())
    usos_selecionados = st.sidebar.multiselect(
        "Selecione o Uso do Imóvel:",
        options=usos_disponiveis,
        default=usos_disponiveis
    )

    # FILTRO: Categoria de Uso (PSEI)
    categorias_disponiveis = sorted(gdf['categoria_uso_psei'].dropna().unique())
    categorias_selecionadas = st.sidebar.multiselect(
        "Selecione a Categoria de Uso (PSEI):",
        options=categorias_disponiveis,
        default=categorias_disponiveis
    )

    # Aplica todos os filtros ao GeoDataFrame
    gdf_filtrado = gdf[
        gdf['nome_bairro'].isin(bairros_selecionados) &
        gdf['uso_imovel'].isin(usos_selecionados) &
        gdf['categoria_uso_psei'].isin(categorias_selecionadas)
    ]
    
    # --- PONTO CHAVE DA CORREÇÃO ---
    # Cria uma versão em Pandas (sem geometria) para usar nos elementos do dashboard.
    df_display = pd.DataFrame(gdf_filtrado.drop(columns='geometry'))


    # --- Corpo Principal do Dashboard ---
    if df_display.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        # --- Métricas Principais (KPIs) ---
        st.subheader("Resumo dos Dados Filtrados")
        
        # Calculando os totais das taxas
        total_taxa_ajustado = df_display['taxa_psei_ajustado'].sum()
        total_taxa_parc_corr = df_display['taxa_psei_parcelamento_corrigido'].sum()
        diferenca_taxas = total_taxa_ajustado - total_taxa_parc_corr

        # Layout das métricas em duas linhas para melhor organização
        col1, col2 = st.columns(2)
        col1.metric("Total de Imóveis", f"{df_display.shape[0]:,}".replace(",", "."))
        col2.metric("Valor Venal Total (R$)", f"{df_display['valor_total_lote'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

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
            uso_counts = df_display['uso_imovel'].value_counts().reset_index()
            fig_uso_imovel = px.pie(uso_counts, names='uso_imovel', values='count', title='Distribuição por Uso do Imóvel')
            st.plotly_chart(fig_uso_imovel, use_container_width=True)

        with gcol2:
            # Gráfico 2: Top 10 Bairros por Arrecadação (PSEI Ajustado)
            taxa_por_bairro = df_display.groupby('nome_bairro')['taxa_psei_ajustado'].sum().nlargest(10).reset_index()
            fig_taxa_bairro = px.bar(
                taxa_por_bairro, x='nome_bairro', y='taxa_psei_ajustado',
                title='Top 10 Bairros por Arrecadação (PSEI Ajustado)',
                labels={'nome_bairro': 'Bairro', 'taxa_psei_ajustado': 'Taxa Total (R$)'}, text_auto='.2s'
            )
            st.plotly_chart(fig_taxa_bairro, use_container_width=True)
            
        # GRÁFICO: Comparativo de Taxas por Bairro
        st.markdown("---")
        st.subheader("Análise Comparativa de Taxas por Bairro")
        
        taxas_comparativas = df_display.groupby('nome_bairro')[['taxa_psei_ajustado', 'taxa_psei_parcelamento_corrigido']].sum().reset_index()
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
        st.info(f"A tabela completa contém {df_display.shape[0]:,} registros. Apenas as primeiras 1.000 linhas são exibidas.")
        st.dataframe(df_display.head(1000))

        # BOTÃO de Download
        csv_data = convert_df_to_csv(df_display)
        st.download_button(
            label="📥 Download dos Dados Filtrados (CSV)", data=csv_data,
            file_name='dados_filtrados.csv', mime='text/csv',
        )
else:
    st.error("Não foi possível carregar os dados. Verifique o arquivo de processamento e o caminho do Parquet.")

