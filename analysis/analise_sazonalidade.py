import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# =============================================
# CONFIG
# =============================================
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
GRAPH_DIR = os.path.join(os.path.dirname(__file__), 'graficos_sazonal')
os.makedirs(GRAPH_DIR, exist_ok=True)

lines = []
def L(s=''):
    lines.append(s)

def save_fig(name):
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPH_DIR, name), dpi=150, bbox_inches='tight')
    plt.close()

# =============================================
# CARREGAR E MERGE
# =============================================
print('Carregando dados...')
price = pd.read_csv(os.path.join(DATA_DIR, 'Price_AV_Itapema.csv'))
details = pd.read_csv(os.path.join(DATA_DIR, 'Details_Itapema.csv'))
mesh = pd.read_csv(os.path.join(DATA_DIR, 'Mesh_Ids_Data_Itapema.csv'))

price['date'] = pd.to_datetime(price['date'])
details['aquisition_date_d'] = pd.to_datetime(details['aquisition_date']).dt.date

# Merge price com details
df = price.merge(details[['airbnb_listing_id', 'listing_type', 'number_of_bedrooms',
                           'number_of_bathrooms', 'star_rating']], on='airbnb_listing_id', how='inner')

# Merge com mesh para suburb
if 'suburb' not in df.columns:
    df = df.merge(mesh[['airbnb_listing_id', 'suburb']], on='airbnb_listing_id', how='left')

df['mes'] = df['date'].dt.to_period('M')
df['mes_num'] = df['date'].dt.month
df['mes_nome'] = df['date'].dt.strftime('%b/%Y')

# =============================================
# VARIAVEIS DERIVADAS
# =============================================
df['grupo_quartos'] = pd.cut(df['number_of_bedrooms'], bins=[-1, 0.5, 1.5, 2.5, 10],
                              labels=['Studio/0', '1 quarto', '2 quartos', '3+ quartos'])

# Filtrar P1-P99 por mes (evitar distorcao)
p1 = df['price'].quantile(0.01)
p99 = df['price'].quantile(0.99)
df_f = df[(df['price'] >= p1) & (df['price'] <= p99)].copy()

print(f'Gerando relatório de sazonalidade ({len(df_f)} registros, {df_f["airbnb_listing_id"].nunique()} imóveis)...')

# =============================================
# 1. SAZONALIDADE GERAL
# =============================================
print('  1/6 Sazonalidade geral...')
saz_geral = df_f.groupby('mes').agg(
    n_registros=('price', 'count'),
    n_imoveis=('airbnb_listing_id', 'nunique'),
    preco_mediano=('price', 'median'),
    preco_medio=('price', 'mean'),
    preco_p25=('price', lambda x: x.quantile(0.25)),
    preco_p75=('price', lambda x: x.quantile(0.75)),
).round(2)

baseline_preco = saz_geral['preco_mediano'].median()
saz_geral['idx_preco'] = (saz_geral['preco_mediano'] / baseline_preco * 100).round(1)
saz_geral['idx_volume'] = (saz_geral['n_imoveis'] / saz_geral['n_imoveis'].median() * 100).round(1)

L('# Análise de Sazonalidade - Itapema/SC')
L('')
L('**Dados:** Price_AV_Itapema.csv (preços diários rastreados pelo Airbnb)')
L('**Período:** Janeiro a Abril 2025')
L('**Metodologia:** Mediana de preço diário por imóvel, agrupado por mês de coleta')
L('')
L('---')
L('')
L('## 1. Sazonalidade Geral')
L('')
L('| Mês | Imóveis | Preço mediano | Índice preço | Índice volume |')
L('|-----|---------|---------------|-------------|---------------|')
for idx, row in saz_geral.iterrows():
    L(f'| {idx} | {int(row["n_imoveis"])} | R$ {row["preco_mediano"]:,.0f} | {row["idx_preco"]:.0f} | {row["idx_volume"]:.0f} |')
L('')
amplitude = saz_geral['preco_mediano'].max() / saz_geral['preco_mediano'].min()
L(f'**Amplitude sazonal (máx/mín):** {amplitude:.1f}x — preços no pico são {((amplitude-1)*100):.0f}% maiores que no vale.')
L(f'**Meses de alta (>110% do baseline):** {", ".join(saz_geral[saz_geral["idx_preco"]>110].index.astype(str))}')
L(f'**Meses de baixa (<90% do baseline):** {", ".join(saz_geral[saz_geral["idx_preco"]<90].index.astype(str))}')
L('')

