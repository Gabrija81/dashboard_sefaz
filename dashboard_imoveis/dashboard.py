import streamlit as st
import plotly.express as px
import os
import pandas as pd
from processamento import carregar_e_processar_dados

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Análise de Imóveis e Taxas")

# --- FUNÇÕES AUXILIARES DE FORMATAÇÃO ---
def convert_df_to_csv(df):
    """Converte um DataFrame para um arquivo CSV em memória."""
    return df.to_csv(index=False).encode('utf-8')

def format_brazilian_currency(number):
    """Formata um número para o padrão de moeda brasileiro (1.234,56)."""
    return f"{number:,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')

def format_brazilian_integer(number):
    """Formata um inteiro para o padrão brasileiro (1.234)."""
    return f"{number:,}".replace(',', '.')

# --- TÍTULO ---
st.title("📊 Dashboard de Análise de Imóveis e Taxas")
st.write("Utilize os filtros na barra lateral para explorar os dados.")


# --- CARREGAMENTO DOS DADOS A PARTIR DA URL ---
# <<< SUBSTITUA PELA SUA URL DE DOWNLOAD DIRETO DO GOOGLE DRIVE AQUI
URL_DO_PARQUET = "https://drive.google.com/file/d/17eyIEl3pjx0C9-_74OhtkD5eNLxfi5aG/view?usp=sharing"

df_completo = carregar_e_processar_dados(URL_DO_PARQUET)


# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("Filtros")

# Inicializa o dataframe filtrado com o dataframe completo
df_filtrado = df_completo.copy()

# Verifica se o dataframe não está vazio para criar os filtros
if not df_completo.empty:
    # Filtro de Bairro
    bairros_selecionados = st.sidebar.multiselect(
        "Selecione o(s) Bairro(s):",
        options=sorted([str(b) for b in df_completo['nome_bairro'].dropna().unique()]),
        default=[]
    )

    # Filtro de Uso do Imóvel
    usos_selecionados = st.sidebar.multiselect(
        "Selecione o(s) Uso(s) do Imóvel:",
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
    st.error("Não foi possível carregar os dados. Verifique a URL e as permissões do arquivo.")
else:
    # --- MÉTRICAS (KPIs) ---
    st.header("Resumo dos Dados Filtrados")
    col1, col2, col3 = st.columns(3)
    col1.metric("Número de Imóveis", format_brazilian_integer(df_filtrado.shape[0]))
    col2.metric("IPTU Calculado (R$)", format_brazilian_currency(df_filtrado['iptu_calculado'].sum()))
    col3.metric("Taxa PSEI Ajustado (R$)", format_brazilian_currency(df_filtrado['taxa_psei_ajustado'].sum()))

    st.divider()
    
    # --- MÉTRICAS DE COMPARAÇÃO DE TAXAS ---
    st.subheader("Comparativo entre Cenários de Taxa")
    col_comp1, col_comp2, col_comp3 = st.columns(3)
    
    total_taxa_ajustado = df_filtrado['taxa_psei_ajustado'].sum()
    total_taxa_corrigido = df_filtrado['taxa_psei_parcelamento_corrigido'].sum()
    diferenca = total_taxa_ajustado - total_taxa_corrigido
    
    col_comp1.metric("Total Taxa PSEI Ajustado (R$)", format_brazilian_currency(total_taxa_ajustado))
    col_comp2.metric("Total Taxa Parc. Corrigido (R$)", format_brazilian_currency(total_taxa_corrigido))
    col_comp3.metric("Diferença (Ajustado - Corrigido)", format_brazilian_currency(diferenca), delta_color="off")

    # --- GRÁFICOS ---
    st.header("Análises Gráficas")
    
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Contagem de Imóveis por Uso")
        if not df_filtrado.empty:
            fig_hist_uso = px.histogram(
                df_filtrado,
                x='uso_imovel',
                title="Contagem de Imóveis por Tipo de Uso",
                labels={'uso_imovel': 'Tipo de Uso', 'count': 'Número de Imóveis'}
            ).update_xaxes(categoryorder='total descending')
            st.plotly_chart(fig_hist_uso, use_container_width=True)
            
    with col_graf2:
        st.subheader("Total da Taxa (PSEI Ajustado) por Bairro")
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
