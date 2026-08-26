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
    price_std = price_agg['price_std'].fillna(0)

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
    return details

def analyze_pets(df):
    print("\n" + "="*80)
    print("  ANÁLISE: PERMISSÃO DE ANIMAIS")
    print("="*80)
    agg = df.groupby('permite_animais').agg(
        qtd=('airbnb_listing_id', 'count'),
        pct=('airbnb_listing_id', lambda x: f"{len(x)/len(df)*100:.1f}%"),
        preco_diario_medio=('avg_daily_price', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        rating_medio=('star_rating', 'mean'),
        reviews_medio=('number_of_reviews', 'mean'),
        guest_satisfaction=('guest_satisfaction_overall', 'mean'),
        quartos_medio=('number_of_bedrooms', 'mean'),
        banheiros_medio=('number_of_bathrooms', 'mean'),
        huespedes_medio=('number_of_guests', 'mean')
    ).round(2)
    print(agg.to_string())

    if 'roi_liquido' in df.columns:
        roi_agg = df.groupby('permite_animais').agg(
            roi_medio=('roi_liquido', 'mean'),
            payback_medio=('payback_anos', 'mean')
        ).round(2)
        print("\n--- ROI por Política de Animais ---")
        print(roi_agg.to_string())
    return agg

def analyze_bathrooms(df):
    print("\n" + "="*80)
    print("  ANÁLISE: NÚMERO DE BANHEIROS")
    print("="*80)
    df_valid = df[df['number_of_bathrooms'] <= 6].copy()
    agg = df_valid.groupby('number_of_bathrooms').agg(
        qtd=('airbnb_listing_id', 'count'),
        preco_diario_medio=('avg_daily_price', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        rating_medio=('star_rating', 'mean'),
        reviews_medio=('number_of_reviews', 'mean'),
        guest_satisfaction=('guest_satisfaction_overall', 'mean'),
        quartos_medio=('number_of_bedrooms', 'mean'),
        huespedes_medio=('number_of_guests', 'mean')
    ).round(2)
    print(agg.to_string())

    if 'roi_liquido' in df.columns:
        roi_agg = df_valid.groupby('number_of_bathrooms').agg(
            roi_medio=('roi_liquido', 'mean'),
            payback_medio=('payback_anos', 'mean'),
            preco_venda_medio=('preco_venda_medio', 'mean')
        ).round(2)
        print("\n--- ROI por Nº de Banheiros ---")
        print(roi_agg.to_string())
    return agg

def analyze_guest_favorite(df):
    print("\n" + "="*80)
    print("  ANÁLISE: FAVORITO DOS HÓSPEDES")
    print("="*80)
    agg = df.groupby('is_guest_favorite').agg(
        qtd=('airbnb_listing_id', 'count'),
        pct=('airbnb_listing_id', lambda x: f"{len(x)/len(df)*100:.1f}%"),
        preco_diario_medio=('avg_daily_price', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        rating_medio=('star_rating', 'mean'),
        reviews_medio=('number_of_reviews', 'mean'),
        guest_satisfaction=('guest_satisfaction_overall', 'mean'),
        quartos_medio=('number_of_bedrooms', 'mean'),
        banheiros_medio=('number_of_bathrooms', 'mean'),
        superhost_pct=('is_superhost', 'mean')
    ).round(2)
    print(agg.to_string())

    if 'roi_liquido' in df.columns:
        roi_agg = df.groupby('is_guest_favorite').agg(
            roi_medio=('roi_liquido', 'mean'),
            payback_medio=('payback_anos', 'mean'),
            preco_venda_medio=('preco_venda_medio', 'mean')
        ).round(2)
        print("\n--- ROI por Favorito dos Hóspedes ---")
        print(roi_agg.to_string())
    return agg

def analyze_combined_characteristics(df):
    print("\n" + "="*80)
    print("  ANÁLISE COMBINADA: ANIMAIS + BANHEIROS + FAVORITO")
    print("="*80)
    df_comb = df.copy()
    df_comb['banheiro_grupo'] = df_comb['number_of_bathrooms'].apply(
        lambda x: '1' if x <= 1 else ('2' if x == 2 else ('3' if x == 3 else '4+'))
    )
    df_comb['perfil'] = (
        df_comb['permite_animais'] + ' | ' +
        df_comb['banheiro_grupo'] + ' banheiro(s) | ' +
        df_comb['is_guest_favorite'].astype(str)
    )
    agg = df_comb.groupby('perfil').agg(
        qtd=('airbnb_listing_id', 'count'),
        preco_diario_medio=('avg_daily_price', 'mean'),
        receita_anual_media=('annual_revenue', 'mean'),
        rating_medio=('star_rating', 'mean'),
        reviews_medio=('number_of_reviews', 'mean')
    ).round(2)
    agg = agg[agg['qtd'] >= 10].sort_values('receita_anual_media', ascending=False)
    print(agg.to_string())

    if 'roi_liquido' in df_comb.columns:
        roi_agg = df_comb.groupby('perfil').agg(
            roi_medio=('roi_liquido', 'mean'),
            payback_medio=('payback_anos', 'mean'),
            preco_venda_medio=('preco_venda_medio', 'mean')
        ).round(2)
        roi_agg = roi_agg.loc[roi_agg.index.isin(agg.index)]
        print("\n--- ROI por Perfil Combinado ---")
        print(roi_agg.to_string())
    return agg

def plot1_pets_comparison(df):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    order = ['Sim', 'Não']

    sns.barplot(data=df, x='permite_animais', y='annual_revenue', order=order,
                palette='Set2', ax=axes[0], edgecolor='black', estimator='mean')
    axes[0].set_title('Receita Anual Média\n(Pet Policy)', fontweight='bold')
    axes[0].set_xlabel('Permite Animais')
    axes[0].set_ylabel('Receita Anual (R$)')
    for p in axes[0].patches:
        axes[0].annotate(f'R${p.get_height():,.0f}',
                         (p.get_x() + p.get_width()/2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    sns.barplot(data=df, x='permite_animais', y='number_of_reviews', order=order,
                palette='Set2', ax=axes[1], edgecolor='black',
                estimator=lambda x: x.mean())
    axes[1].set_title('Reviews por Imóvel\n(Pet Policy)', fontweight='bold')
    axes[1].set_xlabel('Permite Animais')
    axes[1].set_ylabel('Reviews Médios')

    sns.countplot(data=df, x='permite_animais', order=order,
                  palette='Set2', ax=axes[2], edgecolor='black')
    axes[2].set_title('Distribuição de Imóveis\n(Pet Policy)', fontweight='bold')
    axes[2].set_xlabel('Permite Animais')
    axes[2].set_ylabel('Quantidade')
    for p in axes[2].patches:
        axes[2].annotate(f'{int(p.get_height()):,}',
                         (p.get_x() + p.get_width()/2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Impacto da Permissão de Animais no Negócio', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/13_animais_impacto.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 13_animais_impacto.png")

def plot2_bathrooms_analysis(df):
    df_valid = df[df['number_of_bathrooms'] <= 5].copy()

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    bath_order = sorted(df_valid['number_of_bathrooms'].unique())
    palette = sns.color_palette('YlOrRd', len(bath_order))

    sns.barplot(data=df_valid, x='number_of_bathrooms', y='annual_revenue',
                order=bath_order, palette=palette, ax=axes[0], edgecolor='black',
                estimator='mean')
    axes[0].set_title('Receita Anual Média\npor Nº de Banheiros', fontweight='bold')
    axes[0].set_xlabel('Nº de Banheiros')
    axes[0].set_ylabel('Receita Anual (R$)')

    sns.barplot(data=df_valid, x='number_of_bathrooms', y='number_of_reviews',
                order=bath_order, palette=palette, ax=axes[1], edgecolor='black',
                estimator='mean')
    axes[1].set_title('Reviews por Imóvel\npor Nº de Banheiros', fontweight='bold')
    axes[1].set_xlabel('Nº de Banheiros')
    axes[1].set_ylabel('Reviews Médios')

    sns.countplot(data=df_valid, x='number_of_bathrooms', order=bath_order,
                  palette=palette, ax=axes[2], edgecolor='black')
    axes[2].set_title('Distribuição de Imóveis\npor Nº de Banheiros', fontweight='bold')
    axes[2].set_xlabel('Nº de Banheiros')
    axes[2].set_ylabel('Quantidade')
    for p in axes[2].patches:
        axes[2].annotate(f'{int(p.get_height()):,}',
                         (p.get_x() + p.get_width()/2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Impacto do Número de Banheiros', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/14_banheiros_impacto.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 14_banheiros_impacto.png")

def plot3_guest_favorite(df):
    order = [True, False]
    labels = ['Favorito', 'Não Favorito']

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    sns.barplot(data=df, x='is_guest_favorite', y='annual_revenue', order=order,
                palette=['#2ecc71', '#e74c3c'], ax=axes[0], edgecolor='black')
    axes[0].set_title('Receita Anual Média\npor Favorito', fontweight='bold')
    axes[0].set_xlabel('Favorito dos Hóspedes')
    axes[0].set_xticklabels(labels)
    for p in axes[0].patches:
        axes[0].annotate(f'R${p.get_height():,.0f}',
                         (p.get_x() + p.get_width()/2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    sns.barplot(data=df, x='is_guest_favorite', y='number_of_reviews', order=order,
                palette=['#2ecc71', '#e74c3c'], ax=axes[1], edgecolor='black')
    axes[1].set_title('Reviews por Imóvel\npor Favorito', fontweight='bold')
    axes[1].set_xlabel('Favorito dos Hóspedes')
    axes[1].set_xticklabels(labels)

    sns.countplot(data=df, x='is_guest_favorite', order=order,
                  palette=['#2ecc71', '#e74c3c'], ax=axes[2], edgecolor='black')
    axes[2].set_title('Distribuição de Imóveis\npor Favorito', fontweight='bold')
    axes[2].set_xlabel('Favorito dos Hóspedes')
    axes[2].set_xticklabels(labels)
    axes[2].set_ylabel('Quantidade')
    for p in axes[2].patches:
        axes[2].annotate(f'{int(p.get_height()):,}',
                         (p.get_x() + p.get_width()/2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Impacto de ser "Guest Favorite" no Airbnb', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/15_favorito_impacto.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 15_favorito_impacto.png")

def plot4_combined_heatmap(df):
    df_hm = df.copy()
    df_hm['banheiro_grupo'] = df_hm['number_of_bathrooms'].apply(
        lambda x: '1' if x <= 1 else ('2' if x == 2 else ('3' if x == 3 else '4+'))
    )
    pivot = df_hm.groupby(['permite_animais', 'banheiro_grupo'])['annual_revenue'].mean().reset_index()
    pivot = pivot.pivot(index='permite_animais', columns='banheiro_grupo', values='annual_revenue')

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(pivot / 1000, annot=True, fmt='.1f', cmap='YlOrRd',
                linewidths=0.5, ax=ax, cbar_kws={'label': 'Receita Anual (R$ mil)'})
    ax.set_title('Receita Anual Média (R$ mil): Animais x Banheiros', fontsize=13, fontweight='bold')
    ax.set_xlabel('Nº de Banheiros', fontsize=12)
    ax.set_ylabel('Permite Animais', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/16_heatmap_animais_banheiros.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 16_heatmap_animais_banheiros.png")

if __name__ == "__main__":
    print("Carregando dados...")
    details, prices, mesh, hosts, vivareal = load_data()

    print("Preparando dados...")
    df = merge_data(details, prices, mesh, hosts)

    pets = parse_pet_policy(details)[['airbnb_listing_id', 'permite_animais']]
    df = df.merge(pets, on='airbnb_listing_id', how='left')
    df['permite_animais'] = df['permite_animais'].fillna('Não')

    roi_df = build_roi(df, vivareal)
    df = df.merge(roi_df[['airbnb_listing_id', 'roi_liquido', 'payback_anos', 'preco_venda_medio']],
                  on='airbnb_listing_id', how='left')

    print(f"Total de imóveis: {len(df)}")

    pets_df = analyze_pets(df)
    bath_df = analyze_bathrooms(df)
    fav_df = analyze_guest_favorite(df)
    comb_df = analyze_combined_characteristics(df)

    print(f"\nGerando gráficos...")
    plot1_pets_comparison(df)
    plot2_bathrooms_analysis(df)
    plot3_guest_favorite(df)
    plot4_combined_heatmap(df)

    print("\nConcluído!")