# Grafico 1: duplo eixo
fig, ax1 = plt.subplots(figsize=(10, 5))
months = saz_geral.index.astype(str)
x = range(len(months))
ax1.bar(x, saz_geral['preco_mediano'], color='#2196F3', alpha=0.7, label='Preço mediano')
ax1.set_ylabel('Preço mediano (R$)', color='#2196F3')
ax1.tick_params(axis='y', labelcolor='#2196F3')
ax2 = ax1.twinx()
ax2.plot(x, saz_geral['n_imoveis'], color='#FF5722', marker='o', linewidth=2, label='Imóveis ativos')
ax2.set_ylabel('Imóveis ativos', color='#FF5722')
ax2.tick_params(axis='y', labelcolor='#FF5722')
ax1.set_xticks(x)
ax1.set_xticklabels(months, rotation=45)
ax1.set_title('Sazonalidade Geral: Preço x Volume de Imóveis')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
save_fig('01_sazonalidade_geral.png')

# =============================================
# 2. SAZONALIDADE POR TIPO
# =============================================
print('  2/6 Sazonalidade por tipo...')
saz_tipo = df_f.groupby(['mes', 'listing_type']).agg(
    n_imoveis=('airbnb_listing_id', 'nunique'),
    preco_mediano=('price', 'median')).round(2).reset_index()

tipos_principais = df_f['listing_type'].value_counts().head(2).index.tolist()
saz_tipo_f = saz_tipo[saz_tipo['listing_type'].isin(tipos_principais)]
saz_tipo_pivot = saz_tipo_f.pivot_table(index='mes', columns='listing_type', values='preco_mediano', aggfunc='median').round(2)

L('## 2. Sazonalidade por Tipo de Imóvel')
L('')
if not saz_tipo_pivot.empty:
    header = '| Mês | ' + ' | '.join(saz_tipo_pivot.columns) + ' |'
    sep = '|-----|' + '|'.join(['--------'] * len(saz_tipo_pivot.columns)) + '|'
    L(header)
    L(sep)
    for idx, row in saz_tipo_pivot.iterrows():
        vals = ' | '.join([f'R$ {v:,.0f}' if pd.notna(v) else '-' for v in row])
        L(f'| {idx} | {vals} |')
    L('')

    # Calcular amplitude por tipo
    L('**Amplitude sazonal por tipo:**')
    for tipo in tipos_principais:
        dados = saz_tipo_f[saz_tipo_f['listing_type'] == tipo].set_index('mes')['preco_mediano']
        if len(dados) > 1:
            amp = dados.max() / dados.min()
            L(f'- **{tipo}:** {amp:.1f}x (variação de {((amp-1)*100):.0f}%)')
    L('')

# Grafico 2
fig, ax = plt.subplots(figsize=(10, 5))
for tipo in tipos_principais:
    dados = saz_tipo_f[saz_tipo_f['listing_type'] == tipo].set_index('mes')['preco_mediano']
    ax.plot(dados.index.astype(str), dados.values, marker='o', linewidth=2, label=tipo)
ax.set_title('Sazonalidade por Tipo de Imóvel')
ax.set_ylabel('Preço mediano (R$)')
ax.legend()
ax.grid(True, alpha=0.3)
save_fig('02_sazonalidade_tipo.png')

# =============================================
# 3. SAZONALIDADE POR QUARTOS
# =============================================
print('  3/6 Sazonalidade por quartos...')
saz_q = df_f.groupby(['mes', 'grupo_quartos'], observed=False).agg(
    n_imoveis=('airbnb_listing_id', 'nunique'),
    preco_mediano=('price', 'median')).round(2).reset_index()

grupos_q = ['Studio/0', '1 quarto', '2 quartos', '3+ quartos']
saz_q_pivot = saz_q[saz_q['grupo_quartos'].isin(grupos_q)].pivot_table(
    index='mes', columns='grupo_quartos', values='preco_mediano', aggfunc='median', observed=False).round(2)

