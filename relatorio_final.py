import pandas as pd
import numpy as np
import os

DATA_DIR = 'data'
OCCUPANCY_RATE = 0.65

def load_all():
    details = pd.read_csv(f'{DATA_DIR}/Details_Itapema.csv')
    prices = pd.read_csv(f'{DATA_DIR}/Price_AV_Itapema.csv')
    mesh = pd.read_csv(f'{DATA_DIR}/Mesh_Ids_Data_Itapema.csv')
    hosts = pd.read_csv(f'{DATA_DIR}/Hosts_ids_Itapema.csv')
    vivareal = pd.read_csv(f'{DATA_DIR}/VivaReal_Itapema.csv')
    return details, prices, mesh, hosts, vivareal

def clean(details, prices, mesh, hosts, vivareal):
    details = details.drop_duplicates(subset='airbnb_listing_id')
    details['star_rating'] = details['star_rating'].fillna(0)
    details['guest_satisfaction_overall'] = details['guest_satisfaction_overall'].fillna(0)
    details['is_guest_favorite'] = details['is_guest_favorite'].fillna(False)
    details['permite_animais'] = details['house_rules'].apply(
        lambda x: 'Sim' if pd.notna(x) and 'Permitido animais' in str(x) else 'Nao')

    prices['date'] = pd.to_datetime(prices['date'])
    p_agg = prices.groupby('airbnb_listing_id').agg(
        mediana_preco=('price', 'median'),
        qtd_dias=('price', 'count')).reset_index()

    mesh_sub = mesh[['airbnb_listing_id', 'suburb']].drop_duplicates(subset='airbnb_listing_id')
    df = details.merge(p_agg, on='airbnb_listing_id', how='inner')
    df = df.merge(mesh_sub, on='airbnb_listing_id', how='left')
    df = df[df['qtd_dias'] >= 30]

    q1 = df['mediana_preco'].quantile(0.01)
    q3 = df['mediana_preco'].quantile(0.99)
    df = df[(df['mediana_preco'] >= q1) & (df['mediana_preco'] <= q3)]

    df['receita_mensal'] = df['mediana_preco'] * 30 * OCCUPANCY_RATE
    df['receita_anual'] = df['receita_mensal'] * 12

    h = hosts[['owner_id', 'is_superhost']].drop_duplicates(subset='owner_id')
    df = df.merge(h, on='owner_id', how='left')
    df['is_superhost'] = df['is_superhost'].fillna(False)

    vr = vivareal[(vivareal['sale_price'] > 100000)].copy()
    vr_avg = vr.groupby(['suburb', 'bedrooms']).agg(
        preco_venda_medio=('sale_price', 'median'),
        condominio_medio=('monthly_condo_fee', 'median'),
        iptu_medio=('yearly_iptu', 'median')).reset_index().round(2)
    vr_avg = vr_avg.rename(columns={'bedrooms': 'number_of_bedrooms'})

    df = df.merge(vr_avg, on=['suburb', 'number_of_bedrooms'], how='inner')
    df = df[df['preco_venda_medio'] > 0]

    df['custos_anuais'] = df['condominio_medio'].fillna(0) * 12 + df['iptu_medio'].fillna(0)
    df['receita_liquida'] = df['receita_anual'] - df['custos_anuais']
    df['roi_liquido'] = (df['receita_liquida'] / df['preco_venda_medio'] * 100).round(2)
    df['payback_anos'] = (df['preco_venda_medio'] / df['receita_liquida']).round(1)

    df['grupo_quartos'] = df['number_of_bedrooms'].apply(
        lambda x: 'Studio/0' if x == 0 else ('1 quarto' if x == 1 else ('2 quartos' if x == 2 else ('3 quartos' if x == 3 else '4+ quartos'))))
    return df

def t(df):
    """Converte DataFrame para tabela Markdown"""
    return df.to_markdown(index=True)

