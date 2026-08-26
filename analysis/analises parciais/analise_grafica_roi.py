import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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
        median_daily_price=('price', 'median'),
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

    # Truncate extreme values for visualization
    roi_df['roi_liquido_plot'] = roi_df['roi_liquido'].clip(upper=100)
    roi_df['payback_plot'] = roi_df['payback_anos'].clip(upper=40)

    return roi_df

def plot1_scatter_roi_payback(roi_df):
    fig, ax = plt.subplots(figsize=(14, 7))
    sns.scatterplot(
        data=roi_df, x='payback_anos', y='roi_liquido',
        hue='number_of_bedrooms', size='preco_venda_medio',
        sizes=(20, 300), alpha=0.5, palette='viridis', ax=ax
    )
    ax.set_title('ROI Líquido vs Payback por Nº de Quartos', fontsize=16, fontweight='bold')
    ax.set_xlabel('Payback (anos)', fontsize=12)
    ax.set_ylabel('ROI Líquido (% a.a.)', fontsize=12)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 50)
    ax.legend(title='Quartos / Preço Venda', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/01_scatter_roi_payback.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 01_scatter_roi_payback.png")

def plot2_roi_by_bedrooms(roi_df):
    agg = roi_df.groupby('number_of_bedrooms').agg(
        roi_medio=('roi_liquido', 'mean'),
        roi_mediana=('roi_liquido', 'median'),
        payback_medio=('payback_anos', 'mean'),
        qtd=('airbnb_listing_id', 'count')
    ).reset_index().round(2)
    agg = agg[agg['number_of_bedrooms'] <= 6]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    bars = ax1.bar(agg['number_of_bedrooms'].astype(str), agg['roi_medio'],
                   color=sns.color_palette('viridis', len(agg)), edgecolor='black', alpha=0.85)
    ax1.set_title('ROI Líquido Médio por Nº de Quartos', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Nº de Quartos', fontsize=12)
    ax1.set_ylabel('ROI Líquido Médio (%)', fontsize=12)

    ax2 = ax1.twinx()
    ax2.plot(agg['number_of_bedrooms'].astype(str), agg['payback_medio'],
             color='red', marker='o', linewidth=2, label='Payback (anos)')
    ax2.set_ylabel('Payback Médio (anos)', fontsize=12, color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    ax2.legend(loc='upper right')

    for i, row in agg.iterrows():
        ax1.text(i, row['roi_medio'] + 0.3, f"{row['roi_medio']}%", ha='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/02_roi_por_quartos.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 02_roi_por_quartos.png")

def plot3_roi_by_suburb(roi_df):
    agg = roi_df.groupby('suburb').agg(
        roi_medio=('roi_liquido', 'mean'),
        payback_medio=('payback_anos', 'mean'),
        qtd=('airbnb_listing_id', 'count'),
        preco_medio=('preco_venda_medio', 'mean')
    ).reset_index().round(2)
    agg = agg[agg['qtd'] >= 10].sort_values('roi_medio', ascending=True)

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = sns.color_palette('RdYlGn', len(agg))
    bars = ax.barh(agg['suburb'], agg['roi_medio'], color=colors, edgecolor='black', alpha=0.85)

    for bar, row in zip(bars, agg.itertuples()):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f"  ROI: {row.roi_medio}%  |  Payback: {row.payback_medio}a  |  n={row.qtd}",
                va='center', fontsize=9)

    ax.set_title('ROI Líquido Médio por Bairros (n ≥ 10 imóveis)', fontsize=14, fontweight='bold')
    ax.set_xlabel('ROI Líquido Médio (%)', fontsize=12)
    ax.axvline(x=10, color='red', linestyle='--', alpha=0.5, label='Referência 10%')
    ax.legend()
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/03_roi_por_bairro.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 03_roi_por_bairro.png")

def plot4_heatmap_roi_bedrooms_suburb(roi_df):
    roi_filtered = roi_df[roi_df['number_of_bedrooms'] <= 5].copy()
    pivot = roi_filtered.groupby(['suburb', 'number_of_bedrooms'])['roi_liquido'].mean().reset_index()
    pivot = pivot.pivot(index='suburb', columns='number_of_bedrooms', values='roi_liquido')

    # Filter rows with enough data
    counts = roi_filtered.groupby('suburb')['airbnb_listing_id'].count()
    valid = counts[counts >= 10].index
    pivot = pivot.loc[pivot.index.isin(valid)]

    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', center=10,
                linewidths=0.5, ax=ax, cbar_kws={'label': 'ROI Líquido (%)'})
    ax.set_title('Heatmap: ROI Líquido (%) por Bairro x Nº de Quartos', fontsize=14, fontweight='bold')
    ax.set_xlabel('Nº de Quartos', fontsize=12)
    ax.set_ylabel('Bairro', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/04_heatmap_roi.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 04_heatmap_roi.png")

def plot5_payback_distribution(roi_df):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    roi_valid = roi_df[roi_df['payback_anos'] <= 30]

    sns.histplot(roi_valid['payback_anos'], bins=30, kde=True, color='steelblue', ax=axes[0])
    axes[0].set_title('Distribuição do Payback (anos)', fontsize=13, fontweight='bold')
    axes[0].set_xlabel('Payback (anos)', fontsize=11)
    axes[0].set_ylabel('Frequência', fontsize=11)
    axes[0].axvline(roi_valid['payback_anos'].median(), color='red', linestyle='--',
                    label=f"Mediana: {roi_valid['payback_anos'].median()}a")
    axes[0].legend()

    sns.boxplot(data=roi_valid, x='number_of_bedrooms', y='payback_anos',
                palette='viridis', ax=axes[1])
    axes[1].set_title('Payback por Nº de Quartos', fontsize=13, fontweight='bold')
    axes[1].set_xlabel('Nº de Quartos', fontsize=11)
    axes[1].set_ylabel('Payback (anos)', fontsize=11)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/05_distribuicao_payback.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 05_distribuicao_payback.png")

def plot6_roi_vs_preco(roi_df):
    fig, ax = plt.subplots(figsize=(14, 7))
    scatter = ax.scatter(
        roi_df['preco_venda_medio'] / 1000, roi_df['roi_liquido'],
        c=roi_df['payback_anos'], cmap='RdYlGn_r', alpha=0.4, s=30, edgecolors='none'
    )
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Payback (anos)', fontsize=11)

    ax.set_title('ROI Líquido vs Preço de Venda (cor = Payback)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Preço de Venda Médio (R$ mil)', fontsize=12)
    ax.set_ylabel('ROI Líquido (%)', fontsize=12)
    ax.set_xlim(0, 5000)
    ax.set_ylim(0, 50)
    ax.axhline(y=10, color='red', linestyle='--', alpha=0.5, label='Referência 10%')
    ax.legend()
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/06_roi_vs_preco.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 06_roi_vs_preco.png")

def plot7_comparativo_cenarios(roi_df):
    cenarios = roi_df.groupby('number_of_bedrooms').agg(
        roi_medio=('roi_liquido', 'mean'),
        payback_medio=('payback_anos', 'mean'),
        receita_media=('annual_revenue', 'mean'),
        preco_medio=('preco_venda_medio', 'mean'),
        qtd=('airbnb_listing_id', 'count')
    ).reset_index().round(2)
    cenarios = cenarios[(cenarios['number_of_bedrooms'] <= 5) & (cenarios['qtd'] >= 10)]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # ROI
    axes[0, 0].bar(cenarios['number_of_bedrooms'].astype(str), cenarios['roi_medio'],
                   color=sns.color_palette('viridis', len(cenarios)), edgecolor='black')
    axes[0, 0].set_title('ROI Líquido Médio (%)', fontweight='bold')
    axes[0, 0].set_xlabel('Quartos')
    for i, v in enumerate(cenarios['roi_medio']):
        axes[0, 0].text(i, v + 0.2, f'{v}%', ha='center', fontsize=9, fontweight='bold')

    # Payback
    axes[0, 1].bar(cenarios['number_of_bedrooms'].astype(str), cenarios['payback_medio'],
                   color=sns.color_palette('magma', len(cenarios)), edgecolor='black')
    axes[0, 1].set_title('Payback Médio (anos)', fontweight='bold')
    axes[0, 1].set_xlabel('Quartos')
    for i, v in enumerate(cenarios['payback_medio']):
        axes[0, 1].text(i, v + 0.2, f'{v}a', ha='center', fontsize=9, fontweight='bold')

    # Receita Anual
    axes[1, 0].bar(cenarios['number_of_bedrooms'].astype(str), cenarios['receita_media'] / 1000,
                   color=sns.color_palette('YlOrRd', len(cenarios)), edgecolor='black')
    axes[1, 0].set_title('Receita Anual Média (R$ mil)', fontweight='bold')
    axes[1, 0].set_xlabel('Quartos')
    for i, v in enumerate(cenarios['receita_media'] / 1000):
        axes[1, 0].text(i, v + 1, f'R${v:.0f}k', ha='center', fontsize=9, fontweight='bold')

    # Preço Venda
    axes[1, 1].bar(cenarios['number_of_bedrooms'].astype(str), cenarios['preco_medio'] / 1000,
                   color=sns.color_palette('coolwarm', len(cenarios)), edgecolor='black')
    axes[1, 1].set_title('Preço Venda Médio (R$ mil)', fontweight='bold')
    axes[1, 1].set_xlabel('Quartos')
    for i, v in enumerate(cenarios['preco_medio'] / 1000):
        axes[1, 1].text(i, v + 20, f'R${v:.0f}k', ha='center', fontsize=9, fontweight='bold')

    plt.suptitle('Panorama Comparativo por Nº de Quartos', fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/07_panorama_quartos.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 07_panorama_quartos.png")

def plot8_superhost_roi(roi_df):
    agg = roi_df.groupby('is_superhost').agg(
        roi_medio=('roi_liquido', 'mean'),
        payback_medio=('payback_anos', 'mean'),
        qtd=('airbnb_listing_id', 'count')
    ).reset_index().round(2)

    fig, ax = plt.subplots(figsize=(8, 5))
    x = ['Não Superhost', 'Superhost']
    colors = ['#e74c3c', '#2ecc71']
    bars = ax.bar(x, agg['roi_medio'], color=colors, edgecolor='black', width=0.5)

    for bar, row in zip(bars, agg.itertuples()):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{row.roi_medio}%\nPayback: {row.payback_medio}a\nn={row.qtd}",
                ha='center', fontsize=10, fontweight='bold')

    ax.set_title('Impacto do Superhost no ROI e Payback', fontsize=14, fontweight='bold')
    ax.set_ylabel('ROI Líquido Médio (%)', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/08_superhost_roi.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 08_superhost_roi.png")

if __name__ == "__main__":
    print("Carregando dados...")
    details, prices, mesh, hosts, vivareal = load_data()

    print("Construindo DataFrame de ROI...")
    df = merge_data(details, prices, mesh, hosts)
    roi_df = build_roi(df, vivareal)

    print(f"Total de imóveis com ROI: {len(roi_df)}")
    print(f"\nGerando gráficos em '{OUTPUT_DIR}/'...\n")

    plot1_scatter_roi_payback(roi_df)
    plot2_roi_by_bedrooms(roi_df)
    plot3_roi_by_suburb(roi_df)
    plot4_heatmap_roi_bedrooms_suburb(roi_df)
    plot5_payback_distribution(roi_df)
    plot6_roi_vs_preco(roi_df)
    plot7_comparativo_cenarios(roi_df)
    plot8_superhost_roi(roi_df)

    print(f"\n8 gráficos salvos em '{OUTPUT_DIR}/'. Concluído!")