L('## 3. Sazonalidade por Nº de Quartos')
L('')
if not saz_q_pivot.empty:
    header = '| Mês | ' + ' | '.join(saz_q_pivot.columns) + ' |'
    sep = '|-----|' + '|'.join(['--------'] * len(saz_q_pivot.columns)) + '|'
    L(header)
    L(sep)
    for idx, row in saz_q_pivot.iterrows():
        vals = ' | '.join([f'R$ {v:,.0f}' if pd.notna(v) else '-' for v in row])
        L(f'| {idx} | {vals} |')
    L('')

    L('**Amplitude sazonal por quartos:**')
    for q in grupos_q:
        dados = saz_q[(saz_q['grupo_quartos'] == q)].set_index('mes')['preco_mediano']
        if len(dados) > 1:
            amp = dados.max() / dados.min()
            L(f'- **{q}:** {amp:.1f}x (variação de {((amp-1)*100):.0f}%)')
    L('')

# Grafico 3
fig, ax = plt.subplots(figsize=(10, 5))
colors = ['#4CAF50', '#2196F3', '#FF9800', '#F44336']
for i, q in enumerate(grupos_q):
    dados = saz_q[(saz_q['grupo_quartos'] == q)].set_index('mes')['preco_mediano']
    if len(dados) > 0:
        ax.plot(dados.index.astype(str), dados.values, marker='o', linewidth=2, label=q, color=colors[i])
ax.set_title('Sazonalidade por Nº de Quartos')
ax.set_ylabel('Preço mediano (R$)')
ax.legend()
ax.grid(True, alpha=0.3)
save_fig('03_sazonalidade_quartos.png')

# =============================================
# 4. SAZONALIDADE POR BAIRRO
# =============================================
print('  4/6 Sazonalidade por bairro...')
bairros_top = df_f.groupby('suburb')['airbnb_listing_id'].nunique().sort_values(ascending=False).head(8).index.tolist()
saz_b = df_f[df_f['suburb'].isin(bairros_top)].groupby(['mes', 'suburb']).agg(
    n_imoveis=('airbnb_listing_id', 'nunique'),
    preco_mediano=('price', 'median')).round(2).reset_index()

saz_b_pivot = saz_b.pivot_table(index='mes', columns='suburb', values='preco_mediano', aggfunc='median').round(2)

L('## 4. Sazonalidade por Bairro (Top 8)')
L('')
if not saz_b_pivot.empty:
    header = '| Mês | ' + ' | '.join(saz_b_pivot.columns) + ' |'
    sep = '|-----|' + '|'.join(['---------'] * len(saz_b_pivot.columns)) + '|'
    L(header)
    L(sep)
    for idx, row in saz_b_pivot.iterrows():
        vals = ' | '.join([f'R$ {v:,.0f}' if pd.notna(v) else '-' for v in row])
        L(f'| {idx} | {vals} |')
    L('')

    L('**Amplitude sazonal por bairro:**')
    for b in bairros_top:
        dados = saz_b[saz_b['suburb'] == b].set_index('mes')['preco_mediano']
        if len(dados) > 1:
            amp = dados.max() / dados.min()
            L(f'- **{b}:** {amp:.1f}x (variação de {((amp-1)*100):.0f}%)')
    L('')

# Grafico 4
fig, ax = plt.subplots(figsize=(12, 6))
for b in bairros_top[:5]:
    dados = saz_b[saz_b['suburb'] == b].set_index('mes')['preco_mediano']
    if len(dados) > 0:
        ax.plot(dados.index.astype(str), dados.values, marker='o', linewidth=2, label=b)
ax.set_title('Sazonalidade por Bairro (Top 5)')
ax.set_ylabel('Preço mediano (R$)')
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True, alpha=0.3)
save_fig('04_sazonalidade_bairros.png')

# =============================================
# 5. AMPLITUDE POR IMOVEL (quanto cada listing muda)
# =============================================
print('  5/6 Amplitude por imóvel...')
amp_imovel = df_f.groupby('airbnb_listing_id').agg(
    n_meses=('mes', 'nunique'),
    preco_min=('price', 'min'),
    preco_max=('price', 'max'),
    preco_med=('price', 'median'),
    listing_type=('listing_type', 'first'),
    quartos=('number_of_bedrooms', 'first')).reset_index()

amp_imovel['amplitude'] = (amp_imovel['preco_max'] / amp_imovel['preco_min']).round(2)
amp_multi = amp_imovel[amp_imovel['n_meses'] >= 2].copy()

