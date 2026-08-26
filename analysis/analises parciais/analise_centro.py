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

def load_and_clean():
    details = pd.read_csv(f'{DATA_DIR}/Details_Itapema.csv')
    prices = pd.read_csv(f'{DATA_DIR}/Price_AV_Itapema.csv')
    mesh = pd.read_csv(f'{DATA_DIR}/Mesh_Ids_Data_Itapema.csv')
    hosts = pd.read_csv(f'{DATA_DIR}/Hosts_ids_Itapema.csv')
    vivareal = pd.read_csv(f'{DATA_DIR}/VivaReal_Itapema.csv')

    # Filtro Centro
    centro_ids = mesh[mesh['suburb'] == 'Centro']['airbnb_listing_id'].unique()
    d = details[details['airbnb_listing_id'].isin(centro_ids)].copy()
    d = d.drop_duplicates(subset='airbnb_listing_id')

    # Nulos
    d['star_rating'] = d['star_rating'].fillna(0)
    d['guest_satisfaction_overall'] = d['guest_satisfaction_overall'].fillna(0)
    d['is_guest_favorite'] = d['is_guest_favorite'].fillna(False)

    # Pets
    d['permite_animais'] = d['house_rules'].apply(
        lambda x: 'Sim' if pd.notna(x) and 'Permitido animais' in str(x) else 'Nao'
    )

    # Preco
    prices['date'] = pd.to_datetime(prices['date'])
    p = prices[prices['airbnb_listing_id'].isin(centro_ids)]
    p_agg = p.groupby('airbnb_listing_id').agg(
        mediana_preco=('price', 'median'),
        media_preco=('price', 'mean'),
        min_preco=('price', 'min'),
        max_preco=('price', 'max'),
        qtd_dias=('price', 'count'),
        std_preco=('price', 'std')
    ).reset_index()
    p_agg['std_preco'] = p_agg['std_preco'].fillna(0)

    # Merge
    df = d.merge(p_agg, on='airbnb_listing_id', how='inner')
    df = df[df['qtd_dias'] >= 30]

    # Outlier filter
    q1 = df['mediana_preco'].quantile(0.01)
    q3 = df['mediana_preco'].quantile(0.99)
    df = df[(df['mediana_preco'] >= q1) & (df['mediana_preco'] <= q3)]

    # Receita
    df['receita_mensal'] = df['mediana_preco'] * 30 * OCCUPANCY_RATE
    df['receita_anual'] = df['receita_mensal'] * 12

    # Hosts
    h = hosts[['owner_id', 'is_superhost']].copy()
    h = h.drop_duplicates(subset='owner_id')
    df = df.merge(h, on='owner_id', how='left')
    df['is_superhost'] = df['is_superhost'].fillna(False)

    # ROI
    vr = vivareal[(vivareal['sale_price'] > 100000) & (vivareal['suburb'] == 'Centro')]
    vr_avg = vr.groupby('bedrooms').agg(
        preco_venda_medio=('sale_price', 'median'),
        condominio_medio=('monthly_condo_fee', 'median'),
        iptu_medio=('yearly_iptu', 'median')
    ).reset_index().round(2)
    vr_avg = vr_avg.rename(columns={'bedrooms': 'number_of_bedrooms'})

    df = df.merge(vr_avg[['number_of_bedrooms', 'preco_venda_medio', 'condominio_medio', 'iptu_medio']],
                  on='number_of_bedrooms', how='inner')
    df = df[df['preco_venda_medio'] > 0]

    df['custos_anuais'] = df['condominio_medio'].fillna(0) * 12 + df['iptu_medio'].fillna(0)
    df['receita_liquida'] = df['receita_anual'] - df['custos_anuais']
    df['roi_liquido'] = (df['receita_liquida'] / df['preco_venda_medio'] * 100).round(2)
    df['payback_anos'] = (df['preco_venda_medio'] / df['receita_liquida']).round(1)

    # Grupo de quartos
    df['grupo_quartos'] = df['number_of_bedrooms'].apply(
        lambda x: 'Studio/0' if x == 0 else ('1 quarto' if x == 1 else ('2 quartos' if x == 2 else ('3 quartos' if x == 3 else '4+ quartos')))
    )

    return df

