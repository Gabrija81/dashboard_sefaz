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
# CORREÇÃO DEFINITIVA: Usando a URL de download direto correta.
URL_DO_PARQUET = "https://drive.google.com/uc?export=download&id=17eyIEl3pjx0C9-_74OhtkD5eNLxfi5aG"

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
    col_comp2.metric("Total Taxa Reclassificada (R$)", format_brazilian_currency(total_taxa_corrigido))
    col_comp3.metric("Diferença (Ajustado - Reclass.)", format_brazilian_currency(diferenca), delta_color="off")

    # --- GRÁFICOS ---
    st.header("Análises Gráficas")
    
    col_graf1, col_graf2 = st.columns(2)

    # Dicionário para renomear as taxas nos gráficos
    rename_map = {
        'taxa_psei_ajustado': 'Taxa Ajustada',
        'taxa_psei_parcelamento_corrigido': 'Taxa Reclassificada'
    }

    with col_graf1:
        st.subheader("Comparativo de Taxas por Uso do Imóvel")
        if not df_filtrado.empty:
            soma_por_uso = df_filtrado.groupby('uso_imovel')[['taxa_psei_ajustado', 'taxa_psei_parcelamento_corrigido']].sum().reset_index()
            soma_por_uso_melted = soma_por_uso.melt(id_vars='uso_imovel', var_name='Tipo de Taxa', value_name='Valor Total')
            soma_por_uso_melted['Tipo de Taxa'] = soma_por_uso_melted['Tipo de Taxa'].map(rename_map)

            fig_bar_uso = px.bar(
                soma_por_uso_melted,
                x='uso_imovel',
                y='Valor Total',
                color='Tipo de Taxa',
                barmode='group',
                title="Soma das Taxas por Tipo de Uso",
                labels={'uso_imovel': 'Tipo de Uso', 'Valor Total': 'Soma da Taxa (R$)'}
            ).update_xaxes(categoryorder='total descending')
            st.plotly_chart(fig_bar_uso, use_container_width=True)
            
    with col_graf2:
        # ALTERAÇÃO: Substituindo o gráfico de barras por um Treemap interativo
        st.subheader("Distribuição das Taxas por Bairro")
        
        taxa_selecionada = st.radio(
            "Selecione a taxa para visualizar no Treemap:",
            ('Taxa Ajustada', 'Taxa Reclassificada'),
            horizontal=True
        )

        taxa_coluna_map = {
            'Taxa Ajustada': 'taxa_psei_ajustado',
            'Taxa Reclassificada': 'taxa_psei_parcelamento_corrigido'
        }
        taxa_escolhida_col = taxa_coluna_map[taxa_selecionada]

        if not df_filtrado.empty:
            taxa_por_bairro_treemap = df_filtrado.groupby('nome_bairro')[taxa_escolhida_col].sum().reset_index()
            taxa_por_bairro_treemap = taxa_por_bairro_treemap[taxa_por_bairro_treemap[taxa_escolhida_col] > 0]

            fig_treemap_bairro = px.treemap(
                taxa_por_bairro_treemap,
                path=[px.Constant("Todos os Bairros"), 'nome_bairro'],
                values=taxa_escolhida_col,
                color=taxa_escolhida_col,
                color_continuous_scale='Blues',
                title=f"Distribuição da {taxa_selecionada} por Bairro"
            )
            fig_treemap_bairro.update_layout(margin = dict(t=50, l=25, r=25, b=25))
            st.plotly_chart(fig_treemap_bairro, use_container_width=True)
            
    st.divider()

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
