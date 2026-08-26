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

# ============================================================
# 1. CARREGAMENTO E LIMPEZA
# ============================================================

def load_data():
    details = pd.read_csv(f'{DATA_DIR}/Details_Itapema.csv')
    prices = pd.read_csv(f'{DATA_DIR}/Price_AV_Itapema.csv')
    mesh = pd.read_csv(f'{DATA_DIR}/Mesh_Ids_Data_Itapema.csv')
    hosts = pd.read_csv(f'{DATA_DIR}/Hosts_ids_Itapema.csv')
    vivareal = pd.read_csv(f'{DATA_DIR}/VivaReal_Itapema.csv')
    return details, prices, mesh, hosts, vivareal

def clean_data(details, prices, mesh, hosts):
    print("=" * 80)
    print("  LIMPEZA E TRATAMENTO DOS DADOS")
    print("=" * 80)

    # --- DETAILS ---
    d = details.copy()
    print(f"\n[Details] Inicial: {len(d)} linhas, {d['airbnb_listing_id'].nunique()} imóveis únicos")
    d = d.drop_duplicates(subset='airbnb_listing_id')
    print(f"[Details] Após remover duplicatas: {len(d)} imóveis únicos")

    # Nulos críticos
    d['star_rating'] = d['star_rating'].fillna(0)
    d['number_of_reviews'] = d['number_of_reviews'].fillna(0)
    d['guest_satisfaction_overall'] = d['guest_satisfaction_overall'].fillna(0)
    d['cleaning_fee'] = d['cleaning_fee'].fillna(0)
    d['number_of_bathrooms'] = d['number_of_bathrooms'].fillna(1)
    d['picture_count'] = d['picture_count'].fillna(0)
    d['is_guest_favorite'] = d['is_guest_favorite'].fillna(False)

    # Parse pet policy
    d['permite_animais'] = d['house_rules'].apply(
        lambda x: 'Sim' if pd.notna(x) and 'Permitido animais' in str(x) else 'Não'
    )

    # --- PRICES ---
    p = prices.copy()
    p['date'] = pd.to_datetime(p['date'])
    print(f"\n[Prices] Inicial: {len(p)} registros, {p['airbnb_listing_id'].nunique()} imóveis únicos")

    # Agregar por imóvel (MEDIANA para evitar outliers)
    price_agg = p.groupby('airbnb_listing_id').agg(
        mediana_preco=('price', 'median'),
        media_preco=('price', 'mean'),
        min_preco=('price', 'min'),
        max_preco=('price', 'max'),
        qtd_dias=('price', 'count'),
        desvio_preco=('price', 'std')
    ).reset_index()
    price_agg['desvio_preco'] = price_agg['desvio_preco'].fillna(0)
    print(f"[Prices] Agregados: {len(price_agg)} imóveis")

    # --- FILTRO DE OUTLIERS NO PREÇO ---
    # Usar IQR para filtrar preços absurdos
    q1 = price_agg['mediana_preco'].quantile(0.01)
    q3 = price_agg['mediana_preco'].quantile(0.99)
    antes = len(price_agg)
    price_agg = price_agg[(price_agg['mediana_preco'] >= q1) & (price_agg['mediana_preco'] <= q3)]
    print(f"[Prices] Apos filtro de outliers (P1-P99): {antes} -> {len(price_agg)} imoveis")

    # --- MESH ---
    m = mesh[['airbnb_listing_id', 'suburb', 'latitude', 'longitude']].copy()
    m = m.drop_duplicates(subset='airbnb_listing_id')

    # --- HOSTS ---
    h = hosts[['owner_id', 'is_superhost', 'star_rating_host', 'years_host']].copy()
    h = h.drop_duplicates(subset='owner_id')

    # --- MERGE ---
    df = d.merge(m, on='airbnb_listing_id', how='left')
    df = df.merge(price_agg, on='airbnb_listing_id', how='inner')
    df = df.merge(h, on='owner_id', how='left', suffixes=('', '_host'))

    # Filtro: imóveis com pelo menos 30 dias de preço (dados representativos)
    antes = len(df)
    df = df[df['qtd_dias'] >= 30]
    print(f"[Merge] Apos filtro >=30 dias de preco: {antes} -> {len(df)} imoveis")

    # Receita estimada
    df['receita_mensal'] = df['mediana_preco'] * 30 * OCCUPANCY_RATE
    df['receita_anual'] = df['receita_mensal'] * 12

    print(f"\n[FINAL] Dataset limpo: {len(df)} imóveis")
    print(f"  Tipos: {df['listing_type'].value_counts().to_dict()}")
    print(f"  Bairros: {df['suburb'].nunique()}")
    print(f"  Preço mediano: R$ {df['mediana_preco'].median():.0f} (mediana)")

    return df

