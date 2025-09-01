import streamlit as st
import plotly.express as px
import os
import pandas as pd
from processamento import carregar_e_processar_dados

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Análise de Imóveis e Taxas")

# --- FUNÇÃO PARA DOWNLOAD ---
# A conversão para CSV é rápida, não precisa de cache.
def convert_df_to_csv(df):
    """Converte um DataFrame para um arquivo CSV em memória."""
    return df.to_csv(index=False).encode('utf-8')

# --- TÍTULO ---
st.title("📊 Dashboard de Análise de Imóveis e Taxas")
st.write("Utilize os filtros na barra lateral para explorar os dados.")

# --- CARREGAMENTO DOS DADOS ---
# Construindo o caminho para o arquivo de dados de forma robusta
try:
    caminho_script = os.path.dirname(__file__)
    caminho_parquet = os.path.join(caminho_script, 'imoveis_relatorio.parquet')
    df_completo = carregar_e_processar_dados(caminho_parquet)
except Exception:
    st.error("Erro ao construir o caminho para o arquivo de dados. Verifique a estrutura das pastas.")
    df_completo = pd.DataFrame()


# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("Filtros")

# Inicializa o dataframe filtrado com o dataframe completo
df_filtrado = df_completo.copy()

# Verifica se o dataframe não está vazio para criar os filtros
if not df_completo.empty:
    # Filtro de Bairro
    bairros_selecionados = st.sidebar.multiselect(
        "Selecione o(s) Bairro(s):",
        # CORREÇÃO: Tratamento robusto para evitar erros com valores nulos ou tipos mistos
        options=sorted([str(b) for b in df_completo['nome_bairro'].dropna().unique()]),
        default=[]
    )

    # Filtro de Uso do Imóvel
    usos_selecionados = st.sidebar.multiselect(
        "Selecione o(s) Uso(s) do Imóvel:",
        # CORREÇÃO: Tratamento robusto para evitar erros
        options=sorted([str(u) for u in df_completo['uso_imovel'].dropna().unique()]),
        default=[]
    )

    # Lógica de filtragem - aplica os filtros se alguma seleção for feita
    if bairros_selecionados:
        df_filtrado = df_filtrado[df_filtrado['nome_bairro'].isin(bairros_selecionados)]
    
    if usos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['uso_imovel'].isin(usos_selecionados)]

# --- EXIBIÇÃO DO DASHBOARD ---

if df_filtrado.empty and not df_completo.empty:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
elif df_completo.empty:
    st.error("Não foi possível carregar os dados. Verifique a console de logs.")
else:
    # --- MÉTRICAS (KPIs) ---
    st.header("Resumo dos Dados Filtrados")
    col1, col2, col3 = st.columns(3)
    col1.metric("Número de Imóveis", f"{df_filtrado.shape[0]:,}")
    # ALTERAÇÃO: Trocado 'valor_total_lote' pela nova coluna 'iptu_calculado'
    col2.metric("IPTU Calculado (R$)", f"{df_filtrado['iptu_calculado'].sum():,.2f}")
    col3.metric("Taxa PSEI Ajustado (R$)", f"{df_filtrado['taxa_psei_ajustado'].sum():,.2f}")

    st.divider()
    
    # --- MÉTRICAS DE COMPARAÇÃO DE TAXAS ---
    st.subheader("Comparativo entre Cenários de Taxa")
    col_comp1, col_comp2, col_comp3 = st.columns(3)
    
    total_taxa_ajustado = df_filtrado['taxa_psei_ajustado'].sum()
    total_taxa_corrigido = df_filtrado['taxa_psei_parcelamento_corrigido'].sum()
    diferenca = total_taxa_ajustado - total_taxa_corrigido
    
    col_comp1.metric("Total Taxa PSEI Ajustado (R$)", f"{total_taxa_ajustado:,.2f}")
    col_comp2.metric("Total Taxa Parc. Corrigido (R$)", f"{total_taxa_corrigido:,.2f}")
    col_comp3.metric("Diferença (Ajustado - Corrigido)", f"{diferenca:,.2f}", delta_color="off")


    # --- GRÁFICOS ---
    st.header("Análises Gráficas")
    
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Contagem de Imóveis por Uso")
        if not df_filtrado.empty:
            # ALTERAÇÃO: Gráfico de pizza para histograma (gráfico de barras)
            fig_hist_uso = px.histogram(
                df_filtrado,
                x='uso_imovel',
                title="Contagem de Imóveis por Tipo de Uso",
                labels={'uso_imovel': 'Tipo de Uso', 'count': 'Número de Imóveis'}
            ).update_xaxes(categoryorder='total descending') # Ordena as barras
            st.plotly_chart(fig_hist_uso, use_container_width=True)
            
    with col_graf2:
        st.subheader("Total da Taxa (PSEI Ajustado) por Bairro")
        # Mostra o gráfico com todos os bairros por padrão, e filtra se selecionado
        taxa_por_bairro = df_filtrado.groupby('nome_bairro')['taxa_psei_ajustado'].sum().sort_values(ascending=False).head(20)
        fig_bar_bairro = px.bar(
            taxa_por_bairro,
            x=taxa_por_bairro.index,
            y=taxa_por_bairro.values,
            title="Total Arrecadado por Bairro (Top 20)",
            labels={'x': 'Bairro', 'y': 'Total Taxa (R$)'}
        )
        st.plotly_chart(fig_bar_bairro, use_container_width=True)
            
    st.divider()
    
    # --- GRÁFICO COMPARATIVO DE TAXAS ---
    st.subheader("Comparativo de Taxas por Bairro")
    if not df_filtrado.empty:
        df_grouped = df_filtrado.groupby('nome_bairro')[['taxa_psei_ajustado', 'taxa_psei_parcelamento_corrigido']].sum().reset_index()
        # Pega apenas os top 20 bairros para não poluir o gráfico
        top_bairros = df_grouped.nlargest(20, 'taxa_psei_ajustado')['nome_bairro']
        df_grouped = df_grouped[df_grouped['nome_bairro'].isin(top_bairros)]
        
        df_melted = df_grouped.melt(
            id_vars='nome_bairro', 
            var_name='Tipo de Taxa', 
            value_name='Valor Total'
        )

        fig_comp_bar = px.bar(
            df_melted,
            x='nome_bairro',
            y='Valor Total',
            color='Tipo de Taxa',
            barmode='group',
            title='Comparativo de Taxas por Bairro (Top 20 por Taxa Ajustada)',
            labels={'nome_bairro': 'Bairro', 'Valor Total': 'Total Arrecadado (R$)'}
        )
        st.plotly_chart(fig_comp_bar, use_container_width=True)


    # --- TABELA DE DADOS ---
    st.header("Dados Detalhados")
    st.dataframe(df_filtrado.head(1000))
    
    # BOTÃO de Download
    csv_data = convert_df_to_csv(df_filtrado)
    st.download_button(
        label="📥 Download dos Dados Filtrados (CSV)",
        data=csv_data,
        file_name='dados_filtrados.csv',
        mime='text/csv',
    )
