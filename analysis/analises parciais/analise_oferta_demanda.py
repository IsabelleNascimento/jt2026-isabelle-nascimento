import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

DATA_DIR = 'data'
OCCUPANCY_RATE = 0.65
OUTPUT_DIR = 'graficos'

os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams['figure.dpi'] = 120
plt.rcParams['savefig.dpi'] = 120
sns.set_style('whitegrid')
sns.set_palette('viridis')

def load_data():
    details = pd.read_csv(f'{DATA_DIR}/Details_Itapema.csv')
    prices = pd.read_csv(f'{DATA_DIR}/Price_AV_Itapema.csv')
    mesh = pd.read_csv(f'{DATA_DIR}/Mesh_Ids_Data_Itapema.csv')
    hosts = pd.read_csv(f'{DATA_DIR}/Hosts_ids_Itapema.csv')
    vivareal = pd.read_csv(f'{DATA_DIR}/VivaReal_Itapema.csv')
    return details, prices, mesh, hosts, vivareal

def merge_data(details, prices, mesh, hosts):
    prices['date'] = pd.to_datetime(prices['date'])
    price_agg = prices.groupby('airbnb_listing_id').agg(
        avg_daily_price=('price', 'mean'),
        days_listed=('price', 'count'),
        price_std=('price', 'std')
    ).reset_index()
    price_agg['price_std'] = price_agg['price_std'].fillna(0)

    df = details.merge(mesh[['airbnb_listing_id', 'suburb', 'latitude', 'longitude']],
                       on='airbnb_listing_id', how='left')
    df = df.merge(price_agg, on='airbnb_listing_id', how='inner')
    df = df.merge(hosts[['owner_id', 'is_superhost', 'star_rating_host', 'years_host']],
                  on='owner_id', how='left')

    df['monthly_revenue'] = df['avg_daily_price'] * 30 * OCCUPANCY_RATE
    df['annual_revenue'] = df['monthly_revenue'] * 12
    return df

def build_roi(df, vivareal):
    vr = vivareal[vivareal['sale_price'] > 100000].copy()
    vr_avg = vr.groupby(['suburb', 'bedrooms']).agg(
        preco_venda_medio=('sale_price', 'mean'),
        condominio_medio=('monthly_condo_fee', 'mean'),
        iptu_medio=('yearly_iptu', 'mean')
    ).reset_index().round(2)
    vr_avg = vr_avg.rename(columns={'bedrooms': 'number_of_bedrooms'})

    roi_df = df.merge(vr_avg[['suburb', 'number_of_bedrooms', 'preco_venda_medio',
                               'condominio_medio', 'iptu_medio']],
                      on=['suburb', 'number_of_bedrooms'], how='inner')
    roi_df = roi_df[roi_df['preco_venda_medio'] > 0].copy()

    roi_df['custos_anuais'] = (
        roi_df['condominio_medio'].fillna(0) * 12 +
        roi_df['iptu_medio'].fillna(0)
    )
    roi_df['receita_liquida'] = roi_df['annual_revenue'] - roi_df['custos_anuais']
    roi_df['roi_liquido'] = (roi_df['receita_liquida'] / roi_df['preco_venda_medio'] * 100).round(2)
    roi_df['payback_anos'] = (roi_df['preco_venda_medio'] / roi_df['receita_liquida']).round(1)
    return roi_df

