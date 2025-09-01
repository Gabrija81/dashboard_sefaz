import pandas as pd
import streamlit as st
import requests
import io

# O @st.cache_data é o segredo para a performance do seu dashboard!
# Ele garante que o processamento pesado só aconteça uma vez.
@st.cache_data
def carregar_e_processar_dados(url_do_parquet):
    """
    Função responsável por ler o arquivo Parquet de uma URL pública
    e aplicar as regras de negócio.
    """
    print("EXECUTANDO A CARGA E PROCESSAMENTO OTIMIZADO DOS DADOS A PARTIR DA URL...")

    try:
        # --- LEITURA DO ARQUIVO A PARTIR DA INTERNET ---
        response = requests.get(url_do_parquet)
        response.raise_for_status()  # Gera um erro se o download falhar

        # Usa BytesIO para ler o conteúdo do arquivo em memória sem salvar em disco
        arquivo_em_memoria = io.BytesIO(response.content)

        # --- OTIMIZAÇÃO DE MEMÓRIA ---
        # Lista de colunas a serem carregadas do arquivo Parquet.
        colunas_necessarias = [
            # Colunas ativas no Dashboard
            'tiqimo_NOMEBAIRRO', 'tiqimo_USOIMOVEL', 'tiqimo_VALORTOTALLOTE',
            'TAXA_PSEI_AJUSTADO', 'TAXA_PSEI_PARC_CORR',

            # Colunas necessárias para cálculos internos (mapeamento PSEI)
            'PSEI_AJUSTADO', 'PSEI_RECLASS_80', 'PSEI_PARC_CORRIGIDO',

            # Colunas para o cálculo de IPTU
            'tiqimo_AVALIACAO', 'tiqimo_ALIQUOTA', 'COBRAR',
        ]

        df = pd.read_parquet(arquivo_em_memoria, columns=colunas_necessarias)

    except Exception as e:
        st.error(f"Erro ao ler o arquivo Parquet da URL: {e}")
        return pd.DataFrame()

    # --- Renomeando colunas para nomes mais amigáveis ---
    column_rename_map = {
        'tiqimo_NOMEBAIRRO': 'nome_bairro', 'tiqimo_USOIMOVEL': 'uso_imovel',
        'tiqimo_VALORTOTALLOTE': 'valor_total_lote', 'TAXA_PSEI_AJUSTADO': 'taxa_psei_ajustado',
        'TAXA_PSEI_PARC_CORR': 'taxa_psei_parcelamento_corrigido', 'PSEI_AJUSTADO': 'psei_ajustado',
        'PSEI_RECLASS_80': 'psei_reclassificado_80', 'PSEI_PARC_CORRIGIDO': 'psei_parcelamento_corrigido',
        'tiqimo_AVALIACAO': 'avaliacao', 'tiqimo_ALIQUOTA': 'aliquota', 'COBRAR': 'cobrar',
    }
    df = df.rename(columns=column_rename_map)

    # --- CÁLCULO DO IPTU ---
    df['avaliacao'] = pd.to_numeric(df['avaliacao'], errors='coerce').fillna(0)
    df['aliquota'] = pd.to_numeric(df['aliquota'], errors='coerce').fillna(0)
    df['iptu_calculado'] = 0.0
    df.loc[df['cobrar'] == True, 'iptu_calculado'] = df['avaliacao'] * (df['aliquota'] / 100)

    return df
