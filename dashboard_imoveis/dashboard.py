import pandas as pd
import geopandas as gpd
import streamlit as st

# O @st.cache_data é o segredo para a performance do seu dashboard!
# Ele garante que o processamento pesado só aconteça uma vez.
@st.cache_data
def carregar_e_processar_dados(caminho_arquivo_parquet):
    """
    Função responsável por ler o arquivo Parquet e aplicar as regras de negócio.
    Agora otimizada para carregar apenas as colunas necessárias com a função correta.
    """
    print("EXECUTANDO A CARGA E PROCESSAMENTO OTIMIZADO DOS DADOS...")

    # --- OTIMIZAÇÃO DE MEMÓRIA ---
    # Lista de colunas a serem carregadas do arquivo Parquet.
    colunas_necessarias = [
        # Colunas ativas no Dashboard
        'tiqimo_NOMEBAIRRO',
        'tiqimo_USOIMOVEL',
        'tiqimo_VALORTOTALLOTE',
        'TAXA_PSEI_AJUSTADO',
        'TAXA_PSEI_PARC_CORR',
        
        # Colunas necessárias para cálculos internos (mapeamento PSEI)
        'PSEI_AJUSTADO',
        'PSEI_RECLASS_80',
        'PSEI_PARC_CORRIGIDO',

        # Colunas para o novo cálculo de IPTU
        'tiqimo_AVALIACAO',
        'tiqimo_ALIQUOTA',
        'COBRAR',

        # --- Colunas Adicionais (comentadas por padrão) ---
        # 'INSCANT',
        # 'tiqimo_NOMEREGIAO',
        # 'tiqimo_PARCELAMEN',
        # 'tiqimo_PROPRIETAR',
        # 'tiqimo_COMPROMISS',
        # 'tiqimo_ADMINISTRA',
        # 'tiqimo_TAXACAO',
        # 'tiqimo_DESCRICAOT',
        # 'tiqimo_VALORVENAL',
        # 'tiqimo_FRACAOIDEA',
        # 'tiqimo_AREATERREN',
        # 'tiqimo_AREAEDIFICIMOVEL',
        # 'tiqimo_VALORCONST',
        # 'tiqimo_VALORTERRENOLOTE',
        # 'tiqimo_VALOREDIFICLOTE',
        # 'PRECISAO',
        # 'TAXA_PSEI_RECLASS_80',
        # 'GLEBAS_CATEG',
        # 'CALC_NOME_CONDOMINIO',
        # 'CALC_VU_MEDIO',
        # 'CALC_VU_MEDIO_AJUSTADO',
        # 'CALC_AV_TERRENO_AJUSTADO',
        # 'CALC_AV_TOTAL_AJUSTADO',
        # 'sc_SETOR',
        # 'sc_GRUPO',
        # 'sc_TAMANHO_TESTADA',
        # 'sc_TAMANHO_PROFUNDIDADE',
        # 'sc_VALOR_PADRAO',
        # 'sc_AREA_PADRAO',
        # 'sc_SC_VALOR_M2',
        # 'C_pop_2022',
        # 'C_dom_2022',
        # 'C_dd_2022',
        # 'C_tgmca_2022',
        # 'C_REND_NOMIN',
        # 'C_REND_SM202',
        # 'C_IVS',
        # 'C_VAR_RENDA',
    ]

    try:
        # CORREÇÃO: Usando pd.read_parquet, pois não estamos lendo a coluna de geometria.
        df = pd.read_parquet(caminho_arquivo_parquet, columns=colunas_necessarias)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Parquet: {e}")
        return pd.DataFrame()

    # --- Mapeamento de categorias PSEI para valores numéricos ---
    def map_psei_category_to_numeric(category):
        mapping = {
            'BI': 1, 'BM': 2, 'BS': 3, 'NI': 4, 'NM': 5,
            'NS': 6, 'AI': 7, 'AM': 8, 'AS': 9
        }
        return mapping.get(category, None)

    # Atualiza a lista de colunas a serem mapeadas com base nas colunas disponíveis
    columns_to_map = [
        'PSEI_AJUSTADO',
        'PSEI_RECLASS_80',
        'PSEI_PARC_CORRIGIDO',
    ]

    for col in columns_to_map:
        new_col_name = f'{col.lower()}_n'
        if col in df.columns:
            df[new_col_name] = df[col].apply(map_psei_category_to_numeric)

    # --- Renomeando colunas para nomes mais amigáveis ---
    column_rename_map = {
        'INSCANT': 'inscant', 'tiqimo_NOMEREGIAO': 'nome_regiao', 'tiqimo_NOMEBAIRRO': 'nome_bairro', 'tiqimo_PARCELAMEN': 'parcelamento',
        'tiqimo_PROPRIETAR': 'proprietario', 'tiqimo_COMPROMISS': 'compromissario', 'tiqimo_ADMINISTRA': 'administrador',
        'tiqimo_TAXACAO': 'taxacao', 'tiqimo_DESCRICAOT': 'descricao_tax',
        'tiqimo_USOIMOVEL': 'uso_imovel', 'tiqimo_VALORVENAL': 'valor_venal_sc',
        'tiqimo_FRACAOIDEA': 'fracao_ideal',
        'tiqimo_AREATERREN': 'area_terreno', 'tiqimo_AREAEDIFICIMOVEL': 'area_edificada_imovel',
        'tiqimo_VALORCONST': 'valor_construcao', 'tiqimo_AVALIACAO': 'avaliacao', 'tiqimo_VALORTERRENOLOTE': 'valor_terreno_lote',
        'tiqimo_VALOREDIFICLOTE': 'valor_edificacao_lote', 'tiqimo_VALORTOTALLOTE': 'valor_total_lote', 'tiqimo_ALIQUOTA': 'aliquota',
        'PRECISAO': 'precisao', 'COBRAR': 'cobrar',
        'PSEI_AJUSTADO': 'psei_ajustado', 'TAXA_PSEI_AJUSTADO': 'taxa_psei_ajustado',
        'PSEI_RECLASS_80': 'psei_reclassificado_80', 'TAXA_PSEI_RECLASS_80': 'taxa_psei_reclassificado_80',
        'GLEBAS_CATEG': 'glebas_categ',
        'PSEI_PARC_CORRIGIDO': 'psei_parcelamento_corrigido', 'TAXA_PSEI_PARC_CORR': 'taxa_psei_parcelamento_corrigido',
        'CALC_NOME_CONDOMINIO': 'calc_nome_condominio', 'CALC_VU_MEDIO': 'calc_vu_medio', 'CALC_VU_MEDIO_AJUSTADO': 'calc_vu_medio_ajustado',
        'CALC_AV_TERRENO_AJUSTADO': 'calc_av_terreno_ajustado', 'CALC_AV_TOTAL_AJUSTADO': 'calc_av_total_ajustado',
        'sc_SETOR': 'sc_setor', 'sc_GRUPO': 'sc_grupo', 'sc_TAMANHO_TESTADA': 'sc_tamanho_testada',
        'sc_TAMANHO_PROFUNDIDADE': 'sc_tamanho_profundidade', 'sc_VALOR_PADRAO': 'sc_valor_padrao',
        'sc_AREA_PADRAO': 'sc_area_padrao', 'sc_SC_VALOR_M2': 'sc_valor_m2',
        'C_pop_2022': 'censo_pop_2022', 'C_dom_2022': 'censo_dom_2022', 'C_dd_2022': 'censo_dd_2022',
        'C_tgmca_2022': 'censo_tgmca_2022', 'C_REND_NOMIN': 'censo_renda_nom_2022', 'C_REND_SM202': 'censo_renda_sal_min_2022',
        'C_IVS': 'censo_ivs', 'C_VAR_RENDA': 'censo_variacao_renda',
    }
    df = df.rename(columns=column_rename_map)

    # --- CÁLCULO DO IPTU ---
    # Garantir que as colunas numéricas não tenham valores nulos que possam quebrar o cálculo
    df['avaliacao'] = pd.to_numeric(df['avaliacao'], errors='coerce').fillna(0)
    df['aliquota'] = pd.to_numeric(df['aliquota'], errors='coerce').fillna(0)
    
    # Inicializa a coluna com zero
    df['iptu_calculado'] = 0.0
    # Calcula o IPTU apenas onde 'cobrar' for True. A alíquota é dividida por 100.
    # Usamos .loc para garantir que a atribuição seja feita corretamente.
    df.loc[df['cobrar'] == True, 'iptu_calculado'] = df['avaliacao'] * (df['aliquota'] / 100)


    return df