# ============================================================
# 2. ROI
# ============================================================

def build_roi(df, vivareal):
    vr = vivareal[vivareal['sale_price'] > 100000].copy()
    vr = vr.drop_duplicates(subset='listing_id')
    vr_avg = vr.groupby(['suburb', 'bedrooms']).agg(
        preco_venda_medio=('sale_price', 'median'),
        condominio_medio=('monthly_condo_fee', 'median'),
        iptu_medio=('yearly_iptu', 'median')
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
    roi_df['receita_liquida'] = roi_df['receita_anual'] - roi_df['custos_anuais']
    roi_df['roi_liquido'] = (roi_df['receita_liquida'] / roi_df['preco_venda_medio'] * 100).round(2)
    roi_df['payback_anos'] = (roi_df['preco_venda_medio'] / roi_df['receita_liquida']).round(1)
    return roi_df

# ============================================================
# 3. ANÁLISES
# ============================================================

def analise_geral(df):
    print("\n" + "=" * 80)
    print("  VISÃO GERAL DO MERCADO (DADOS LIMPOS)")
    print("=" * 80)
    print(f"\n  Total de imóveis analisados: {len(df)}")
    print(f"  Preço diário mediano:       R$ {df['mediana_preco'].median():.0f}")
    print(f"  Receita anual mediana:      R$ {df['receita_anual'].median():.0f}")
    print(f"  Rating mediano:             {df['star_rating'].median():.1f}")
    print(f"  Reviews mediano:            {df['number_of_reviews'].median():.0f}")

def analise_tipo(df):
    print("\n" + "=" * 80)
    print("  ANÁLISE POR TIPO DE ANÚNCIO")
    print("=" * 80)
    agg = df.groupby('listing_type').agg(
        n_imoveis=('airbnb_listing_id', 'count'),
        preco_diario_mediano=('mediana_preco', 'median'),
        receita_anual_mediana=('receita_anual', 'median'),
        rating_mediano=('star_rating', 'median'),
        reviews_mediano=('number_of_reviews', 'median'),
        quartos_medio=('number_of_bedrooms', 'mean'),
        banheiros_medio=('number_of_bathrooms', 'mean'),
        huespedes_medio=('number_of_guests', 'mean'),
        pct_superhost=('is_superhost', 'mean'),
        pct_animais=('permite_animais', lambda x: (x == 'Sim').mean()),
        pct_favorito=('is_guest_favorite', 'mean')
    ).round(2).sort_values('receita_anual_mediana', ascending=False)
    print(agg.to_string())
    return agg

def analise_tipo_bairro(df):
    print("\n" + "=" * 80)
    print("  TIPO DE ANÚNCIO POR BAIRRO (Top 5)")
    print("=" * 80)
    top = df['suburb'].value_counts().head(5).index
    for bairro in top:
        sub = df[df['suburb'] == bairro]
        agg = sub.groupby('listing_type').agg(
            n=('airbnb_listing_id', 'count'),
            preco_mediano=('mediana_preco', 'median'),
            receita_mediana=('receita_anual', 'median')
        ).round(2)
        print(f"\n--- {bairro} (n={len(sub)}) ---")
        print(agg.to_string())

def analise_tipo_quartos(df):
    print("\n" + "=" * 80)
    print("  TIPO DE ANÚNCIO POR Nº DE QUARTOS")
    print("=" * 80)
    df_v = df[df['number_of_bedrooms'] <= 5].copy()
    pivot = df_v.groupby(['number_of_bedrooms', 'listing_type']).agg(
        n=('airbnb_listing_id', 'count'),
        preco_mediano=('mediana_preco', 'median'),
        receita_mediana=('receita_anual', 'median')
    ).round(2)
    print(pivot.to_string())

def analise_animais(df):
    print("\n" + "=" * 80)
    print("  ANÁLISE: PERMISSÃO DE ANIMAIS")
    print("=" * 80)
    agg = df.groupby('permite_animais').agg(
        n=('airbnb_listing_id', 'count'),
        preco_mediano=('mediana_preco', 'median'),
        receita_mediana=('receita_anual', 'median'),
        rating_mediano=('star_rating', 'median'),
        reviews_mediano=('number_of_reviews', 'median'),
        quartos_medio=('number_of_bedrooms', 'mean'),
        banheiros_medio=('number_of_bathrooms', 'mean')
    ).round(2)
    print(agg.to_string())
    return agg

def analise_banheiros(df):
    print("\n" + "=" * 80)
    print("  ANÁLISE: NÚMERO DE BANHEIROS")
    print("=" * 80)
    df_v = df[df['number_of_bathrooms'] <= 5].copy()
    agg = df_v.groupby('number_of_bathrooms').agg(
        n=('airbnb_listing_id', 'count'),
        preco_mediano=('mediana_preco', 'median'),
        receita_mediana=('receita_anual', 'median'),
        rating_mediano=('star_rating', 'median'),
        reviews_mediano=('number_of_reviews', 'median'),
        quartos_medio=('number_of_bedrooms', 'mean')
    ).round(2)
    print(agg.to_string())
    return agg

def analise_favorito(df):
    print("\n" + "=" * 80)
    print("  ANÁLISE: FAVORITO DOS HÓSPEDES")
    print("=" * 80)
    agg = df.groupby('is_guest_favorite').agg(
        n=('airbnb_listing_id', 'count'),
        preco_mediano=('mediana_preco', 'median'),
        receita_mediana=('receita_anual', 'median'),
        rating_mediano=('star_rating', 'median'),
        reviews_mediano=('number_of_reviews', 'median'),
        quartos_medio=('number_of_bedrooms', 'mean'),
        banheiros_medio=('number_of_bathrooms', 'mean'),
        pct_superhost=('is_superhost', 'mean')
    ).round(2)
    print(agg.to_string())
    return agg

def analise_roi_completo(roi_df):
    print("\n" + "=" * 80)
    print("  ROI POR TIPO DE ANÚNCIO")
    print("=" * 80)
    agg = roi_df.groupby('listing_type').agg(
        n=('airbnb_listing_id', 'count'),
        roi_mediano=('roi_liquido', 'median'),
        payback_mediano=('payback_anos', 'median'),
        receita_mediana=('receita_anual', 'median'),
        preco_venda_mediano=('preco_venda_medio', 'median')
    ).round(2).sort_values('roi_mediano', ascending=False)
    print(agg.to_string())

    print("\n" + "=" * 80)
    print("  ROI POR BAIRRO (Top 10)")
    print("=" * 80)
    agg_b = roi_df.groupby('suburb').agg(
        n=('airbnb_listing_id', 'count'),
        roi_mediano=('roi_liquido', 'median'),
        payback_mediano=('payback_anos', 'median'),
        receita_mediana=('receita_anual', 'median'),
        preco_venda_mediano=('preco_venda_medio', 'median')
    ).round(2).sort_values('roi_mediano', ascending=False)
    print(agg_b.head(10).to_string())

    print("\n" + "=" * 80)
    print("  ROI POR QUARTOS")
    print("=" * 80)
    df_v = roi_df[roi_df['number_of_bedrooms'] <= 5].copy()
    agg_q = df_v.groupby('number_of_bedrooms').agg(
        n=('airbnb_listing_id', 'count'),
        roi_mediano=('roi_liquido', 'median'),
        payback_mediano=('payback_anos', 'median'),
        receita_mediana=('receita_anual', 'median'),
        preco_venda_mediano=('preco_venda_medio', 'median')
    ).round(2).sort_values('roi_mediano', ascending=False)
    print(agg_q.to_string())
    return agg, agg_b, agg_q

# ============================================================
# 4. GRÁFICOS
# ============================================================

def graficos_tipo(df):
    order = df['listing_type'].value_counts().index.tolist()
    palette = sns.color_palette('Set2', len(order))

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    sns.countplot(data=df, x='listing_type', order=order, hue='listing_type',
                  palette=palette, ax=axes[0, 0], edgecolor='black', legend=False)
    axes[0, 0].set_title('Distribuição de Imóveis', fontweight='bold')
    for p in axes[0, 0].patches:
        axes[0, 0].annotate(f'{int(p.get_height()):,}',
                            (p.get_x() + p.get_width()/2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

    sns.barplot(data=df, x='listing_type', y='receita_anual', order=order,
                hue='listing_type', palette=palette, ax=axes[0, 1], edgecolor='black',
                legend=False, estimator='median')
    axes[0, 1].set_title('Receita Anual MEDIANA', fontweight='bold')
    axes[0, 1].set_ylabel('R$')
    for p in axes[0, 1].patches:
        axes[0, 1].annotate(f'R${p.get_height():,.0f}',
                            (p.get_x() + p.get_width()/2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

    sns.barplot(data=df, x='listing_type', y='mediana_preco', order=order,
                hue='listing_type', palette=palette, ax=axes[1, 0], edgecolor='black',
                legend=False, estimator='median')
    axes[1, 0].set_title('Preço Diário MEDIANO', fontweight='bold')
    axes[1, 0].set_ylabel('R$')
    for p in axes[1, 0].patches:
        axes[1, 0].annotate(f'R${p.get_height():,.0f}',
                            (p.get_x() + p.get_width()/2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

    sns.barplot(data=df, x='listing_type', y='star_rating', order=order,
                hue='listing_type', palette=palette, ax=axes[1, 1], edgecolor='black',
                legend=False, estimator='median')
    axes[1, 1].set_title('Rating MEDIANO', fontweight='bold')
    axes[1, 1].set_ylim(3, 5.5)
    for p in axes[1, 1].patches:
        axes[1, 1].annotate(f'{p.get_height():.1f}',
                            (p.get_x() + p.get_width()/2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Panorama por Tipo de Anúncio (Dados Limpos - Medianas)', fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/21_tipo_overview_limpo.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 21_tipo_overview_limpo.png")

def grafico_tipo_bairro(df):
    top = df['suburb'].value_counts().head(5).index.tolist()
    df_top = df[df['suburb'].isin(top)]
    pivot = df_top.groupby(['suburb', 'listing_type'])['receita_anual'].median().reset_index()
    pivot = pivot.pivot(index='suburb', columns='listing_type', values='receita_anual') / 1000

    fig, ax = plt.subplots(figsize=(12, 6))
    pivot.plot(kind='bar', ax=ax, edgecolor='black', width=0.8)
    ax.set_title('Receita Anual MEDIANA (R$ mil) por Tipo e Bairro', fontsize=13, fontweight='bold')
    ax.set_ylabel('Receita Anual (R$ mil)')
    ax.legend(title='Tipo')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/22_tipo_bairro_limpo.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 22_tipo_bairro_limpo.png")

def grafico_animais(df):
    order = ['Não', 'Sim']
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    sns.barplot(data=df, x='permite_animais', y='receita_anual', order=order,
                hue='permite_animais', palette=['#e74c3c', '#2ecc71'], ax=axes[0],
                edgecolor='black', legend=False, estimator='median')
    axes[0].set_title('Receita Anual MEDIANA\npor Política de Animais', fontweight='bold')
    axes[0].set_ylabel('R$')
    for p in axes[0].patches:
        axes[0].annotate(f'R${p.get_height():,.0f}',
                         (p.get_x() + p.get_width()/2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    sns.barplot(data=df, x='permite_animais', y='mediana_preco', order=order,
                hue='permite_animais', palette=['#e74c3c', '#2ecc71'], ax=axes[1],
                edgecolor='black', legend=False, estimator='median')
    axes[1].set_title('Preço Diário MEDIANO\npor Política de Animais', fontweight='bold')
    axes[1].set_ylabel('R$')
    for p in axes[1].patches:
        axes[1].annotate(f'R${p.get_height():,.0f}',
                         (p.get_x() + p.get_width()/2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    sns.countplot(data=df, x='permite_animais', order=order,
                  hue='permite_animais', palette=['#e74c3c', '#2ecc71'], ax=axes[2],
                  edgecolor='black', legend=False)
    axes[2].set_title('Distribuição de Imóveis', fontweight='bold')
    for p in axes[2].patches:
        axes[2].annotate(f'{int(p.get_height()):,}',
                         (p.get_x() + p.get_width()/2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Impacto da Permissão de Animais (Dados Limpos)', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/23_animais_limpo.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 23_animais_limpo.png")

def grafico_banheiros(df):
    df_v = df[df['number_of_bathrooms'] <= 5].copy()
    order = sorted(df_v['number_of_bathrooms'].unique())
    palette = sns.color_palette('YlOrRd', len(order))

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    sns.barplot(data=df_v, x='number_of_bathrooms', y='receita_anual', order=order,
                hue='number_of_bathrooms', palette=palette, ax=axes[0],
                edgecolor='black', legend=False, estimator='median')
    axes[0].set_title('Receita Anual MEDIANA\npor Nº de Banheiros', fontweight='bold')
    axes[0].set_ylabel('R$')

    sns.barplot(data=df_v, x='number_of_bathrooms', y='mediana_preco', order=order,
                hue='number_of_bathrooms', palette=palette, ax=axes[1],
                edgecolor='black', legend=False, estimator='median')
    axes[1].set_title('Preço Diário MEDIANO\npor Nº de Banheiros', fontweight='bold')
    axes[1].set_ylabel('R$')

    sns.countplot(data=df_v, x='number_of_bathrooms', order=order,
                  hue='number_of_bathrooms', palette=palette, ax=axes[2],
                  edgecolor='black', legend=False)
    axes[2].set_title('Distribuição de Imóveis', fontweight='bold')
    for p in axes[2].patches:
        axes[2].annotate(f'{int(p.get_height()):,}',
                         (p.get_x() + p.get_width()/2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Impacto do Nº de Banheiros (Dados Limpos)', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/24_banheiros_limpo.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 24_banheiros_limpo.png")

def grafico_favorito(df):
    order = [True, False]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    sns.barplot(data=df, x='is_guest_favorite', y='receita_anual', order=order,
                hue='is_guest_favorite', palette=['#2ecc71', '#95a5a6'], ax=axes[0],
                edgecolor='black', legend=False, estimator='median')
    axes[0].set_title('Receita Anual MEDIANA\npor Favorito', fontweight='bold')
    axes[0].set_ylabel('R$')
    axes[0].set_xticklabels(['Favorito', 'Não Favorito'])
    for p in axes[0].patches:
        axes[0].annotate(f'R${p.get_height():,.0f}',
                         (p.get_x() + p.get_width()/2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    sns.barplot(data=df, x='is_guest_favorite', y='star_rating', order=order,
                hue='is_guest_favorite', palette=['#2ecc71', '#95a5a6'], ax=axes[1],
                edgecolor='black', legend=False, estimator='median')
    axes[1].set_title('Rating MEDIANO\npor Favorito', fontweight='bold')
    axes[1].set_xticklabels(['Favorito', 'Não Favorito'])
    axes[1].set_ylim(3, 5.5)

    sns.countplot(data=df, x='is_guest_favorite', order=order,
                  hue='is_guest_favorite', palette=['#2ecc71', '#95a5a6'], ax=axes[2],
                  edgecolor='black', legend=False)
    axes[2].set_title('Distribuição de Imóveis', fontweight='bold')
    axes[2].set_xticklabels(['Favorito', 'Não Favorito'])
    for p in axes[2].patches:
        axes[2].annotate(f'{int(p.get_height()):,}',
                         (p.get_x() + p.get_width()/2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Impacto de ser Guest Favorite (Dados Limpos)', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/25_favorito_limpo.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 25_favorito_limpo.png")

def grafico_roi_tipo(roi_df):
    agg = roi_df.groupby('listing_type').agg(
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median')
    ).round(2).sort_values('roi', ascending=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    palette = sns.color_palette('RdYlGn_r', len(agg))

    axes[0].barh(agg.index, agg['roi'], color=palette, edgecolor='black')
    for i, row in enumerate(agg.itertuples()):
        axes[0].text(row.roi + 0.2, i, f'{row.roi}%', va='center', fontsize=10, fontweight='bold')
    axes[0].set_title('ROI Líquido MEDIANO por Tipo', fontweight='bold')
    axes[0].set_xlabel('ROI (%)')
    axes[0].axvline(x=10, color='red', linestyle='--', alpha=0.5, label='10%')
    axes[0].legend()

    axes[1].barh(agg.index, agg['payback'], color=palette, edgecolor='black')
    for i, row in enumerate(agg.itertuples()):
        axes[1].text(row.payback + 0.2, i, f'{row.payback}a', va='center', fontsize=10, fontweight='bold')
    axes[1].set_title('Payback MEDIANO por Tipo', fontweight='bold')
    axes[1].set_xlabel('Payback (anos)')

    plt.suptitle('ROI por Tipo de Anúncio (Dados Limpos)', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/26_roi_tipo_limpo.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 26_roi_tipo_limpo.png")

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("Carregando dados brutos...")
    details, prices, mesh, hosts, vivareal = load_data()

    df = clean_data(details, prices, mesh, hosts)
    roi_df = build_roi(df, vivareal)

    analise_geral(df)
    tipo_df = analise_tipo(df)
    analise_tipo_bairro(df)
    analise_tipo_quartos(df)
    animais_df = analise_animais(df)
    banheiros_df = analise_banheiros(df)
    fav_df = analise_favorito(df)
    roi_tipo, roi_bairro, roi_quartos = analise_roi_completo(roi_df)

    print(f"\nGerando gráficos...")
    graficos_tipo(df)
    grafico_tipo_bairro(df)
    grafico_animais(df)
    grafico_banheiros(df)
    grafico_favorito(df)
    grafico_roi_tipo(roi_df)

    print("\nAnálise limpa concluída!")