def analyze_supply_demand(df, roi_df):
    print("\n" + "="*80)
    print("  OFERTA vs DEMANDA POR BAIRRO")
    print("="*80)

    # Supply: total listings per suburb
    supply = df.groupby('suburb').agg(
        total_imoveis=('airbnb_listing_id', 'count'),
        imoveis_unicos=('airbnb_listing_id', 'nunique'),
        preco_diario_medio=('avg_daily_price', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        quartos_media=('number_of_bedrooms', 'mean'),
        huespedes_media=('number_of_guests', 'mean')
    ).reset_index().round(2)

    # Demand proxies per suburb
    demand = df.groupby('suburb').agg(
        total_reviews=('number_of_reviews', 'sum'),
        reviews_por_imovel=('number_of_reviews', 'mean'),
        rating_medio=('star_rating', 'mean'),
        guest_satisfaction=('guest_satisfaction_overall', 'mean'),
        dias_listados_media=('days_listed', 'mean'),
        fotos_media=('picture_count', 'mean'),
        pct_superhost=('is_superhost', 'mean'),
        pct_instant_book=('can_instant_book', lambda x: (x == 'True').mean() if x.dtype == 'object' else x.mean())
    ).reset_index().round(2)

    # Merge supply + demand
    supply_demand = supply.merge(demand, on='suburb', how='inner')

    # Add ROI from roi_df
    roi_agg = roi_df.groupby('suburb').agg(
        roi_liquido_medio=('roi_liquido', 'mean'),
        payback_medio=('payback_anos', 'mean'),
        preco_venda_medio=('preco_venda_medio', 'mean')
    ).reset_index().round(2)

    supply_demand = supply_demand.merge(roi_agg, on='suburb', how='left')
    supply_demand = supply_demand.sort_values('roi_liquido_medio', ascending=False)

    # Demand index: normalized composite score
    for col in ['reviews_por_imovel', 'rating_medio', 'guest_satisfaction', 'dias_listados_media']:
        if col in supply_demand.columns:
            min_val = supply_demand[col].min()
            max_val = supply_demand[col].max()
            if max_val > min_val:
                supply_demand[f'{col}_norm'] = ((supply_demand[col] - min_val) / (max_val - min_val) * 100).round(1)
            else:
                supply_demand[f'{col}_norm'] = 50

    supply_demand['indice_demanda'] = (
        supply_demand['reviews_por_imovel_norm'] * 0.35 +
        supply_demand['rating_medio_norm'] * 0.25 +
        supply_demand['guest_satisfaction_norm'] * 0.20 +
        supply_demand['dias_listados_media_norm'] * 0.20
    ).round(1)

    supply_demand['relacao_oferta_demanda'] = (
        supply_demand['total_imoveis'] / supply_demand['indice_demanda'].replace(0, 1)
    ).round(2)

    print("\n--- Tabela Completa: Oferta vs Demanda vs ROI ---")
    print(supply_demand[[
        'suburb', 'total_imoveis', 'reviews_por_imovel', 'rating_medio',
        'guest_satisfaction', 'dias_listados_media', 'indice_demanda',
        'relacao_oferta_demanda', 'roi_liquido_medio', 'payback_medio',
        'preco_venda_medio'
    ]].to_string(index=False))

    return supply_demand

def analyze_bedroom_demand(df, roi_df):
    print("\n" + "="*80)
    print("  OFERTA vs DEMANDA POR Nº DE QUARTOS")
    print("="*80)

    agg = df.groupby('number_of_bedrooms').agg(
        total_imoveis=('airbnb_listing_id', 'count'),
        reviews_por_imovel=('number_of_reviews', 'mean'),
        rating_medio=('star_rating', 'mean'),
        guest_satisfaction=('guest_satisfaction_overall', 'mean'),
        preco_diario_medio=('avg_daily_price', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        dias_listados_media=('days_listed', 'mean'),
        pct_superhost=('is_superhost', 'mean')
    ).reset_index().round(2)

    roi_agg = roi_df.groupby('number_of_bedrooms').agg(
        roi_liquido_medio=('roi_liquido', 'mean'),
        payback_medio=('payback_anos', 'mean'),
        preco_venda_medio=('preco_venda_medio', 'mean')
    ).reset_index().round(2)

    agg = agg.merge(roi_agg, on='number_of_bedrooms', how='left')
    agg = agg.sort_values('roi_liquido_medio', ascending=False)

    print("\n" + agg.to_string(index=False))
    return agg

def plot1_supply_demand_roi(supply_demand):
    valid = supply_demand[supply_demand['total_imoveis'] >= 10].copy()
    valid = valid.sort_values('roi_liquido_medio', ascending=False)

    fig, ax1 = plt.subplots(figsize=(14, 7))

    x = range(len(valid))
    width = 0.35

    bars1 = ax1.bar([i - width/2 for i in x], valid['total_imoveis'],
                    width, label='Total Imóveis (Oferta)', color='steelblue', edgecolor='black', alpha=0.8)
    bars2 = ax1.bar([i + width/2 for i in x], valid['indice_demanda'],
                    width, label='Índice Demanda (0-100)', color='coral', edgecolor='black', alpha=0.8)

    ax1.set_xlabel('Bairro', fontsize=12)
    ax1.set_ylabel('Qtd Imóveis / Índice Demanda', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(valid['suburb'], rotation=45, ha='right', fontsize=9)
    ax1.legend(loc='upper left', fontsize=10)

    ax2 = ax1.twinx()
    ax2.plot(x, valid['roi_liquido_medio'], color='green', marker='D', linewidth=2,
             markersize=8, label='ROI Líquido (%)')
    ax2.set_ylabel('ROI Líquido Médio (%)', fontsize=12, color='green')
    ax2.tick_params(axis='y', labelcolor='green')
    ax2.legend(loc='upper right', fontsize=10)

    for i, row in enumerate(valid.itertuples()):
        ax1.text(i - width/2, row.total_imoveis + 10, str(int(row.total_imoveis)),
                 ha='center', fontsize=8, fontweight='bold')
        ax1.text(i + width/2, row.indice_demanda + 1, f'{row.indice_demanda:.0f}',
                 ha='center', fontsize=8, fontweight='bold')

    ax1.set_title('Oferta vs Demanda vs ROI por Bairro (n ≥ 10)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/09_oferta_demanda_roi.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 09_oferta_demanda_roi.png")

def plot2_scatter_oferta_roi(supply_demand):
    valid = supply_demand[supply_demand['total_imoveis'] >= 5].copy()

    fig, ax = plt.subplots(figsize=(12, 7))
    scatter = ax.scatter(valid['total_imoveis'], valid['roi_liquido_medio'],
                         s=valid['indice_demanda'] * 5, c=valid['payback_medio'],
                         cmap='RdYlGn_r', alpha=0.7, edgecolors='black')

    for _, row in valid.iterrows():
        ax.annotate(row['suburb'], (row['total_imoveis'], row['roi_liquido_medio']),
                    fontsize=8, ha='center', va='bottom', fontweight='bold')

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Payback (anos)', fontsize=11)

    ax.set_title('Oferta (nº imóveis) vs ROI Líquido (tamanho = Índice Demanda, cor = Payback)',
                 fontsize=13, fontweight='bold')
    ax.set_xlabel('Total de Imóveis no Bairro (Oferta)', fontsize=12)
    ax.set_ylabel('ROI Líquido Médio (%)', fontsize=12)
    ax.axhline(y=10, color='red', linestyle='--', alpha=0.5, label='Referência 10%')
    ax.legend()
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/10_scatter_oferta_roi.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 10_scatter_oferta_roi.png")

def plot3_bedroom_demand_comparison(bed_agg):
    valid = bed_agg[bed_agg['number_of_bedrooms'] <= 6].copy()

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # Total imóveis
    axes[0].bar(valid['number_of_bedrooms'].astype(str), valid['total_imoveis'],
                color=sns.color_palette('Blues_d', len(valid)), edgecolor='black')
    axes[0].set_title('Total Imóveis (Oferta)', fontweight='bold')
    axes[0].set_xlabel('Quartos')
    for i, v in enumerate(valid['total_imoveis']):
        axes[0].text(i, v + 50, f'{int(v):,}', ha='center', fontsize=9, fontweight='bold')

    # Reviews por imóvel
    axes[1].bar(valid['number_of_bedrooms'].astype(str), valid['reviews_por_imovel'],
                color=sns.color_palette('Oranges_d', len(valid)), edgecolor='black')
    axes[1].set_title('Reviews por Imóvel (Demanda)', fontweight='bold')
    axes[1].set_xlabel('Quartos')
    for i, v in enumerate(valid['reviews_por_imovel']):
        axes[1].text(i, v + 0.2, f'{v:.1f}', ha='center', fontsize=9, fontweight='bold')

    # ROI
    axes[2].bar(valid['number_of_bedrooms'].astype(str), valid['roi_liquido_medio'],
                color=sns.color_palette('Greens_d', len(valid)), edgecolor='black')
    axes[2].set_title('ROI Líquido Médio (%)', fontweight='bold')
    axes[2].set_xlabel('Quartos')
    for i, v in enumerate(valid['roi_liquido_medio']):
        axes[2].text(i, v + 0.3, f'{v:.1f}%', ha='center', fontsize=9, fontweight='bold')

    plt.suptitle('Oferta vs Demanda vs ROI por Nº de Quartos', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/11_oferta_demanda_quartos.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 11_oferta_demanda_quartos.png")

def plot4_tension_map(supply_demand):
    valid = supply_demand[supply_demand['total_imoveis'] >= 10].copy()

    fig, ax = plt.subplots(figsize=(12, 7))

    scatter = ax.scatter(valid['total_imoveis'], valid['indice_demanda'],
                         s=valid['roi_liquido_medio'] * 15, c=valid['roi_liquido_medio'],
                         cmap='RdYlGn', alpha=0.7, edgecolors='black', vmin=0, vmax=30)

    for _, row in valid.iterrows():
        ax.annotate(row['suburb'], (row['total_imoveis'], row['indice_demanda']),
                    fontsize=9, ha='center', va='bottom', fontweight='bold')

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('ROI Líquido (%)', fontsize=11)

    # Quadrant lines
    med_x = valid['total_imoveis'].median()
    med_y = valid['indice_demanda'].median()
    ax.axvline(med_x, color='gray', linestyle=':', alpha=0.5)
    ax.axhline(med_y, color='gray', linestyle=':', alpha=0.5)

    ax.text(med_x * 1.5, med_y * 1.15, 'ALTA OFERTA\nALTA DEMANDA', fontsize=9,
            ha='center', color='green', fontweight='bold', alpha=0.7)
    ax.text(med_x * 0.4, med_y * 1.15, 'BAIXA OFERTA\nALTA DEMANDA', fontsize=9,
            ha='center', color='darkgreen', fontweight='bold', alpha=0.7)
    ax.text(med_x * 1.5, med_y * 0.7, 'ALTA OFERTA\nBAIXA DEMANDA', fontsize=9,
            ha='center', color='red', fontweight='bold', alpha=0.7)
    ax.text(med_x * 0.4, med_y * 0.7, 'BAIXA OFERTA\nBAIXA DEMANDA', fontsize=9,
            ha='center', color='gray', fontweight='bold', alpha=0.7)

    ax.set_title('Mapa de Tensão: Oferta vs Demanda (tamanho/cor = ROI)',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Total de Imóveis (Oferta)', fontsize=12)
    ax.set_ylabel('Índice de Demanda (0-100)', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/12_mapa_tensao.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 12_mapa_tensao.png")

if __name__ == "__main__":
    print("Carregando dados...")
    details, prices, mesh, hosts, vivareal = load_data()

    print("Construindo DataFrames...")
    df = merge_data(details, prices, mesh, hosts)
    roi_df = build_roi(df, vivareal)

    print(f"Imóveis com ROI: {len(roi_df)}\n")

    supply_demand = analyze_supply_demand(df, roi_df)
    bed_agg = analyze_bedroom_demand(df, roi_df)

    print(f"\nGerando gráficos...")
    plot1_supply_demand_roi(supply_demand)
    plot2_scatter_oferta_roi(supply_demand)
    plot3_bedroom_demand_comparison(bed_agg)
    plot4_tension_map(supply_demand)

    print("\nConcluído!")