L('## 5. Amplitude de Preço por Imóvel')
L('')
L('Para imóveis com dados em 2+ meses:')
L('')
L('| Métrica | Valor |')
L('|---------|-------|')
L(f'| Imóveis com 2+ meses de dados | {len(amp_multi)} |')
L(f'| Amplitude mediana | {amp_multi["amplitude"].median():.1f}x |')
L(f'| Amplitude média | {amp_multi["amplitude"].mean():.1f}x |')
L(f'| Imóveis com amplitude > 1.5x | {(amp_multi["amplitude"] > 1.5).sum()} ({(amp_multi["amplitude"] > 1.5).mean()*100:.0f}%) |')
L(f'| Imóveis com amplitude > 2x | {(amp_multi["amplitude"] > 2).sum()} ({(amp_multi["amplitude"] > 2).mean()*100:.0f}%) |')
L('')

# Amplitude por tipo
L('**Amplitude mediana por tipo:**')
for tipo in tipos_principais:
    sub = amp_multi[amp_multi['listing_type'] == tipo]
    if len(sub) > 0:
        L(f'- **{tipo}:** {sub["amplitude"].median():.1f}x (n={len(sub)})')
L('')

# Grafico 5: distribuicao de amplitude
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].hist(amp_multi['amplitude'], bins=30, color='#2196F3', edgecolor='white', alpha=0.8)
axes[0].axvline(amp_multi['amplitude'].median(), color='red', linestyle='--', label=f'Mediana: {amp_multi["amplitude"].median():.1f}x')
axes[0].set_title('Distribuição da Amplitude de Preço')
axes[0].set_xlabel('Amplitude (máx/mín)')
axes[0].set_ylabel('Nº de imóveis')
axes[0].legend()

# Boxplot por tipo
tipos_box = [amp_multi[amp_multi['listing_type'] == t]['amplitude'].values for t in tipos_principais]
axes[1].boxplot(tipos_box, tick_labels=tipos_principais)
axes[1].set_title('Amplitude por Tipo')
axes[1].set_ylabel('Amplitude (máx/mín)')
axes[1].axhline(1, color='gray', linestyle=':', alpha=0.5)
save_fig('05_amplitude_por_imovel.png')

# =============================================
# 6. IMPACTO NA RECEITA ANUAL
# =============================================
print('  6/6 Impacto na receita anual...')

# Cenario A: preco fixo (mediana anual) x 365 dias x 65% ocupacao
# Cenario B: preco sazonal (mes a mes) x dias do mes x 65% ocupacao
OCCUPANCY = 0.65

df_f['dias_no_mes'] = df_f['date'].dt.days_in_month
receita_fixa = df_f.groupby('airbnb_listing_id').agg(
    preco_anual=('price', 'median'),
    listing_type=('listing_type', 'first'),
    quartos=('number_of_bedrooms', 'first'),
    suburb=('suburb', 'first')).reset_index()
receita_fixa['receita_fixa'] = receita_fixa['preco_anual'] * 365 * OCCUPANCY

receita_saz = df_f.groupby(['airbnb_listing_id', 'mes']).agg(
    preco_mes=('price', 'median'),
    dias=('dias_no_mes', 'first')).reset_index()
receita_saz['receita_mes'] = receita_saz['preco_mes'] * receita_saz['dias'] * OCCUPANCY
receita_saz_anual = receita_saz.groupby('airbnb_listing_id')['receita_mes'].sum().reset_index()
receita_saz_anual.columns = ['airbnb_listing_id', 'receita_sazonal']

comp_receita = receita_fixa.merge(receita_saz_anual, on='airbnb_listing_id', how='inner')
comp_receita['diferenca_pct'] = ((comp_receita['receita_sazonal'] / comp_receita['receita_fixa'] - 1) * 100).round(2)

L('## 6. Impacto na Receita Anual Estimada')
L('')
L('Compara dois cenários (mesmo imóvel, mesma ocupação de 65%):')
L('- **A: Preço fixo** — mediana anual aplicada a 365 dias')
L('- **B: Preço sazonal** — mediana mensal aplicada a cada mês')
L('')
L('| Métrica | Valor |')
L('|---------|-------|')
L(f'| Imóveis com dados suficientes | {len(comp_receita)} |')
L(f'| Diferença mediana | {comp_receita["diferenca_pct"].median():+.1f}% |')
L(f'| Diferença média | {comp_receita["diferenca_pct"].mean():+.1f}% |')
L(f'| Imóveis com receita SAZONAL > FIXA | {(comp_receita["diferenca_pct"]>0).sum()} ({(comp_receita["diferenca_pct"]>0).mean()*100:.0f}%) |')
L(f'| Imóveis com receita FIXA > SAZONAL | {(comp_receita["diferenca_pct"]<0).sum()} ({(comp_receita["diferenca_pct"]<0).mean()*100:.0f}%) |')
L('')