def analise_centro_geral(df):
    print("=" * 80)
    print("  CENTRO - VISAO GERAL")
    print("=" * 80)
    print(f"\n  Total de imoveis: {len(df)}")
    print(f"  Preco diario mediano: R$ {df['mediana_preco'].median():.0f}")
    print(f"  Receita anual mediana: R$ {df['receita_anual'].median():.0f}")
    print(f"  ROI liquido mediano: {df['roi_liquido'].median():.1f}%")
    print(f"  Payback mediano: {df['payback_anos'].median():.1f} anos")

def analise_quartos_centro(df):
    print("\n" + "=" * 80)
    print("  CENTRO - POR GRUPO DE QUARTOS")
    print("=" * 80)
    agg = df.groupby('grupo_quartos').agg(
        n=('airbnb_listing_id', 'count'),
        preco_mediano=('mediana_preco', 'median'),
        receita_anual=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median'),
        rating=('star_rating', 'median'),
        reviews=('number_of_reviews', 'median'),
        guest_satisfaction=('guest_satisfaction_overall', 'median'),
        pct_favorito=('is_guest_favorite', 'mean'),
        pct_superhost=('is_superhost', 'mean'),
        pct_animais=('permite_animais', lambda x: (x == 'Sim').mean()),
        preco_venda=('preco_venda_medio', 'median')
    ).round(2)

    # Ordem logica
    order = ['Studio/0', '1 quarto', '2 quartos', '3 quartos', '4+ quartos']
    agg = agg.reindex([x for x in order if x in agg.index])
    print(agg.to_string())
    return agg

def analise_favorito_centro(df):
    print("\n" + "=" * 80)
    print("  CENTRO - FAVORITO DOS HOSPEDES")
    print("=" * 80)
    agg = df.groupby('is_guest_favorite').agg(
        n=('airbnb_listing_id', 'count'),
        preco_mediano=('mediana_preco', 'median'),
        receita_anual=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median'),
        rating=('star_rating', 'median'),
        reviews=('number_of_reviews', 'median'),
        pct_superhost=('is_superhost', 'mean'),
        quartos_medio=('number_of_bedrooms', 'mean')
    ).round(2)
    print(agg.to_string())
    return agg

def analise_animais_centro(df):
    print("\n" + "=" * 80)
    print("  CENTRO - PERMISSAO DE ANIMAIS")
    print("=" * 80)
    agg = df.groupby('permite_animais').agg(
        n=('airbnb_listing_id', 'count'),
        preco_mediano=('mediana_preco', 'median'),
        receita_anual=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median'),
        rating=('star_rating', 'median'),
        reviews=('number_of_reviews', 'median')
    ).round(2)
    print(agg.to_string())
    return agg

def analise_banheiros_centro(df):
    print("\n" + "=" * 80)
    print("  CENTRO - POR BANHEIROS")
    print("=" * 80)
    df_v = df[df['number_of_bathrooms'] <= 4].copy()
    agg = df_v.groupby('number_of_bathrooms').agg(
        n=('airbnb_listing_id', 'count'),
        preco_mediano=('mediana_preco', 'median'),
        receita_anual=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median'),
        quartos_medio=('number_of_bedrooms', 'mean')
    ).round(2)
    print(agg.to_string())
    return agg

def analise_tipo_centro(df):
    print("\n" + "=" * 80)
    print("  CENTRO - POR TIPO DE ANUNCIO")
    print("=" * 80)
    agg = df.groupby('listing_type').agg(
        n=('airbnb_listing_id', 'count'),
        preco_mediano=('mediana_preco', 'median'),
        receita_anual=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median'),
        rating=('star_rating', 'median'),
        reviews=('number_of_reviews', 'median'),
        quartos_medio=('number_of_bedrooms', 'mean')
    ).round(2)
    print(agg.to_string())
    return agg

