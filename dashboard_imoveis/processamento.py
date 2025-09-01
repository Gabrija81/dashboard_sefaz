import pandas as pd
import geopandas as gpd
import streamlit as st

@st.cache_data # O segredo da performance! Processa os dados uma vez e guarda na memória.
def carregar_e_processar_dados(caminho_arquivo_parquet):
    """
    Função completa para carregar o arquivo GeoParquet, aplicar as transformações
    e retornar um GeoDataFrame limpo e pronto para análise.
    """
    # --- 1. Carregamento dos Dados ---
    try:
        gdf = gpd.read_parquet(caminho_arquivo_parquet)
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado no caminho: {caminho_arquivo_parquet}")
        return pd.DataFrame() # Retorna um DataFrame vazio se o arquivo não for encontrado

    # --- 2. Mapeamento de Categorias para Valores Numéricos ---
    def map_psei_category_to_numeric(category):
        """Mapeia a categoria PSEI para um valor numérico."""
        mapping = {
            'BI': 1, 'BM': 2, 'BS': 3,
            'NI': 4, 'NM': 5, 'NS': 6,
            'AI': 7, 'AM': 8, 'AS': 9
        }
        return mapping.get(category, None)

    columns_to_map = [
        'PSEI_AJUSTADO', 'PSEI_RECLASSIFICADO', 'PSEI_RECLASS_80',
        'PSEI_RECLASS80_GLEBA', 'PSEI_PARC_CORRIGIDO',
    ]

    for col in columns_to_map:
        new_col_name = f'{col.lower()}_n'
        if col in gdf.columns:
            gdf[new_col_name] = gdf[col].apply(map_psei_category_to_numeric)

    # --- 3. Renomear e Selecionar Colunas ---
    # Dicionário para renomear as colunas para um padrão mais limpo
    column_rename_map = {
        'INSCANT': 'inscant', 'tiqimo_CODELOTE': 'codelote', 'tiqimo_NOMEREGIAO': 'nome_regiao',
        'tiqimo_NOMEBAIRRO': 'nome_bairro', 'tiqimo_PARCELAMEN': 'parcelamento', 'tiqimo_QUADRA': 'quadra',
        'tiqimo_LOTE': 'lote', 'tiqimo_TIPOLOC': 'tipo_logradouro', 'tiqimo_RUAIMO': 'nome_logradouro',
        'tiqimo_NRPORTA': 'numero_porta', 'tiqimo_PROPRIETAR': 'proprietario', 'tiqimo_COMPROMISS': 'compromissario',
        'tiqimo_ADMINISTRA': 'administrador', 'tiqimo_TAXACAO': 'taxacao', 'tiqimo_DESCRICAOT': 'descricao_tax',
        'tiqimo_USOIMOVEL': 'uso_imovel', 'tiqimo_SETORCALCU': 'setor_calculo', 'tiqimo_VALORVENAL': 'valor_venal_sc',
        'tiqimo_TESTADA': 'testada', 'tiqimo_NRTESTADA': 'numero_testada', 'tiqimo_FRACAOIDEA': 'fracao_ideal',
        'tiqimo_AREATERREN': 'area_terreno', 'tiqimo_AREALOTE': 'area_lote', 'tiqimo_AREAEDIFICIMOVEL': 'area_edificada_imovel',
        'tiqimo_VALORCONST': 'valor_construcao', 'tiqimo_AVALIACAO': 'avaliacao', 'tiqimo_VALORTERRENOLOTE': 'valor_terreno_lote',
        'tiqimo_VALOREDIFICLOTE': 'valor_edificacao_lote', 'tiqimo_VALORTOTALLOTE': 'valor_total_lote', 'tiqimo_ALIQUOTA': 'aliquota',
        'tiqimo_CPF_CNPJ': 'cpf_cnpj', 'PRECISAO': 'precisao', 'CATEGORIA_USO': 'categoria_uso_psei', 'COBRAR': 'cobrar',
        'PSEI_AJUSTADO': 'psei_ajustado', 'TAXA_PSEI_AJUSTADO': 'taxa_psei_ajustado', 'PSEI_RECLASSIFICADO': 'psei_reclassificado',
        'TAXA_PSEI_RECLASS': 'taxa_psei_reclassificado', 'PSEI_RECLASS_80': 'psei_reclassificado_80',
        'TAXA_PSEI_RECLASS_80': 'taxa_psei_reclassificado_80', 'GLEBAS_CATEG': 'glebas_categorias',
        'PSEI_RECLASS80_GLEBA': 'psei_reclassificado_80_gleba', 'TAXA_PSEI_RECLASS80_GLEBA': 'taxa_psei_reclassificado_80_gleba',
        'PSEI_PARC_CORRIGIDO': 'psei_parcelamento_corrigido', 'TAXA_PSEI_PARC_CORR': 'taxa_psei_parcelamento_corrigido',
        'CALC_NOME_CONDOMINIO': 'calc_nome_condominio', 'CALC_KRIG_CONDOMINIO': 'calc_krigagem_condominio',
        'CALC_KRIG_GERAL': 'calc_krigagem_geral', 'CALC_VU_MEDIO': 'calc_vu_medio', 'CALC_VU_MEDIO_AJUSTADO': 'calc_vu_medio_ajustado',
        'CALC_AV_TERRENO_AJUSTADO': 'calc_av_terreno_ajustado', 'CALC_AV_TOTAL_AJUSTADO': 'calc_av_total_ajustado',
        'FRONT25_VAL_TER': 'front25_valor_terreno', 'FRONT25_VAL_CON': 'front25_valor_construcao', 'FRONT25_USER': 'front25_usuario',
        'sc_SETOR': 'sc_setor', 'sc_DV': 'sc_dv', 'sc_GRUPO': 'sc_grupo', 'sc_TAMANHO_TESTADA': 'sc_tamanho_testada',
        'sc_TAMANHO_PROFUNDIDADE': 'sc_tamanho_profundidade', 'sc_VALOR_PADRAO': 'sc_valor_padrao',
        'sc_AREA_PADRAO': 'sc_area_padrao', 'sc_SC_VALOR_M2': 'sc_valor_m2', 'C22_pop_2010': 'censo_pop_2010',
        'C_pop_2022': 'censo_pop_2022', 'C_dom_2010': 'censo_dom_2010', 'C_dom_2022': 'censo_dom_2022',
        'C_dd_2010': 'censo_dd_2010', 'C_dd_2022': 'censo_dd_2022', 'C_tgmca_2010': 'censo_tgmca_2010',
        'C_tgmca_2022': 'censo_tgmca_2022', 'C_REND_NOMIN': 'censo_renda_nominal', 'C_REND_SM202': 'censo_renda_sal_min_2022',
        'C_IVS': 'censo_ivs', 'C_VAR_VULNER': 'censo_variacao_vulnerabilidade', 'C_VAR_RENDA': 'censo_variacao_renda'
    }
    gdf.rename(columns=column_rename_map, inplace=True)

    # Lista final de colunas a serem mantidas, usando os novos nomes
    # Adicionamos as colunas numéricas criadas e a geometria
    final_columns = list(column_rename_map.values()) + [f'{c.lower()}_n' for c in columns_to_map] + ['geometry']
    
    # Filtra o DataFrame para manter apenas as colunas desejadas e existentes
    existing_final_columns = [col for col in final_columns if col in gdf.columns]
    gdf = gdf[existing_final_columns]

    return gdf
