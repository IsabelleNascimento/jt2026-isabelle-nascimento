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

def parse_pet_policy(details):
    details = details.copy()
    details['permite_animais'] = details['house_rules'].apply(
        lambda x: 'Sim' if pd.notna(x) and 'Permitido animais' in str(x) else 'Não'
    )
    return details[['airbnb_listing_id', 'permite_animais']]

def analyze_listing_type(df):
    print("\n" + "="*80)
    print("  ANÁLISE POR TIPO DE ANÚNCIO (listing_type)")
    print("="*80)

    agg = df.groupby('listing_type').agg(
        qtd=('airbnb_listing_id', 'count'),
        pct=('airbnb_listing_id', lambda x: f"{len(x)/len(df)*100:.1f}%"),
        preco_diario_medio=('avg_daily_price', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        rating_medio=('star_rating', 'mean'),
        reviews_medio=('number_of_reviews', 'mean'),
        guest_satisfaction=('guest_satisfaction_overall', 'mean'),
        quartos_medio=('number_of_bedrooms', 'mean'),
        banheiros_medio=('number_of_bathrooms', 'mean'),
        huespedes_medio=('number_of_guests', 'mean'),
        pct_superhost=('is_superhost', 'mean'),
        pct_animais=('permite_animais', lambda x: (x == 'Sim').mean()),
        pct_favorito=('is_guest_favorite', 'mean'),
        dias_listados=('days_listed', 'mean')
    ).round(2).sort_values('receita_anual_media', ascending=False)
    print(agg.to_string())

    return agg

def analyze_type_by_bairro(df):
    print("\n" + "="*80)
    print("  TIPO DE ANÚNCIO POR BAIRRO (Top 5 bairros)")
    print("="*80)

    top_bairros = df['suburb'].value_counts().head(5).index
    df_top = df[df['suburb'].isin(top_bairros)]

    pivot = df_top.groupby(['suburb', 'listing_type']).agg(
        qtd=('airbnb_listing_id', 'count'),
        receita_media=('annual_revenue', 'mean'),
        roi_medio=('roi_liquido', 'mean')
    ).round(2)

    for bairro in top_bairros:
        print(f"\n--- {bairro} ---")
        print(pivot.loc[bairro].to_string() if bairro in pivot.index else "  Sem dados")

    return pivot

def analyze_type_by_bedrooms(df):
    print("\n" + "="*80)
    print("  TIPO DE ANÚNCIO POR Nº DE QUARTOS")
    print("="*80)

    df_valid = df[df['number_of_bedrooms'] <= 5].copy()
    pivot = df_valid.groupby(['number_of_bedrooms', 'listing_type']).agg(
        qtd=('airbnb_listing_id', 'count'),
        receita_media=('annual_revenue', 'mean'),
        roi_medio=('roi_liquido', 'mean'),
        preco_venda=('preco_venda_medio', 'mean')
    ).round(2)

    print(pivot.to_string())
    return pivot

def plot1_listing_type_overview(df):
    order = df['listing_type'].value_counts().index.tolist()

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    palette = sns.color_palette('Set2', len(order))

    # Quantidade
    sns.countplot(data=df, x='listing_type', order=order, hue='listing_type',
                  palette=palette, ax=axes[0, 0], edgecolor='black', legend=False)
    axes[0, 0].set_title('Distribuição de Imóveis', fontweight='bold')
    axes[0, 0].set_xlabel('Tipo de Anúncio')
    for p in axes[0, 0].patches:
        axes[0, 0].annotate(f'{int(p.get_height()):,}',
                            (p.get_x() + p.get_width()/2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Receita Anual
    sns.barplot(data=df, x='listing_type', y='annual_revenue', order=order,
                hue='listing_type', palette=palette, ax=axes[0, 1], edgecolor='black',
                legend=False, estimator='mean')
    axes[0, 1].set_title('Receita Anual Média', fontweight='bold')
    axes[0, 1].set_xlabel('Tipo de Anúncio')
    axes[0, 1].set_ylabel('R$')
    for p in axes[0, 1].patches:
        axes[0, 1].annotate(f'R${p.get_height():,.0f}',
                            (p.get_x() + p.get_width()/2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Preço Diário
    sns.barplot(data=df, x='listing_type', y='avg_daily_price', order=order,
                hue='listing_type', palette=palette, ax=axes[1, 0], edgecolor='black',
                legend=False, estimator='mean')
    axes[1, 0].set_title('Preço Diário Médio', fontweight='bold')
    axes[1, 0].set_xlabel('Tipo de Anúncio')
    axes[1, 0].set_ylabel('R$')
    for p in axes[1, 0].patches:
        axes[1, 0].annotate(f'R${p.get_height():,.0f}',
                            (p.get_x() + p.get_width()/2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Rating
    sns.barplot(data=df, x='listing_type', y='star_rating', order=order,
                hue='listing_type', palette=palette, ax=axes[1, 1], edgecolor='black',
                legend=False, estimator='mean')
    axes[1, 1].set_title('Rating Médio', fontweight='bold')
    axes[1, 1].set_xlabel('Tipo de Anúncio')
    axes[1, 1].set_ylim(3.5, 5.2)
    for p in axes[1, 1].patches:
        axes[1, 1].annotate(f'{p.get_height():.2f}',
                            (p.get_x() + p.get_width()/2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Panorama por Tipo de Anúncio', fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/17_tipo_anuncio_overview.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 17_tipo_anuncio_overview.png")

def plot2_type_roi(df):
    agg = df.groupby('listing_type').agg(
        roi=('roi_liquido', 'mean'),
        payback=('payback_anos', 'mean'),
        receita=('annual_revenue', 'mean'),
        preco_venda=('preco_venda_medio', 'mean'),
        qtd=('airbnb_listing_id', 'count')
    ).round(2).sort_values('roi', ascending=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    palette = sns.color_palette('RdYlGn_r', len(agg))

    axes[0].barh(agg.index, agg['roi'], color=palette, edgecolor='black')
    for i, row in enumerate(agg.itertuples()):
        axes[0].text(row.roi + 0.2, i, f'{row.roi}%', va='center', fontsize=10, fontweight='bold')
    axes[0].set_title('ROI Líquido Médio por Tipo', fontweight='bold')
    axes[0].set_xlabel('ROI Líquido (%)')
    axes[0].axvline(x=10, color='red', linestyle='--', alpha=0.5)

    axes[1].barh(agg.index, agg['payback'], color=palette, edgecolor='black')
    for i, row in enumerate(agg.itertuples()):
        axes[1].text(row.payback + 0.2, i, f'{row.payback}a', va='center', fontsize=10, fontweight='bold')
    axes[1].set_title('Payback Médio por Tipo', fontweight='bold')
    axes[1].set_xlabel('Payback (anos)')

    plt.suptitle('ROI e Payback por Tipo de Anúncio', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/18_tipo_roi_payback.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 18_tipo_roi_payback.png")

def plot3_type_by_bairro(df):
    top_bairros = df['suburb'].value_counts().head(5).index.tolist()
    df_top = df[df['suburb'].isin(top_bairros)]

    pivot = df_top.groupby(['suburb', 'listing_type'])['annual_revenue'].mean().reset_index()
    pivot = pivot.pivot(index='suburb', columns='listing_type', values='annual_revenue') / 1000

    fig, ax = plt.subplots(figsize=(12, 6))
    pivot.plot(kind='bar', ax=ax, edgecolor='black', width=0.8)
    ax.set_title('Receita Anual Média (R$ mil) por Tipo de Anúncio e Bairro', fontsize=13, fontweight='bold')
    ax.set_xlabel('Bairro', fontsize=12)
    ax.set_ylabel('Receita Anual (R$ mil)', fontsize=12)
    ax.legend(title='Tipo', fontsize=9)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/19_tipo_por_bairro.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 19_tipo_por_bairro.png")

def plot4_type_heatmap_bathrooms(df):
    df_valid = df[df['number_of_bathrooms'] <= 5].copy()
    pivot = df_valid.groupby(['listing_type', 'number_of_bathrooms'])['annual_revenue'].mean().reset_index()
    pivot = pivot.pivot(index='listing_type', columns='number_of_bathrooms', values='annual_revenue') / 1000

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(pivot, annot=True, fmt='.0f', cmap='YlOrRd', linewidths=0.5, ax=ax,
                cbar_kws={'label': 'Receita Anual (R$ mil)'})
    ax.set_title('Receita Anual (R$ mil): Tipo x Banheiros', fontsize=13, fontweight='bold')
    ax.set_xlabel('Nº de Banheiros', fontsize=12)
    ax.set_ylabel('Tipo de Anúncio', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/20_heatmap_tipo_banheiros.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 20_heatmap_tipo_banheiros.png")

if __name__ == "__main__":
    print("Carregando dados...")
    details, prices, mesh, hosts, vivareal = load_data()

    print("Preparando dados...")
    df = merge_data(details, prices, mesh, hosts)

    pets = parse_pet_policy(details)
    df = df.merge(pets, on='airbnb_listing_id', how='left')
    df['permite_animais'] = df['permite_animais'].fillna('Não')

    roi_df = build_roi(df, vivareal)
    df = df.merge(roi_df[['airbnb_listing_id', 'roi_liquido', 'payback_anos', 'preco_venda_medio']],
                  on='airbnb_listing_id', how='left')

    print(f"Total de imóveis: {len(df)}")

    type_agg = analyze_listing_type(df)
    type_bairro = analyze_type_by_bairro(df)
    type_bed = analyze_type_by_bedrooms(df)

    print(f"\nGerando gráficos...")
    plot1_listing_type_overview(df)
    plot2_type_roi(df)
    plot3_type_by_bairro(df)
    plot4_type_heatmap_bathrooms(df)

    print("\nConcluído!")