def analise_quartos_favorito(df):
    print("\n" + "=" * 80)
    print("  CENTRO - QUARTOS x FAVORITO (ROI)")
    print("=" * 80)
    pivot = df.groupby(['grupo_quartos', 'is_guest_favorite']).agg(
        n=('airbnb_listing_id', 'count'),
        roi=('roi_liquido', 'median'),
        receita=('receita_anual', 'median'),
        payback=('payback_anos', 'median'),
        rating=('star_rating', 'median')
    ).round(2)
    order = ['Studio/0', '1 quarto', '2 quartos', '3 quartos', '4+ quartos']
    pivot = pivot.reindex([x for x in order if x in pivot.index], level=0)
    print(pivot.to_string())
    return pivot

def comparativo_centro_vs_geral(df, df_geral):
    print("\n" + "=" * 80)
    print("  CENTRO vs MERCADO GERAL (1 QUARTO)")
    print("=" * 80)
    centro_1q = df[df['number_of_bedrooms'] == 1]
    geral_1q = df_geral[df_geral['number_of_bedrooms'] == 1]

    if len(centro_1q) == 0 or len(geral_1q) == 0:
        print("  Dados insuficientes para comparacao")
        return

    comp = pd.DataFrame({
        'Centro': {
            'n': len(centro_1q),
            'preco': centro_1q['mediana_preco'].median(),
            'receita': centro_1q['receita_anual'].median(),
            'roi': centro_1q['roi_liquido'].median(),
            'payback': centro_1q['payback_anos'].median(),
            'rating': centro_1q['star_rating'].median(),
            'reviews': centro_1q['number_of_reviews'].median(),
            'favorito_pct': centro_1q['is_guest_favorite'].mean() * 100,
        },
        'Geral': {
            'n': len(geral_1q),
            'preco': geral_1q['mediana_preco'].median(),
            'receita': geral_1q['receita_anual'].median(),
            'roi': geral_1q['roi_liquido'].median(),
            'payback': geral_1q['payback_anos'].median(),
            'rating': geral_1q['star_rating'].median(),
            'reviews': geral_1q['number_of_reviews'].median(),
            'favorito_pct': geral_1q['is_guest_favorite'].mean() * 100,
        }
    }).T
    print(comp.round(2).to_string())

# ============================================================
# GRAFICOS
# ============================================================