def gerar_relatorio(df):
    lines = []
    L = lines.append

    L("# Relatório Final - Análise de Investimento em Itapema/SC")
    L("")
    L("**Hackathon JT 2026 - Seazone**")
    L("")
    L("---")
    L("")

    # =============================================
    # RESUMO EXECUTIVO
    # =============================================
    L("## 1. Resumo Executivo")
    L("")
    L("Este relatório analisa o mercado de aluguel de curta duração em Itapema/SC")
    L("para orientar decisões de investimento da Seazone. Foram analisados **{}** imóveis".format(len(df)))
    L("com dados do Airbnb e VivaReal, utilizando **mediana** (não média) para evitar")
    L("distorção por outliers, e filtro estatístico P1-P99.")
    L("")

    total = len(df)
    apt_count = len(df[df['listing_type'] == 'apartamento'])
    fav_count = df['is_guest_favorite'].sum()

    bairros_early = df.groupby('suburb').agg(
        n=('airbnb_listing_id', 'count'),
        roi=('roi_liquido', 'median'),
        receita=('receita_anual', 'median'),
        payback=('payback_anos', 'median')).round(2)
    bairros_conf_early = bairros_early[bairros_early['n'] >= 10]
    centro_roi = bairros_conf_early.loc['Centro']['roi'] if 'Centro' in bairros_conf_early.index else 0
    pet_rev_diff = (df[df['permite_animais']=='Sim']['number_of_reviews'].median() / df[df['permite_animais']=='Nao']['number_of_reviews'].median() - 1) * 100
    L(f"- **{total}** imóveis únicos com dados de preço válidos")
    L(f"- **{apt_count}** apartamentos ({apt_count/total*100:.0f}%)")
    L(f"- **{int(fav_count)}** guest favorites ({fav_count/total*100:.0f}%)")
    L(f"- **Superhosts:** {(df['is_superhost'].mean()*100):.0f}% dos imóveis")
    L(f"- Preço diário mediano: **R$ {df['mediana_preco'].median():.0f}**")
    L(f"- Receita anual mediana: **R$ {df['receita_anual'].median():,.0f}**")
    L(f"- ROI líquido mediano: **{df['roi_liquido'].median():.1f}%**")
    L(f"- Payback mediano: **{df['payback_anos'].median():.1f} anos**")
    L("")
    L("**Respostas rápidas:**")
    L("")
    L("| Pergunta | Resposta |")
    L("|----------|----------|")
    L("| Melhor perfil? | Apartamento, 2 quartos, 1-2 banheiros |")
    tab_roi = bairros_conf_early.loc['Tabuleiro dos Oliveiras']['roi'] if 'Tabuleiro dos Oliveiras' in bairros_conf_early.index else 0
    mor_roi = bairros_conf_early.loc['Morretes']['roi'] if 'Morretes' in bairros_conf_early.index else 0
    cent_n = len(df[df['suburb']=='Centro'])
    mor_n = len(df[df['suburb']=='Morretes'])
    L(f"| Melhor localização? | Centro (ROI {centro_roi:.0f}%, n={cent_n}) ou Morretes (ROI {mor_roi:.0f}%, n={mor_n}) |")
    sh_rec_diff = (df[df['is_superhost']==True]['receita_anual'].median() / df[df['is_superhost']==False]['receita_anual'].median() - 1) * 100
    fav_r = df[df['is_guest_favorite']==True]['star_rating'].median()
    sh_sign = '+' if sh_rec_diff >= 0 else ''
    L(f"| Características-chave? | Guest favorite (rating {fav_r:.2f}), localização (Centro/Morretes), pet friendly (+{pet_rev_diff:.0f}% reviews) |")
    L("| O que comprar? | Apartamento 1-2q em Centro (prioritário) ou Morretes |")
    L("")
    L("---")
    L("")

    # =============================================
    # METODOLOGIA
    # =============================================
    L("## 2. Metodologia")
    L("")
    L("| Item | Detalhe |")
    L("|------|---------|")
    L("| Fonte de dados | Airbnb (Details, Prices, Hosts, Mesh) + VivaReal |")
    L("| Período | Dados históricos de preço Airbnb + listagens VivaReal |")
    L("| Ocupação estimada | 65% (premissa conservadora) |")
    L("| Medida central | Mediana (robusta a outliers) |")
    L("| Filtro de outliers | Percentis P1-P99 do preço diário |")
    L("| Dados insuficientes | Removidos imóveis com <30 dias de preço |")
    L("| Deduplicação | Cada imóvel contado uma única vez (sem duplicatas por data) |")
    L("| ROI calculado | Receita líquida (receita - condomínio - IPTU) / Preço de venda VivaReal |")
    L("| Payback | Preço de venda / Receita líquida anual |")
    L("")
    L("**Limitação — Sazonalidade e ocupação:**")
    L("A análise de preços rastreados (Jan-Abr 2025) revelou forte sazonalidade em Itapema,")
    L("com amplitude de 1,6x entre o pico de verão (R$ 800/noite em janeiro) e o vale de outono")
    L("(R$ 490/noite em abril). Apartamentos são mais sazonais (amplitude 1,7x) que casas (1,5x),")
    L("e 69% dos imóveis oscilam mais de 50% entre meses. No entanto, os dados disponíveis cobrem")
    L("apenas 4 meses (Janeiro a Abril), não incluem a alta temporada completa (dezembro a fevereiro)")
    L("e não dispõem de taxa de ocupação real (o Airbnb não fornece status de disponibilidade nestas tabelas).")
    L("Por isso, mantemos a premissa de **ocupação fixa de 65%** nesta análise.")
    L("Estimativas de receita anual baseadas em apenas 4 meses de preço devem ser interpretadas")
    L("como indicativas, não como forecast preciso.")
    L("")
    L("---")
    L("")

    # =============================================
    # PERGUNTA 1
    # =============================================
    L("## 3. Qual seria o melhor perfil de imóvel para investir?")
    L("")

    # Tipo
    L("### 3.1 Tipo de Anúncio")
    L("")
    tipo = df.groupby('listing_type').agg(
        n=('airbnb_listing_id', 'count'),
        preco_mediano=('mediana_preco', 'median'),
        receita=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median'),
        rating=('star_rating', 'median')).round(2)
    L(t(tipo))
    L("")
    L("> **Conclusão:** Apartamentos dominam ({:.0f}% do mercado) com ROI de {:.1f}% e payback de {:.1f} anos.".format(
        len(df[df['listing_type']=='apartamento'])/total*100,
        df[df['listing_type']=='apartamento']['roi_liquido'].median(),
        df[df['listing_type']=='apartamento']['payback_anos'].median()))
    apt_rec = df[df['listing_type']=='apartamento']['receita_anual'].median()
    casa_rec = df[df['listing_type']=='casa']['receita_anual'].median()
    apt_roi = df[df['listing_type']=='apartamento']['roi_liquido'].median()
    casa_roi = df[df['listing_type']=='casa']['roi_liquido'].median()
    L(f"> Apartamentos superam casas em receita anual (R$ {apt_rec:,.0f} vs R$ {casa_rec:,.0f}) e em ROI ({apt_roi:.1f}% vs {casa_roi:.1f}%).")
    L("> **Nota sobre ROI:** O cálculo de ROI utiliza apenas condomínio e IPTU como custos.")
    L("> Podem existir taxas adicionais não capturadas (seguro, manutenção, administração, vacancy além da premissa de 65%),")
    L("> o que pode superestimar o ROI real. Esta é uma limitação da análise.")
    L("")

    # Quartos
    L("### 3.2 Quantidade de Quartos")
    L("")
    order = ['Studio/0', '1 quarto', '2 quartos', '3 quartos', '4+ quartos']
    qrt = df.groupby('grupo_quartos').agg(
        n=('airbnb_listing_id', 'count'),
        preco=('mediana_preco', 'median'),
        receita=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median'),
        rating=('star_rating', 'median'),
        favorito=('is_guest_favorite', 'mean'),
        superhost=('is_superhost', 'mean'),
        preco_venda=('preco_venda_medio', 'median')).round(2)
    qrt['favorito'] = (qrt['favorito'] * 100).round(0).astype(str) + '%'
    qrt['superhost'] = (qrt['superhost'] * 100).round(0).astype(str) + '%'
    qrt = qrt.reindex([x for x in order if x in qrt.index])
    L(t(qrt))
    L("")
    L("> **Sweet spot: 2 quartos** — melhor equilíbrio entre ROI ({:.1f}%), payback ({:.1f}a) e receita (R$ {:,.0f}).".format(
        df[df['grupo_quartos']=='2 quartos']['roi_liquido'].median(),
        df[df['grupo_quartos']=='2 quartos']['payback_anos'].median(),
        df[df['grupo_quartos']=='2 quartos']['receita_anual'].median()))
    preco_1q_venda = df[df['grupo_quartos']=='1 quarto']['preco_venda_medio'].median()
    preco_2q_venda = df[df['grupo_quartos']=='2 quartos']['preco_venda_medio'].median()
    diff_entrada = (preco_2q_venda - preco_1q_venda) / preco_2q_venda * 100
    L(f"> 1 quarto tem ROI levemente menor mas entrada ~{diff_entrada:.0f}% mais barata (R$ {preco_1q_venda:,.0f} vs R$ {preco_2q_venda:,.0f}).")
    L("> 3+ quartos: receita alta mas ROI cai e payback sobe.")
    L("")

    # Banheiros
    L("### 3.3 Banheiros")
    L("")
    banh = df[df['number_of_bathrooms'] <= 4].groupby('number_of_bathrooms').agg(
        n=('airbnb_listing_id', 'count'),
        preco=('mediana_preco', 'median'),
        receita=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median')).round(2)
    L(t(banh))
    L("")
    L("> **1 banheiro = melhor ROI ({:.1f}%)** e payback mais curto ({:.1f} anos).".format(
        df[df['number_of_bathrooms']==1]['roi_liquido'].median(),
        df[df['number_of_bathrooms']==1]['payback_anos'].median()))
    banho_2b_n = len(df[df['number_of_bathrooms']==2])
    banho_2b_rec = df[df['number_of_bathrooms']==2]['receita_anual'].median()
    banho_1b_rec = df[df['number_of_bathrooms']==1]['receita_anual'].median()
    L(f"> 2 banheiros: maior volume de imóveis ({banho_2b_n}) e receita moderadamente superior (R$ {banho_2b_rec:,.0f} vs R$ {banho_1b_rec:,.0f}).")
    L("")

    # Animais
    L("### 3.4 Política de Animais")
    L("")
    anim = df.groupby('permite_animais').agg(
        n=('airbnb_listing_id', 'count'),
        preco=('mediana_preco', 'median'),
        receita=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        reviews=('number_of_reviews', 'median')).round(2)
    L(t(anim))
    L("")
    pet_rec_diff_val = abs(df[df['permite_animais']=='Sim']['receita_anual'].median() / df[df['permite_animais']=='Nao']['receita_anual'].median() - 1) * 100
    pet_rev_diff = (df[df['permite_animais']=='Sim']['number_of_reviews'].median() / df[df['permite_animais']=='Nao']['number_of_reviews'].median() - 1) * 100
    L(f"> Diferença de receita mínima (~{pet_rec_diff_val:.0f}%). Porém, imóveis que permitem pets recebem **{pet_rev_diff:.0f}% mais reviews**")
    L("> — indicando maior demanda, mesmo sem cobrar mais.")
    L("")

    # Favoritos
    L("### 3.5 Guest Favorite")
    L("")
    fav = df.groupby('is_guest_favorite').agg(
        n=('airbnb_listing_id', 'count'),
        preco=('mediana_preco', 'median'),
        receita=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        rating=('star_rating', 'median'),
        reviews=('number_of_reviews', 'median'),
        superhost=('is_superhost', 'mean')).round(2)
    fav['superhost'] = (fav['superhost'] * 100).round(0).astype(str) + '%'
    L(t(fav))
    L("")
    fav_true_r = df[df['is_guest_favorite']==True]['star_rating'].median()
    fav_false_r = df[df['is_guest_favorite']==False]['star_rating'].median()
    fav_rev_diff = (df[df['is_guest_favorite']==True]['number_of_reviews'].median() / df[df['is_guest_favorite']==False]['number_of_reviews'].median() - 1) * 100
    fav_rec_diff = (df[df['is_guest_favorite']==True]['receita_anual'].median() / df[df['is_guest_favorite']==False]['receita_anual'].median() - 1) * 100
    L(f"> Favoritos têm rating {fav_true_r:.2f} vs {fav_false_r:.2f} e {fav_rev_diff:.0f}% mais reviews.")
    L(f"> Porém, receita {abs(fav_rec_diff):.0f}% menor — possivelmente imóveis menores/melhor avaliados.")
    L("> **Métrica mais importante:** busque imóveis com rating > 4.9.")
    L("")

    # Superhost
    L("### 3.6 Superhost")
    L("")
    sh = df.groupby('is_superhost').agg(
        n=('airbnb_listing_id', 'count'),
        preco=('mediana_preco', 'median'),
        receita=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median'),
        rating=('star_rating', 'median'),
        reviews=('number_of_reviews', 'median')).round(2)
    L(t(sh))
    L("")
    sh_true = df[df['is_superhost']==True]
    sh_false = df[df['is_superhost']==False]
    sh_preco_true = sh_true['mediana_preco'].median()
    sh_preco_false = sh_false['mediana_preco'].median()
    sh_preco_diff = (sh_preco_true / sh_preco_false - 1) * 100
    sh_rec_diff_val = (sh_true['receita_anual'].median() / sh_false['receita_anual'].median() - 1) * 100
    sh_rev_diff_final = (sh_true['number_of_reviews'].median() / sh_false['number_of_reviews'].median() - 1) * 100
    sh_preco_sign = '+' if sh_preco_diff >= 0 else ''
    sh_rec_sign = '+' if sh_rec_diff_val >= 0 else ''
    L(f"> Nesta amostra, superhosts cobram R$ {sh_preco_true:.0f}/noite vs R$ {sh_preco_false:.0f} ({sh_preco_sign}{sh_preco_diff:.0f}%) e faturam R$ {sh_true['receita_anual'].median():,.0f}/ano vs R$ {sh_false['receita_anual'].median():,.0f} ({sh_rec_sign}{sh_rec_diff_val:.0f}%).")
    L("> Porém, superhosts têm mais reviews ({} vs {}) e estão presentes em {:.0f}% dos imóveis.".format(
        sh_true['number_of_reviews'].median(), sh_false['number_of_reviews'].median(),
        sh_true.shape[0]/total*100))
    L("> **Hipótese (não testada):** O preço/receita menor pode refletir que superhosts nesta amostra")
    L("> gerenciam imóveis menores ou em bairros com menor valorização, focando em volume de reviews")
    L("> e ocupação ao invés de preço alto. Alternativamente, o status de superhost pode ser mais")
    L("> acessível para imóveis com ticket menor. Seria necessário controlar por tipo, tamanho e bairro")
    L("> para validar se o efeito superhost é real ou resultado de composição da amostra.")
    L("")

    # Perfil ideal
    L("### 3.7 Perfil Ideal Consolidado")
    L("")
    apt_pct = apt_count/total*100
    roi_1q = df[df['grupo_quartos']=='1 quarto']['roi_liquido'].median()
    roi_2q = df[df['grupo_quartos']=='2 quartos']['roi_liquido'].median()
    pb_1q = df[df['grupo_quartos']=='1 quarto']['payback_anos'].median()
    pb_2q = df[df['grupo_quartos']=='2 quartos']['payback_anos'].median()
    roi_1b = df[df['number_of_bathrooms']==1]['roi_liquido'].median()
    pb_1b = df[df['number_of_bathrooms']==1]['payback_anos'].median()
    L("| Característica | Recomendação | Justificativa |")
    L("|----------------|--------------|---------------|")
    L(f"| Tipo | Apartamento | {apt_pct:.0f}% do mercado, melhor ROI, mais liquidez |")
    L(f"| Quartos | 1-2 quartos | ROI {min(roi_1q,roi_2q):.0f}-{max(roi_1q,roi_2q):.0f}%, payback {min(pb_1q,pb_2q):.0f}-{max(pb_1q,pb_2q):.0f} anos |")
    L(f"| Banheiros | 1 banheiro | ROI {roi_1b:.1f}%, payback {pb_1b:.0f} anos (dados limpos) |")
    L("| Animais | Permitir | Demanda maior, custo zero |")
    L("| Superhost | Buscar imóveis com histórico de superhost | Mais reviews e visibilidade |")
    L("| Rating alvo | > 4.9 | Correlaciona com favoritos e demanda |")
    L("")
    L("---")
    L("")

    # =============================================
    # PERGUNTA 2
    # =============================================
    L("## 4. Em qual localização o imóvel teria a melhor receita?")
    L("")
    L("### 4.1 Ranking de Bairros por Receita e ROI")
    L("")
    bairros = df.groupby('suburb').agg(
        n=('airbnb_listing_id', 'count'),
        preco=('mediana_preco', 'median'),
        receita=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median'),
        rating=('star_rating', 'median'),
        quartos_medio=('number_of_bedrooms', 'mean'),
        preco_venda=('preco_venda_medio', 'median')).round(2)
    bairros = bairros.sort_values('roi', ascending=False)
    L(t(bairros))
    L("")
    L("> **Nota:** Bairros com menos de 10 imóveis podem ter ROI distorcido por amostra pequena.")
    L("> Várzea (n=1), Ilhota (n=9) e Canto da Praia (n=7) devem ser interpretados com cautela.")
    L("")

    L("### 4.2 Top 5 por ROI (mínimo 10 imóveis)")
    L("")
    bairros_conf = bairros[bairros['n'] >= 10]
    top5_roi = bairros_conf.head(5)
    L(t(top5_roi))
    L("")

    L("### 4.3 Top 5 por Receita Anual")
    L("")
    top5_rec = bairros.sort_values('receita', ascending=False).head(5)
    L(t(top5_rec))
    L("")

    L("> **Melhor receita:** Tabuleiro dos Oliveiras (R$ {:,.0f}), Centro (R$ {:,.0f}) e Meia Praia (R$ {:,.0f})".format(
        bairros.loc['Tabuleiro dos Oliveiras']['receita'] if 'Tabuleiro dos Oliveiras' in bairros.index else 0,
        bairros.loc['Centro']['receita'] if 'Centro' in bairros.index else 0,
        bairros.loc['Meia Praia']['receita'] if 'Meia Praia' in bairros.index else 0))
    L("> **Melhor ROI (com dados confiáveis):** Tabuleiro dos Oliveiras ({:.1f}%), Morretes ({:.1f}%), Casa Branca ({:.1f}%)".format(
        bairros_conf.loc['Tabuleiro dos Oliveiras']['roi'] if 'Tabuleiro dos Oliveiras' in bairros_conf.index else 0,
        bairros_conf.loc['Morretes']['roi'] if 'Morretes' in bairros_conf.index else 0,
        bairros_conf.loc['Casa Branca']['roi'] if 'Casa Branca' in bairros_conf.index else 0))
    L("> **Melhor equilíbrio:** Centro — maior oferta (n={}), ROI decente, alta liquidez".format(
        bairros.loc['Centro']['n'] if 'Centro' in bairros.index else 0))
    L("")
    L("---")
    L("")

    # =============================================
    # PERGUNTA 3
    # =============================================
    L("## 5. Quais características explicam as melhores receitas?")
    L("")
    L("### 5.1 Impacto de Cada Variável na Receita")
    L("")

    # Ranking de impacto
    metrics = []

    # Tipo
    apt_r = df[df['listing_type']=='apartamento']['receita_anual'].median()
    casa_r = df[df['listing_type']=='casa']['receita_anual'].median()
    metrics.append(('Tipo (casa vs apt)', abs(casa_r - apt_r), 'Casa: +R$ {:,.0f}'.format(casa_r - apt_r)))

    # Quartos
    r1 = df[df['grupo_quartos']=='1 quarto']['receita_anual'].median()
    r2 = df[df['grupo_quartos']=='2 quartos']['receita_anual'].median()
    r3 = df[df['grupo_quartos']=='3 quartos']['receita_anual'].median()
    metrics.append(('Quartos (2q vs 1q)', abs(r2 - r1), '+R$ {:,.0f}'.format(r2 - r1)))
    metrics.append(('Quartos (3q vs 2q)', abs(r3 - r2), '+R$ {:,.0f}'.format(r3 - r2)))

    # Superhost
    sh_r = df[df['is_superhost']==True]['receita_anual'].median()
    nsh_r = df[df['is_superhost']==False]['receita_anual'].median()
    metrics.append(('Superhost', abs(sh_r - nsh_r), '+R$ {:,.0f} (+{:.0f}%)'.format(sh_r - nsh_r, (sh_r/nsh_r-1)*100)))

    # Favoritos
    fav_r = df[df['is_guest_favorite']==True]['receita_anual'].median()
    nfav_r = df[df['is_guest_favorite']==False]['receita_anual'].median()
    metrics.append(('Guest Favorite', abs(fav_r - nfav_r), '{:+.0f}%'.format((fav_r/nfav_r-1)*100)))

    # Banheiros
    b1 = df[df['number_of_bathrooms']==1]['receita_anual'].median()
    b2 = df[df['number_of_bathrooms']==2]['receita_anual'].median()
    metrics.append(('Banheiros (2b vs 1b)', abs(b2 - b1), '+R$ {:,.0f}'.format(b2 - b1)))

    # Animais
    pet_r = df[df['permite_animais']=='Sim']['receita_anual'].median()
    npet_r = df[df['permite_animais']=='Nao']['receita_anual'].median()
    metrics.append(('Permite animais', abs(pet_r - npet_r), '{:+.0f}%'.format((pet_r/npet_r-1)*100)))

    imp_df = pd.DataFrame(metrics, columns=['Variável', 'Impacto R$', 'Detalhe'])
    imp_df = imp_df.sort_values('Impacto R$', ascending=False)
    L(t(imp_df))
    L("")

    sh_rev_diff_corr = (df[df['is_superhost']==True]['number_of_reviews'].median() / df[df['is_superhost']==False]['number_of_reviews'].median() - 1) * 100
    fav_rev_diff_corr = (df[df['is_guest_favorite']==True]['number_of_reviews'].median() / df[df['is_guest_favorite']==False]['number_of_reviews'].median() - 1) * 100
    pet_rev_diff_corr = (df[df['permite_animais']=='Sim']['number_of_reviews'].median() / df[df['permite_animais']=='Nao']['number_of_reviews'].median() - 1) * 100
    L("### 5.2 Correlações-Chave")
    L("")
    L("| Fator | Efeito na Receita | Efeito no ROI | Efeito na Demanda |")
    L("|-------|-------------------|---------------|-------------------|")
    L("| Mais quartos | ↑↑↑ Forte | ↓ (imóvel mais caro) | ↑ Moderado |")
    L("| Mais banheiros | ↑ Moderado | ↓ (imóvel mais caro) | — Neutro |")
    L(f"| Superhost | Variável (ver 3.6) | ↑ Moderado | ↑↑ Forte (+{sh_rev_diff_corr:.0f}% reviews) |")
    L(f"| Guest Favorite | ↓ Leve | ↓ Leve | ↑↑↑ Forte (+{fav_rev_diff_corr:.0f}% reviews) |")
    L(f"| Permite animais | — Neutro | ↓ Leve | ↑↑ Forte (+{pet_rev_diff_corr:.0f}% reviews) |")
    L("| Localização (bairro) | ↑↑↑ Muito forte | ↑↑↑ Determinante | — Variável |")
    L("")
    L("> **Hierarquia de impacto:** Localização > Tipo > Quartos > Superhost > Banheiros > Animais")
    L("")
    L("---")
    L("")

    # =============================================
    # PERGUNTA 4
    # =============================================
    L("## 6. Qual imóvel a Seazone deveria comprar hoje?")
    L("")
    L("### 6.1 Cenário Principal: Centro (Perfil Recomendado)")
    L("")
    centro_roi = bairros_conf.loc['Centro']['roi'] if 'Centro' in bairros_conf.index else 0
    centro_pb = df[df['suburb']=='Centro']['payback_anos'].median()
    cent_n = len(df[df['suburb']=='Centro'])
    L("| Critério | Especificação |")
    L("|-----------|---------------|")
    L("| Tipo | Apartamento |")
    L("| Quartos | 2 quartos |")
    L("| Banheiros | 1-2 banheiros |")
    L("| Bairro | Centro |")
    L("| Preço alvo | R$ 900k - R$ 1.2M |")
    L(f"| ROI esperado | {centro_roi:.0f}% |")
    L(f"| Payback | {centro_pb:.0f} anos |")
    L("| Animais | Permitir |")
    L("| Superhost | Buscar imóveis geridos por superhosts |")
    L("")
    L(f"**Justificativa:** Centro tem a maior amostra disponível (n={cent_n} imóveis),")
    L(f"o que torna os dados mais estatisticamente confiáveis. ROI de {centro_roi:.0f}% com payback de {centro_pb:.0f} anos,")
    L("ampla oferta de imóveis para escolher, maior liquidez na revenda, e sazonalidade moderada (1,5x).")
    L("Bairros com ROI aparentemente maior (Tabuleiro dos Oliveiras, Ilhota) possuem amostras muito")
    L("pequenas (n<20), o que pode distorcer os resultados e tornar a recomendação arriscada.")
    L("")

    L("### 6.2 Cenário Alternativo: Morretes (Perfil Conservador)")
    L("")
    L("| Critério | Especificação |")
    L("|-----------|---------------|")
    L("| Tipo | Apartamento |")
    L("| Quartos | 1-2 quartos |")
    L("| Banheiros | 1-2 banheiros |")
    L("| Bairro | Morretes |")
    L("| Preço alvo | R$ 600k - R$ 1M |")
    L(f"| ROI esperado | {mor_roi:.0f}% |")
    L(f"| Payback | {df[df['suburb']=='Morretes']['payback_anos'].median():.0f} anos |")
    L("| Animais | Permitir |")
    L("")
    mor_n = len(df[df['suburb']=='Morretes'])
    L(f"**Justificativa:** Segunda opção com amostra razoável (n={mor_n}), ROI superior ao Centro ({mor_roi:.0f}%)")
    L("e a menor sazonalidade entre os bairros relevantes (1,3x). Entry point mais baixo (R$ 600k-1M),")
    L("payback mais curto, adequado para investidores que buscam retorno mais rápido com menor capital.")
    L("")

    L("### 6.3 Cenário Agressivo: Tabuleiro dos Oliveiras")
    L("")
    L("| Critério | Especificação |")
    L("|-----------|---------------|")
    L("| Tipo | Apartamento |")
    L("| Quartos | 2 quartos |")
    L("| Banheiros | 1-2 banheiros |")
    L("| Bairro | Tabuleiro dos Oliveiras |")
    L(f"| ROI esperado | {tab_roi:.0f}% |")
    L(f"| Payback | ~{df[df['suburb']=='Tabuleiro dos Oliveiras']['payback_anos'].median():.0f} anos |")
    L("| Animais | Permitir |")
    L("")
    tab_ol_n = len(df[df['suburb']=='Tabuleiro dos Oliveiras'])
    L(f"**Atenção:** ROI mais alto ({tab_roi:.0f}%) mas amostra pequena (n={tab_ol_n}).")
    L("Resultados podem não ser reproduzíveis. Indicado apenas para investidores dispostos")
    L("a aceitar maior incerteza estatística em troca de potencial de retorno superior.")
    L("")

    L("### 6.3 Cenário C: Máxima Receita (Perfil Agressivo)")
    L("")
    m3q = df[(df['suburb']=='Morretes') & (df['grupo_quartos']=='3 quartos')]
    m3q_n = len(m3q)
    m3q_roi = m3q['roi_liquido'].median() if m3q_n > 0 else 0
    m3q_pb = m3q['payback_anos'].median() if m3q_n > 0 else 0
    m3q_rec = m3q['receita_anual'].median() if m3q_n > 0 else 0
    m3q_preco = m3q['preco_venda_medio'].median() if m3q_n > 0 else 0
    L("| Critério | Especificação |")
    L("|-----------|---------------|")
    L("| Tipo | Apartamento |")
    L("| Quartos | 3 quartos |")
    L("| Banheiros | 2-3 banheiros |")
    L("| Bairro | Morretes ou Centro |")
    L(f"| Preço alvo | R$ {m3q_preco/1e6:.1f}M - R$ {df[(df['suburb']=='Centro') & (df['grupo_quartos']=='3 quartos')]['preco_venda_medio'].median()/1e6:.1f}M |")
    L(f"| ROI esperado | {m3q_roi:.0f}-{df[(df['suburb']=='Centro') & (df['grupo_quartos']=='3 quartos')]['roi_liquido'].median():.0f}% |")
    L(f"| Payback | {m3q_pb:.0f}-{df[(df['suburb']=='Centro') & (df['grupo_quartos']=='3 quartos')]['payback_anos'].median():.0f} anos |")
    L(f"| Receita estimada | R$ {m3q_rec:,.0f} - R$ {df[(df['suburb']=='Centro') & (df['grupo_quartos']=='3 quartos')]['receita_anual'].median():,.0f} |")
    L("| Animais | Permitir |")
    L("")
    L(f"**Atenção:** Este cenário baseia-se em Morretes 3q (n={m3q_n}) e Centro 3q (n={len(df[(df['suburb']=='Centro') & (df['grupo_quartos']=='3 quartos')])}).")
    L("O número de imóveis é pequeno, tornando os valores de ROI e payback menos confiáveis.")
    L("Estes dados devem ser interpretados como indicativos, não como garantia de retorno.")
    L("")
    L("**Justificativa:** Maior receita bruta (R$ 175k+/ano), mas capital maior e")
    L("payback mais longo. Indicado para investidores com mais capital disponível.")
    L("")

    L("### 6.4 Justificativa Final")
    L("")
    L("**Recomendação principal: Cenário Principal** (Apartamento 2q, Centro)")
    L("")
    rec_2q = df[df['grupo_quartos']=='2 quartos']['receita_anual'].median()
    rec_1q = df[df['grupo_quartos']=='1 quarto']['receita_anual'].median()
    pb_2q = df[df['grupo_quartos']=='2 quartos']['payback_anos'].median()
    sh_2q_centro_pct = df[(df['suburb']=='Centro') & (df['grupo_quartos']=='2 quartos')]['is_superhost'].mean() * 100
    L(f"1. **ROI competitivo** (~{centro_roi:.0f}%) com a maior amostra disponível (n={cent_n})")
    L("2. **Maior liquidez** — Centro é o bairro com mais oferta, facilita revenda")
    L(f"3. **Receita sólida** — R$ {rec_2q/1000:.0f}k/ano (2q) vs R$ {rec_1q/1000:.0f}k/ano (1q)")
    L(f"4. **Payback gerenciável** — {centro_pb:.0f} anos")
    L("5. **Perfil mais procurado** — 2 quartos atende casais e famílias pequenas")
    L(f"6. **Potencial de superhost** — {sh_2q_centro_pct:.0f}% dos 2q já são superhosts no Centro")
    L("")
    L("---")
    L("")

    # =============================================
    # ANALISE EXTRA: CENTRO
    # =============================================
    L("## 7. Análise Extra: Centro — Validação da Hipótese")
    L("")
    L("Uma análise preliminar interna sugeriu que **apartamentos compactos (studio/1 quarto)**")
    L("na região **Centro** seriam apostas mais eficientes. Esta seção valida essa hipótese.")
    L("")

    centro = df[df['suburb'] == 'Centro']
    L(f"### 7.1 Panorama do Centro ({len(centro)} imóveis)")
    L("")
    L(f"- Preço diário mediano: **R$ {centro['mediana_preco'].median():.0f}**")
    L(f"- Receita anual mediana: **R$ {centro['receita_anual'].median():,.0f}**")
    L(f"- ROI líquido mediano: **{centro['roi_liquido'].median():.1f}%**")
    L(f"- Payback mediano: **{centro['payback_anos'].median():.1f} anos**")
    L("")

    L("### 7.2 ROI por Quartos no Centro")
    L("")
    centro_q = centro.groupby('grupo_quartos').agg(
        n=('airbnb_listing_id', 'count'),
        preco=('mediana_preco', 'median'),
        receita=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median'),
        rating=('star_rating', 'median'),
        favorito=('is_guest_favorite', 'mean'),
        preco_venda=('preco_venda_medio', 'median')).round(2)
    centro_q['favorito'] = (centro_q['favorito'] * 100).round(0).astype(str) + '%'
    centro_q = centro_q.reindex([x for x in order if x in centro_q.index])
    L(t(centro_q))
    L("")

    L("### 7.3 Favorito x Quartos no Centro (Insight-chave)")
    L("")
    qf = centro.groupby(['grupo_quartos', 'is_guest_favorite']).agg(
        n=('airbnb_listing_id', 'count'),
        roi=('roi_liquido', 'median'),
        receita=('receita_anual', 'median'),
        payback=('payback_anos', 'median'),
        rating=('star_rating', 'median')).round(2)
    qf = qf.reindex(pd.MultiIndex.from_product(
        [[x for x in order if x in centro['grupo_quartos'].unique()],
         [False, True]]), fill_value=0)
    L(t(qf))
    L("")

    L("### 7.4 Banheiros no Centro")
    L("")
    centro_b = centro[centro['number_of_bathrooms'] <= 4].groupby('number_of_bathrooms').agg(
        n=('airbnb_listing_id', 'count'),
        preco=('mediana_preco', 'median'),
        receita=('receita_anual', 'median'),
        roi=('roi_liquido', 'median'),
        payback=('payback_anos', 'median')).round(2)
    L(t(centro_b))
    L("")

    L("### 7.5 Centro vs Mercado Geral (1 Quarto)")
    L("")
    c1q = centro[centro['grupo_quartos'] == '1 quarto']
    g1q = df[(df['grupo_quartos'] == '1 quarto') & (df['suburb'] != 'Centro')]
    comp = pd.DataFrame({
        'Centro': {
            'n': len(c1q),
            'preco': c1q['mediana_preco'].median(),
            'receita': c1q['receita_anual'].median(),
            'roi': c1q['roi_liquido'].median(),
            'payback': c1q['payback_anos'].median(),
            'rating': c1q['star_rating'].median(),
        },
        'Geral (excl Centro)': {
            'n': len(g1q),
            'preco': g1q['mediana_preco'].median(),
            'receita': g1q['receita_anual'].median(),
            'roi': g1q['roi_liquido'].median(),
            'payback': g1q['payback_anos'].median(),
            'rating': g1q['star_rating'].median(),
        }
    }).T.round(2)
    L(t(comp))
    L("")

    L("### 7.6 Veredicto: A Hipótese se Confirma?")
    L("")
    c_1q_roi = c1q['roi_liquido'].median()
    c_2q_roi = centro[centro['grupo_quartos']=='2 quartos']['roi_liquido'].median()
    c_1q_pb = c1q['payback_anos'].median()
    c_2q_pb = centro[centro['grupo_quartos']=='2 quartos']['payback_anos'].median()
    c_1q_pv = c1q['preco_venda_medio'].median()
    c_2q_pv = centro[centro['grupo_quartos']=='2 quartos']['preco_venda_medio'].median()
    g1q_roi = g1q['roi_liquido'].median()
    c_1b_roi = centro[centro['number_of_bathrooms']==1]['roi_liquido'].median()
    c_1b_pb = centro[centro['number_of_bathrooms']==1]['payback_anos'].median()
    c_1q_fav = centro[(centro['grupo_quartos']=='1 quarto') & (centro['is_guest_favorite']==True)]
    c_2q_nfav = centro[(centro['grupo_quartos']=='2 quartos') & (centro['is_guest_favorite']==False)]
    L("| Aspecto | Hipótese | Resultado | Status |")
    L("|---------|----------|-----------|--------|")
    L(f"| 1q tem melhor ROI no Centro? | Sim | ROI {c_1q_roi:.1f}% (2q tem {c_2q_roi:.1f}%) | **{'Sim' if c_1q_roi > c_2q_roi else 'Parcial'}** |")
    L(f"| Payback mais curto para 1q? | Sim | {c_1q_pb:.1f}a (2q: {c_2q_pb:.1f}a) | **{'Sim' if c_1q_pb < c_2q_pb else 'Parcial'}** |")
    L(f"| Entry point menor? | Sim | R$ {c_1q_pv/1e6:.1f}M vs R$ {c_2q_pv/1e6:.1f}M (2q) | **Confirmado** |")
    L(f"| Centro competitivo vs geral? | Sim | ROI {c_1q_roi:.1f}% vs geral {g1q_roi:.1f}% | **{'Sim' if c_1q_roi >= g1q_roi else 'Parcial'}** |")
    L(f"| 1 banheiro é sweet spot? | - | ROI {c_1b_roi:.1f}%, payback {c_1b_pb:.0f}a | **Confirmado** |")
    L("")
    L("**Conclusão:** A premissa está **parcialmente correta**.")
    L(f"- 1 quarto no Centro tem ROI competitivo ({c_1q_roi:.1f}%) e entry point baixo (R$ {c_1q_pv/1e6:.1f}M)")
    L(f"- Porém, **2 quartos** tem ROI levemente superior ({c_2q_roi:.1f}%) e payback similar ({c_2q_pb:.1f}a)")
    L(f"- O maior achado: **1q favorito** tem ROI de **{c_1q_fav['roi_liquido'].median():.1f}%** e payback de **{c_1q_fav['payback_anos'].median():.1f} anos**")
    L(f"- E **2q não-favorito** tem ROI de **{c_2q_nfav['roi_liquido'].median():.1f}%** e payback de **{c_2q_nfav['payback_anos'].median():.1f} anos**")
    L("- A melhor jogada não é apenas \"1q no Centro\", mas **1-2q com perfil de favorito**")
    L("")
    L("---")
    L("")

    # =============================================
    # TABELA RESUMO
    # =============================================
    L("## 8. Tabela Resumo Final")
    L("")
    tab_ol = df[df['suburb']=='Tabuleiro dos Oliveiras']
    mor = df[df['suburb']=='Morretes']
    cen = df[df['suburb']=='Centro']
    cen_1q = cen[cen['grupo_quartos']=='1 quarto']
    L("| Perfil | Bairro | ROI | Payback | Receita | Investimento | Risco |")
    L("|--------|--------|-----|---------|---------|--------------|-------|")
    L(f"| **Principal (Recomendado)** | Centro | {cen['roi_liquido'].median():.0f}% | {cen['payback_anos'].median():.0f}a | R$ {cen['receita_anual'].median()/1000:.0f}k | R$ 900k-1.2M | Baixo |")
    L(f"| **Alternativo** | Morretes | {mor['roi_liquido'].median():.0f}% | {mor['payback_anos'].median():.0f}a | R$ {mor['receita_anual'].median()/1000:.0f}k | R$ 600k-1M | Baixo-Médio |")
    L(f"| **Agressivo** | Tab. Oliveiras | {tab_ol['roi_liquido'].median():.0f}% | {tab_ol['payback_anos'].median():.0f}a | R$ {tab_ol['receita_anual'].median()/1000:.0f}k | R$ 600k-900k | Médio |")
    L(f"| **Máxima Receita** | Morretes/Centro 3q | {m3q_roi:.0f}-{df[(df['suburb']=='Centro') & (df['grupo_quartos']=='3 quartos')]['roi_liquido'].median():.0f}% | {m3q_pb:.0f}-{df[(df['suburb']=='Centro') & (df['grupo_quartos']=='3 quartos')]['payback_anos'].median():.0f}a | R$ {m3q_rec/1000:.0f}-{df[(df['suburb']=='Centro') & (df['grupo_quartos']=='3 quartos')]['receita_anual'].median()/1000:.0f}k | R$ 1-2.5M | Médio-Alto |")
    L("")
    L("---")
    L("")
    L("## 9. Considerações Finais")
    L("")
    L("1. **Dados > Intuição:** A análise limpa revelou que casas NÃO faturam mais que")
    L("   apartamentos (artefato estatístico de dados duplicados). Sem a limpeza, a")
    L("   decisão seria errada.")
    L("")
    L(f"2. **Amostra importa tanto quanto ROI:** Tabuleiro dos Oliveiras tem ROI de {bairros_conf.loc['Tabuleiro dos Oliveiras']['roi']:.0f}% mas apenas {tab_ol_n} imóveis.")
    L(f"   Centro tem ROI de {bairros_conf.loc['Centro']['roi']:.0f}% com {cent_n} imóveis — resultado mais confiável.")
    L("   Bairros com n<20 devem ser tratados como indicativos, não como garantia.")
    L("")
    sh_sign_conc = '+' if sh_preco_diff >= 0 else ''
    L(f"3. **Superhost: sinal de gestão, não de preço alto:** Superhosts nesta amostra cobram {sh_sign_conc}{sh_preco_diff:.0f}%")
    L(f"   por noite e faturam {sh_rec_sign}{sh_rec_diff_val:.0f}% ao ano, mas acumulam +{sh_rev_diff_final:.0f}% mais reviews.")
    L("   O padrão sugere que superhosts priorizam volume e ocupação a preços altos,")
    L("   o que é coerente com gestão profissional de curta duração. Não é possível afirmar")
    L("   que ser superhost causa retorno financeiro superior — apenas que o status está")
    L("   associado a maior visibilidade (reviews) e prática de gestão ativa.")
    L("   Para Seazone:Buscar imóveis com histórico de superhost como proxy de gestão eficiente,")
    L("   mas não pagar prêmio por esse status sem controlar por bairro e tamanho.")
    L("")
    L("4. **Centro é a aposta mais segura:** ROI competitivo (10%), maior amostra (n={})".format(cent_n))
    L("   e sazonalidade moderada (1,5x). Morretes complementa com ROI maior (14%) e")
    L("   sazonalidade menor (1,3x), sendo a segunda opção recomendada.")
    L("")
    pet_rev_pct_final = (df[df['permite_animais']=='Sim']['number_of_reviews'].median() / df[df['permite_animais']=='Nao']['number_of_reviews'].median() - 1) * 100
    L(f"5. **Animais = demanda:** Permitir pets não aumenta preço mas gera {pet_rev_pct_final:.0f}% mais")
    L("   reviews. É uma alavancagem de demanda sem custo.")
    L("")
    L("6. **Payback realista:** No Centro, payback é de ~10 anos.")
    L("   Em Morretes, ~7 anos. Investimento de longo prazo, não especulativo.")
    L("")
    L("---")
    L("")
    L("*Relatório gerado automaticamente por analise consolidada*")
    L(f"*{len(df)} imóveis analisados | Filtro P1-P99 | Mediana como medida central*")
    L("")
    L("### Gráficos de Referência")
    L("")
    L("| Arquivo | Descrição |")
    L("|---------|-----------|")
    L("| `graficos/01_scatter_roi_payback.png` | Visão geral ROI vs Payback |")
    L("| `graficos/03_roi_por_bairro.png` | ROI por bairro |")
    L("| `graficos/04_heatmap_roi.png` | Heatmap quartos x bairro |")
    L("| `graficos/07_panorama_quartos.png` | Panorama por quartos |")
    L("| `graficos/08_superhost_roi.png` | Impacto do superhost |")
    L("| `graficos/09_oferta_demanda_roi.png` | Oferta vs Demanda |")
    L("| `graficos/13_animais_impacto.png` | Impacto de animais |")
    L("| `graficos/14_banheiros_impacto.png` | Impacto de banheiros |")
    L("| `graficos/15_favorito_impacto.png` | Impacto de favoritos |")
    L("| `graficos/21_tipo_overview_limpo.png` | Tipo de anúncio (limpo) |")
    L("| `graficos/27_centro_quartos.png` | Centro por quartos |")
    L("| `graficos/28_centro_favorito_quartos.png` | Centro favorito x quartos |")
    L("| `graficos/29_centro_scatter_roi_payback.png` | Centro scatter ROI |")
    L("| `graficos/30_centro_heatmap_roi.png` | Centro heatmap ROI |")
    L("| `graficos/31_centro_comparativo_1q_2q.png` | Centro 1q vs 2q |")

    return '\n'.join(lines)


if __name__ == '__main__':
    print('Carregando dados...')
    details, prices, mesh, hosts, vivareal = load_all()

    print('Limpando e processando...')
    df = clean(details, prices, mesh, hosts, vivareal)

    print(f'Dados finais: {len(df)} imóveis únicos')

    print('Gerando relatório...')
    relatorio = gerar_relatorio(df)

    output_path = 'relatorio_final.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(relatorio)

    print(f'\nRelatório salvo em: {output_path}')
    print(f'Tamanho: {len(relatorio):,} caracteres')

    # Preview
    print('\n' + '=' * 60)
    print('PREVIEW (primeiras 80 linhas):')
    print('=' * 60)
    for line in relatorio.split('\n')[:80]:
        print(line)
