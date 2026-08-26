import pandas as pd
import numpy as np
import os

pd.reset_option('display.max_columns')
pd.reset_option('display.width')
pd.reset_option('display.max_rows')

DATA_DIR = 'data'
OCCUPANCY_RATE = 0.65

def load_data():
    details = pd.read_csv(f'{DATA_DIR}/Details_Itapema.csv')
    prices = pd.read_csv(f'{DATA_DIR}/Price_AV_Itapema.csv')
    mesh = pd.read_csv(f'{DATA_DIR}/Mesh_Ids_Data_Itapema.csv')
    hosts = pd.read_csv(f'{DATA_DIR}/Hosts_ids_Itapema.csv')
    vivareal = pd.read_csv(f'{DATA_DIR}/VivaReal_Itapema.csv')
    return details, prices, mesh, hosts, vivareal

def merge_data(details, prices, mesh, hosts):
    # Aggregate prices per listing
    prices['date'] = pd.to_datetime(prices['date'])
    price_agg = prices.groupby('airbnb_listing_id').agg(
        avg_daily_price=('price', 'mean'),
        median_daily_price=('price', 'median'),
        min_daily_price=('price', 'min'),
        max_daily_price=('price', 'max'),
        days_listed=('price', 'count'),
        price_std=('price', 'std')
    ).reset_index()
    price_agg['price_std'] = price_agg['price_std'].fillna(0)

    # Merge details + mesh + price_agg
    df = details.merge(mesh[['airbnb_listing_id', 'suburb', 'latitude', 'longitude']],
                       on='airbnb_listing_id', how='left')
    df = df.merge(price_agg, on='airbnb_listing_id', how='inner')
    df = df.merge(hosts[['owner_id', 'is_superhost', 'star_rating_host', 'years_host']],
                  on='owner_id', how='left')

    # Revenue estimates
    df['monthly_revenue'] = df['avg_daily_price'] * 30 * OCCUPANCY_RATE
    df['annual_revenue'] = df['monthly_revenue'] * 12

    return df