# Por tipo
L('**Diferença mediana por tipo:**')
for tipo in tipos_principais:
    sub = comp_receita[comp_receita['listing_type'] == tipo]
    if len(sub) > 0:
        L(f'- **{tipo}:** {sub["diferenca_pct"].median():+.1f}% (n={len(sub)})')
L('')

# Por quartos
L('**Diferença mediana por quartos:**')
for q in grupos_q:
    sub = comp_receita[comp_receita['quartos'] == q]
    if len(sub) > 0:
        L(f'- **{q}:** {sub["diferenca_pct"].median():+.1f}% (n={len(sub)})')
L('')

L('### Interpretação')
L('')
if comp_receita['diferenca_pct'].median() > 0:
    L('> O cenário sazonal gera **mais receita** porque o imóvel é rastreado mais em meses de alto preço.')
    L('> Isso indica **viés de amostragem**: temos mais dados de alta temporada.')
    L('> Para uma estimativa realista, seria necessário preços de 12 meses completos.')
else:
    L('> O cenário sazonal gera **menos receita** porque captura os meses de baixa.')
L('')
L('**Limitação importante:** Temos apenas 4 meses de dados (Jan-Abr 2025).')
L('O pico de verão (dez-fev) está sub-representado em janeiro (só 23 dias de coleta).')
L('Uma estimativa de receita anual precisa de dados de 12 meses completos para ser confiável.')
L('')

# Grafico 6
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].scatter(comp_receita['receita_fixa']/1000, comp_receita['receita_sazonal']/1000, alpha=0.3, s=10)
max_val = max(comp_receita['receita_fixa'].max(), comp_receita['receita_sazonal'].max()) / 1000
axes[0].plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='Linha x=y')
axes[0].set_xlabel('Receita fixa (R$ mil)')
axes[0].set_ylabel('Receita sazonal (R$ mil)')
axes[0].set_title('Fixa vs Sazonal por Imóvel')
axes[0].legend()

axes[1].hist(comp_receita['diferenca_pct'], bins=30, color='#4CAF50', edgecolor='white', alpha=0.8)
axes[1].axvline(0, color='red', linestyle='--')
axes[1].axvline(comp_receita['diferenca_pct'].median(), color='blue', linestyle='--', label=f'Mediana: {comp_receita["diferenca_pct"].median():+.1f}%')
axes[1].set_xlabel('Diferença (sazonal - fixa) %')
axes[1].set_ylabel('Nº de imóveis')
axes[1].set_title('Distribuição da Diferença')
axes[1].legend()
save_fig('06_impacto_receita.png')

# =============================================
# GERAR RELATORIO
# =============================================
L('---')
L('')
L('*Análise gerada por analise_sazonalidade.py*')
L(f'*{len(df_f)} registros de preço | {df_f["airbnb_listing_id"].nunique()} imóveis | Jan-Abr 2025*')
L('')
L('### Gráficos Gerados')
L('')
L('| Arquivo | Descrição |')
L('|---------|-----------|')
L('| `01_sazonalidade_geral.png` | Preço x Volume mensal |')
L('| `02_sazonalidade_tipo.png` | Sazonalidade por tipo |')
L('| `03_sazonalidade_quartos.png` | Sazonalidade por quartos |')
L('| `04_sazonalidade_bairros.png` | Sazonalidade por bairro |')
L('| `05_amplitude_por_imovel.png` | Distribuição de amplitude |')
L('| `06_impacto_receita.png` | Fixa vs Sazonal |')

report = '\n'.join(lines)

output_path = os.path.join(os.path.dirname(__file__), 'analise_sazonalidade.md')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(report)

print(f'\nRelatório salvo: {output_path}')
print(f'Tamanho: {len(report):,} caracteres')
print(f'Gráficos: {GRAPH_DIR}/')
print(f'6 figuras geradas')