def grafico_quartos_centro(df):
    order = ['Studio/0', '1 quarto', '2 quartos', '3 quartos', '4+ quartos']
    df_g = df[df['grupo_quartos'].isin(order)].copy()

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    palette = sns.color_palette('YlOrRd_r', len(order))

    # ROI
    sns.barplot(data=df_g, x='grupo_quartos', y='roi_liquido', order=order,
                hue='grupo_quartos', palette=palette, ax=axes[0, 0],
                edgecolor='black', legend=False, estimator='median')
    axes[0, 0].set_title('ROI Liquido MEDIANO por Quartos', fontweight='bold')
    axes[0, 0].set_ylabel('ROI (%)')
    axes[0, 0].set_xlabel('')
    axes[0, 0].axhline(y=10, color='red', linestyle='--', alpha=0.5, label='Referencia 10%')
    axes[0, 0].legend()
    for p in axes[0, 0].patches:
        axes[0, 0].annotate(f'{p.get_height():.1f}%',
                            (p.get_x() + p.get_width()/2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Payback
    sns.barplot(data=df_g, x='grupo_quartos', y='payback_anos', order=order,
                hue='grupo_quartos', palette=palette, ax=axes[0, 1],
                edgecolor='black', legend=False, estimator='median')
    axes[0, 1].set_title('Payback MEDIANO por Quartos', fontweight='bold')
    axes[0, 1].set_ylabel('Payback (anos)')
    axes[0, 1].set_xlabel('')
    for p in axes[0, 1].patches:
        axes[0, 1].annotate(f'{p.get_height():.1f}a',
                            (p.get_x() + p.get_width()/2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Receita
    sns.barplot(data=df_g, x='grupo_quartos', y='receita_anual', order=order,
                hue='grupo_quartos', palette=palette, ax=axes[1, 0],
                edgecolor='black', legend=False, estimator='median')
    axes[1, 0].set_title('Receita Anual MEDIANA', fontweight='bold')
    axes[1, 0].set_ylabel('R$')
    axes[1, 0].set_xlabel('')
    for p in axes[1, 0].patches:
        axes[1, 0].annotate(f'R${p.get_height():,.0f}',
                            (p.get_x() + p.get_width()/2., p.get_height()),
                            ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Quantidade + Favoritos
    fav_by_q = df_g.groupby(['grupo_quartos', 'is_guest_favorite']).size().unstack(fill_value=0)
    fav_by_q = fav_by_q.reindex([x for x in order if x in fav_by_q.index])
    fav_by_q.plot(kind='bar', ax=axes[1, 1], color=['#95a5a6', '#2ecc71'], edgecolor='black')
    axes[1, 1].set_title('Imoveis: Favorito vs Nao Favorito', fontweight='bold')
    axes[1, 1].set_ylabel('Quantidade')
    axes[1, 1].set_xlabel('')
    axes[1, 1].legend(['Nao Favorito', 'Favorito'])
    axes[1, 1].set_xticklabels(axes[1, 1].get_xticklabels(), rotation=0)

    plt.suptitle('CENTRO - Analise por Grupo de Quartos (Estudio/1q = Foco)', fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/27_centro_quartos.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 27_centro_quartos.png")

def grafico_favorito_quartos(df):
    order = ['Studio/0', '1 quarto', '2 quartos', '3 quartos', '4+ quartos']
    df_g = df[df['grupo_quartos'].isin(order)].copy()

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # ROI por quartos e favorito
    sns.barplot(data=df_g, x='grupo_quartos', y='roi_liquido', order=order,
                hue='is_guest_favorite', palette=['#95a5a6', '#2ecc71'],
                ax=axes[0], edgecolor='black', estimator='median')
    axes[0].set_title('ROI por Quartos x Favorito', fontweight='bold')
    axes[0].set_ylabel('ROI (%)')
    axes[0].set_xlabel('')
    axes[0].axhline(y=10, color='red', linestyle='--', alpha=0.5)
    axes[0].legend(title='Favorito')

    # Rating
    sns.barplot(data=df_g, x='grupo_quartos', y='star_rating', order=order,
                hue='is_guest_favorite', palette=['#95a5a6', '#2ecc71'],
                ax=axes[1], edgecolor='black', estimator='median')
    axes[1].set_title('Rating por Quartos x Favorito', fontweight='bold')
    axes[1].set_ylabel('Rating')
    axes[1].set_xlabel('')
    axes[1].set_ylim(3.5, 5.5)
    axes[1].legend(title='Favorito')

    # Reviews
    sns.barplot(data=df_g, x='grupo_quartos', y='number_of_reviews', order=order,
                hue='is_guest_favorite', palette=['#95a5a6', '#2ecc71'],
                ax=axes[2], edgecolor='black', estimator='median')
    axes[2].set_title('Reviews por Quartos x Favorito', fontweight='bold')
    axes[2].set_ylabel('Reviews')
    axes[2].set_xlabel('')
    axes[2].legend(title='Favorito')

    plt.suptitle('CENTRO - Favorito impacta differently por Quartos', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/28_centro_favorito_quartos.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 28_centro_favorito_quartos.png")

def grafico_scatter_centro(df):
    fig, ax = plt.subplots(figsize=(14, 7))
    colors = {'Studio/0': '#e74c3c', '1 quarto': '#e67e22', '2 quartos': '#f1c40f',
              '3 quartos': '#2ecc71', '4+ quartos': '#3498db'}
    order = ['Studio/0', '1 quarto', '2 quartos', '3 quartos', '4+ quartos']

    for g in order:
        sub = df[df['grupo_quartos'] == g]
        ax.scatter(sub['payback_anos'], sub['roi_liquido'],
                   c=colors[g], label=g, alpha=0.6, s=60, edgecolors='black', linewidth=0.5)

    ax.axhline(y=10, color='red', linestyle='--', alpha=0.5, label='Referencia 10%')
    ax.axvline(x=10, color='blue', linestyle=':', alpha=0.5, label='Payback 10 anos')
    ax.set_title('CENTRO - ROI vs Payback por Grupo de Quartos', fontsize=14, fontweight='bold')
    ax.set_xlabel('Payback (anos)', fontsize=12)
    ax.set_ylabel('ROI Liquido (%)', fontsize=12)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 40)
    ax.legend(title='Grupo', fontsize=9)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/29_centro_scatter_roi_payback.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 29_centro_scatter_roi_payback.png")

def grafico_heatmap_centro(df):
    pivot = df.groupby(['grupo_quartos', 'is_guest_favorite']).agg(
        roi=('roi_liquido', 'median'),
        receita=('receita_anual', 'median')
    ).reset_index()
    pivot = pivot.pivot(index='grupo_quartos', columns='is_guest_favorite', values='roi')
    order = ['Studio/0', '1 quarto', '2 quartos', '3 quartos', '4+ quartos']
    pivot = pivot.reindex([x for x in order if x in pivot.index])
    pivot.columns = ['Nao Favorito', 'Favorito']

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', center=10,
                linewidths=0.5, ax=ax, cbar_kws={'label': 'ROI (%)'})
    ax.set_title('CENTRO - ROI (%) por Quartos x Favorito', fontsize=13, fontweight='bold')
    ax.set_xlabel('Favorito dos Hospedes', fontsize=12)
    ax.set_ylabel('Grupo de Quartos', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/30_centro_heatmap_roi.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 30_centro_heatmap_roi.png")

def grafico_comparativo(df):
    centro_1q = df[df['grupo_quartos'] == '1 quarto']
    centro_2q = df[df['grupo_quartos'] == '2 quartos']

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    metrics = ['roi_liquido', 'payback_anos', 'receita_anual', 'star_rating']
    labels = ['ROI (%)', 'Payback (anos)', 'Receita Anual (R$)', 'Rating']
    c1 = [centro_1q[m].median() for m in metrics]
    c2 = [centro_2q[m].median() for m in metrics]

    x = np.arange(len(labels))
    w = 0.35
    axes[0].bar(x - w/2, c1, w, label='1 Quarto', color='#e67e22', edgecolor='black')
    axes[0].bar(x + w/2, c2, w, label='2 Quartos', color='#f1c40f', edgecolor='black')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, fontsize=9)
    axes[0].set_title('1 Quarto vs 2 Quartos no Centro', fontweight='bold')
    axes[0].legend()

    # Preco de venda vs Receita
    axes[1].bar(['1 Quarto', '2 Quartos'],
                [centro_1q['preco_venda_medio'].median(), centro_2q['preco_venda_medio'].median()],
                color=['#e67e22', '#f1c40f'], edgecolor='black', label='Preco Venda (R$)')
    ax2 = axes[1].twinx()
    ax2.bar(['1 Quarto', '2 Quartos'],
            [centro_1q['receita_anual'].median(), centro_2q['receita_anual'].median()],
            color=['#e67e22', '#f1c40f'], edgecolor='black', alpha=0.4, label='Receita Anual (R$)')
    axes[1].set_title('Preco Venda vs Receita Anual', fontweight='bold')
    axes[1].set_ylabel('Preco Venda (R$)')
    ax2.set_ylabel('Receita Anual (R$)')

    plt.suptitle('CENTRO - Comparativo 1q vs 2q', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/31_centro_comparativo_1q_2q.png', bbox_inches='tight')
    plt.close()
    print("  [OK] 31_centro_comparativo_1q_2q.png")

if __name__ == "__main__":
    print("Carregando e limpando dados...")
    df = load_and_clean()

    # Dados gerais para comparacao
    details_all = pd.read_csv(f'{DATA_DIR}/Details_Itapema.csv')
    prices_all = pd.read_csv(f'{DATA_DIR}/Price_AV_Itapema.csv')
    mesh_all = pd.read_csv(f'{DATA_DIR}/Mesh_Ids_Data_Itapema.csv')
    hosts_all = pd.read_csv(f'{DATA_DIR}/Hosts_ids_Itapema.csv')
    vivareal_all = pd.read_csv(f'{DATA_DIR}/VivaReal_Itapema.csv')

    # Reutilizar funcao de limpeza para geral (simplificado)
    all_ids = mesh_all['airbnb_listing_id'].unique()
    da = details_all[details_all['airbnb_listing_id'].isin(all_ids)].drop_duplicates(subset='airbnb_listing_id')
    da['star_rating'] = da['star_rating'].fillna(0)
    pa = prices_all.copy()
    pa['date'] = pd.to_datetime(pa['date'])
    pa_agg = pa.groupby('airbnb_listing_id').agg(mediana_preco=('price', 'median'), qtd_dias=('price', 'count')).reset_index()
    mesh_sub = mesh_all[['airbnb_listing_id', 'suburb']].drop_duplicates(subset='airbnb_listing_id')
    da = da.merge(pa_agg, on='airbnb_listing_id', how='inner').merge(mesh_sub, on='airbnb_listing_id', how='left')
    da = da[da['qtd_dias'] >= 30]
    q1a = da['mediana_preco'].quantile(0.01)
    q3a = da['mediana_preco'].quantile(0.99)
    da = da[(da['mediana_preco'] >= q1a) & (da['mediana_preco'] <= q3a)]
    da['receita_anual'] = da['mediana_preco'] * 30 * OCCUPANCY_RATE * 12

    vr_all = vivareal_all[vivareal_all['sale_price'] > 100000].copy()
    vr_a = vr_all.groupby(['suburb', 'bedrooms']).agg(preco_venda_medio=('sale_price', 'median')).reset_index()
    vr_a = vr_a.rename(columns={'bedrooms': 'number_of_bedrooms'})
    da = da.merge(vr_a[['suburb', 'number_of_bedrooms', 'preco_venda_medio']], on=['suburb', 'number_of_bedrooms'], how='inner')
    da = da[da['preco_venda_medio'] > 0]
    da['roi_liquido'] = (da['receita_anual'] / da['preco_venda_medio'] * 100).round(2)
    da['payback_anos'] = (da['preco_venda_medio'] / da['receita_anual']).round(1)

    print(f"\nCentro: {len(df)} imoveis | Geral: {len(da)} imoveis\n")

    # Analises
    analise_centro_geral(df)
    quartos_df = analise_quartos_centro(df)
    fav_df = analise_favorito_centro(df)
    anim_df = analise_animais_centro(df)
    banh_df = analise_banheiros_centro(df)
    tipo_df = analise_tipo_centro(df)
    qfav_df = analise_quartos_favorito(df)
    comparativo_centro_vs_geral(df, da)

    # Graficos
    print(f"\nGerando graficos...")
    grafico_quartos_centro(df)
    grafico_favorito_quartos(df)
    grafico_scatter_centro(df)
    grafico_heatmap_centro(df)
    grafico_comparativo(df)

    print("\nAnalise do Centro concluida!")