def analyze_revenue_by_suburb(df):
    print("\n" + "="*70)
    print("  RECEITA POR BAIRRO")
    print("="*70)
    agg = df.groupby('suburb').agg(
        qtd_imoveis=('airbnb_listing_id', 'count'),
        preco_diario_medio=('avg_daily_price', 'mean'),
        receita_mensal_media=('monthly_revenue', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        receita_anual_mediana=('annual_revenue', 'median'),
        qtd_quartos_media=('number_of_bedrooms', 'mean'),
        rating_medio=('star_rating', 'mean')
    ).round(2).sort_values('receita_anual_media', ascending=False)
    print(agg.to_string())
    return agg

def analyze_revenue_by_bedrooms(df):
    print("\n" + "="*70)
    print("  RECEITA POR NÚMERO DE QUARTOS")
    print("="*70)
    agg = df.groupby('number_of_bedrooms').agg(
        qtd_imoveis=('airbnb_listing_id', 'count'),
        preco_diario_medio=('avg_daily_price', 'mean'),
        receita_mensal_media=('monthly_revenue', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        rating_medio=('star_rating', 'mean'),
        review_medio=('number_of_reviews', 'mean')
    ).round(2).sort_values('receita_anual_media', ascending=False)
    print(agg.to_string())
    return agg

def analyze_revenue_by_listing_type(df):
    print("\n" + "="*70)
    print("  RECEITA POR TIPO DE IMÓVEL")
    print("="*70)
    agg = df.groupby('listing_type').agg(
        qtd_imoveis=('airbnb_listing_id', 'count'),
        preco_diario_medio=('avg_daily_price', 'mean'),
        receita_mensal_media=('monthly_revenue', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        rating_medio=('star_rating', 'mean')
    ).round(2).sort_values('receita_anual_media', ascending=False)
    print(agg.to_string())
    return agg

def analyze_top_features(df):
    print("\n" + "="*70)
    print("  TOP 20 IMÓVEIS POR RECEITA ANUAL")
    print("="*70)
    top = df.nlargest(20, 'annual_revenue')[
        ['airbnb_listing_id', 'ad_name', 'suburb', 'number_of_bedrooms',
         'number_of_bathrooms', 'number_of_guests', 'avg_daily_price',
         'annual_revenue', 'star_rating', 'number_of_reviews', 'is_superhost']
    ].round(2)
    print(top.to_string(index=False))
    return top

def analyze_superhost_impact(df):
    print("\n" + "="*70)
    print("  IMPACTO DO SUPERHOST NA RECEITA")
    print("="*70)
    agg = df.groupby('is_superhost').agg(
        qtd_imoveis=('airbnb_listing_id', 'count'),
        preco_diario_medio=('avg_daily_price', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        rating_medio=('star_rating', 'mean'),
        reviews_medio=('number_of_reviews', 'mean')
    ).round(2)
    print(agg.to_string())
    return agg

def analyze_roi(df, vivareal):
    print("\n" + "="*70)
    print("  ANÁLISE DE ROI - CRUZAMENTO AIRBNB x VENDA (VivaReal)")
    print("="*70)

    # Average sale price per suburb + bedrooms from VivaReal
    vr = vivareal[vivareal['sale_price'] > 100000].copy()
    vr_avg = vr.groupby(['suburb', 'bedrooms']).agg(
        preco_venda_medio=('sale_price', 'mean'),
        preco_venda_mediana=('sale_price', 'median'),
        qtd_vendas=('listing_id', 'count'),
        area_media=('usable_area', 'mean'),
        condominio_medio=('monthly_condo_fee', 'mean'),
        iptu_medio=('yearly_iptu', 'mean')
    ).reset_index().round(2)

    # Rename to match df columns for merge
    vr_avg = vr_avg.rename(columns={'bedrooms': 'number_of_bedrooms'})

    # Merge with revenue data
    roi_df = df.merge(vr_avg[['suburb', 'number_of_bedrooms', 'preco_venda_medio',
                               'preco_venda_mediana', 'area_media', 'condominio_medio', 'iptu_medio']],
                      on=['suburb', 'number_of_bedrooms'], how='inner')

    # Filter valid data
    roi_df = roi_df[roi_df['preco_venda_medio'] > 0].copy()

    # ROI calculations
    roi_df['custos_anuais_estimados'] = (
        roi_df['condominio_medio'].fillna(0) * 12 +
        roi_df['iptu_medio'].fillna(0)
    )
    roi_df['receita_liquida_anual'] = roi_df['annual_revenue'] - roi_df['custos_anuais_estimados']
    roi_df['roi_bruto'] = (roi_df['annual_revenue'] / roi_df['preco_venda_medio'] * 100).round(2)
    roi_df['roi_liquido'] = (roi_df['receita_liquida_anual'] / roi_df['preco_venda_medio'] * 100).round(2)
    roi_df['payback_anos'] = (roi_df['preco_venda_medio'] / roi_df['receita_liquida_anual']).round(1)

    # ROI Summary by suburb
    print("\n--- ROI por Bairro ---")
    roi_summary = roi_df.groupby('suburb').agg(
        qtd_imoveis=('airbnb_listing_id', 'count'),
        preco_venda_medio=('preco_venda_medio', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        custos_anuais_medio=('custos_anuais_estimados', 'mean'),
        receita_liquida_media=('receita_liquida_anual', 'mean'),
        roi_bruto_medio=('roi_bruto', 'mean'),
        roi_liquido_medio=('roi_liquido', 'mean'),
        payback_medio=('payback_anos', 'mean')
    ).round(2).sort_values('roi_liquido_medio', ascending=False)
    print(roi_summary.to_string())

    # ROI Summary by bedrooms
    print("\n--- ROI por Número de Quartos ---")
    roi_bed = roi_df.groupby('number_of_bedrooms').agg(
        qtd_imoveis=('airbnb_listing_id', 'count'),
        preco_venda_medio=('preco_venda_medio', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        roi_bruto_medio=('roi_bruto', 'mean'),
        roi_liquido_medio=('roi_liquido', 'mean'),
        payback_medio=('payback_anos', 'mean')
    ).round(2).sort_values('roi_liquido_medio', ascending=False)
    print(roi_bed.to_string())

    # Top 15 best ROI opportunities
    print("\n--- TOP 15 MELHORES OPORTUNIDADES DE ROI ---")
    top_roi = roi_df.nlargest(15, 'roi_liquido')[
        ['airbnb_listing_id', 'ad_name', 'suburb', 'number_of_bedrooms',
         'preco_venda_medio', 'annual_revenue', 'receita_liquida_anual',
         'roi_bruto', 'roi_liquido', 'payback_anos']
    ].round(2)
    print(top_roi.to_string(index=False))

    return roi_df, vr_avg

def investment_recommendation(df, roi_df):
    print("\n" + "="*70)
    print("  RECOMENDAÇÃO DE INVESTIMENTO - SEAZONE")
    print("="*70)

    # Best profile by bedrooms
    best_bed = roi_df.groupby('number_of_bedrooms').agg(
        roi_liquido=('roi_liquido', 'mean'),
        payback=('payback_anos', 'mean'),
        qtd=('airbnb_listing_id', 'count')
    ).round(2).sort_values('roi_liquido', ascending=False).iloc[0]

    # Best suburb
    best_suburb = roi_df.groupby('suburb').agg(
        roi_liquido=('roi_liquido', 'mean'),
        payback=('payback_anos', 'mean'),
        receita=('annual_revenue', 'mean'),
        preco=('preco_venda_medio', 'mean'),
        qtd=('airbnb_listing_id', 'count')
    ).round(2).sort_values('roi_liquido', ascending=False).iloc[0]

    # Best listing type
    best_type = roi_df.groupby('listing_type').agg(
        roi_liquido=('roi_liquido', 'mean'),
        payback=('payback_anos', 'mean'),
        qtd=('airbnb_listing_id', 'count')
    ).round(2).sort_values('roi_liquido', ascending=False).iloc[0]

    print(f"""
PERFIL IDEAL DE INVESTIMENTO:
-----------------------------------------------
  Melhor bairro:        {best_suburb.name}
  Melhor tipo:          {best_type.name}
  Melhor nº quartos:    {int(best_bed.name)}

MÉTRICAS ESPERADAS:
-----------------------------------------------
  ROI Líquido Anual:    {best_suburb['roi_liquido']:.1f}%
  Payback:              {best_suburb['payback']:.1f} anos
  Receita Anual Média:  R$ {best_suburb['receita']:,.0f}
  Preço de Venda Médio: R$ {best_suburb['preco']:,.0f}

CONTEXTO GERAL ITAPEMA:
-----------------------------------------------
  Total de imóveis analisados: {len(df)}
  Total com ROI calculado:     {len(roi_df)}
  Receita anual média geral:   R$ {df['annual_revenue'].mean():,.0f}
  Preço diário médio geral:    R$ {df['avg_daily_price'].mean():,.0f}
  Taxa de ocupação assumida:   {OCCUPANCY_RATE*100:.0f}%

RECOMENDAÇÃO:
-----------------------------------------------
  A Seazone deveria priorizar imóveis de {int(best_bed.name)} quarto(es)
  na região de {best_suburb.name}, do tipo {best_type.name},
  com potencial de ROI líquido de {best_suburb['roi_liquido']:.1f}% ao ano
  e payback de {best_suburb['payback']:.1f} anos.
""")

if __name__ == "__main__":
    print("Carregando dados...")
    details, prices, mesh, hosts, vivareal = load_data()

    print("Realizando joins e estimativas de receita...")
    df = merge_data(details, prices, mesh, hosts)

    print(f"Total de imóveis com dados de preço: {len(df)}")

    suborb_agg = analyze_revenue_by_suburb(df)
    bed_agg = analyze_revenue_by_bedrooms(df)
    type_agg = analyze_revenue_by_listing_type(df)
    top_df = analyze_top_features(df)
    superhost_df = analyze_superhost_impact(df)
    roi_df, vr_avg = analyze_roi(df, vivareal)
    investment_recommendation(df, roi_df)

    print("Análise concluída!")
