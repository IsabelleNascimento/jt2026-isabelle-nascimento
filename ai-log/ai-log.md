# Log de Interação com IA

**Projeto:** Hackathon Jovens Talentos AI Builder 2026 - Seazone
**Objetivo:** Análise de inteligência de mercado e recomendação de investimento imobiliário em Itapema/SC (dados Airbnb + VivaReal)
**Ferramenta de IA:** opencode (assistente de código) — big-pickle

---

## 1. Visão Geral do Processo

Este documento registra como a IA foi utilizada ao longo de todo o ciclo de vida do projeto, desde a primeira exploração dos dados até a validação do relatório final. O processo evoluiu em **itens de análise progressivos**, cada um gerando artefatos (tabelas, gráficos e conclusões) que alimentaram o relatório consolidado.

| Etapa | Fase | Artefatos Gerados |
|-------|------|-------------------|
| 1 | EDA inicial | `analise.py`, `eda_tables.md` |
| 2 | Receita e ROI | `analise_receita_roi.py` + gráficos 01-08 |
| 3 | Oferta vs Demanda | `analise_oferta_demanda.py` + gráficos 09-12 |
| 4 | Características qualitativas | `analise_caracteristicas.py` + gráficos 13-16 |
| 5 | Tipo de anúncio | `analise_tipo_anuncio.py` + gráficos 17-20 |
| 6 | Análise limpa (master) | `analise_completa_limpa.py` + gráficos 21-26 |
| 7 | Deep-dive Centro | `analise_centro.py` + gráficos 27-31 |
| 8 | Sazonalidade | `analise_sazonalidade.py/.md` + gráficos sazonais |
| 9 | Relatório consolidado | `relatorio_final.py` → `relatorio_final.md` |

---

## 2. Premissas e Decisões Tomadas com a IA

Durante o processo, a IA e o usuário negociaram e fixaram as seguintes premissas analíticas:

| Decisão | Justificativa |
|---------|---------------|
| **Mediana** como medida central (não média) | Robustez contra outliers (imóveis de alto padrão distorcem a média) |
| **Filtro P1-P99** no preço diário | Eliminar preços extremos/erros de coleta |
| Apenas imóveis com **≥30 dias de preço** | Garantir histórico mínimo para estimar receita |
| **Ocupação fixa em 65%** (`OCCUPANCY_RATE = 0.65`) | Dados não possuem status de disponibilidade (faltou `available: true/false`) |
| **Join VivaReal via suburb + bedrooms** | Não há ID direto; 99,98% dos campos `rental_price` são nulos |
| **n ≥ 10 para bairros confiáveis** | Evitar ROI distorcido (ex: Várzea com n=1 teve ROI de 52%, descartado) |
| **Parâmetro de casa (pets)** via busca em `house_rules` | "Permitido animais" |

---

## 3. Evolução da Recomendação (Iteração Guiada pela IA)

A recomendação principal **mudou ao longo do processo** graças à verificação estatística e ao questionamento do usuário:

### 3.1. Primeira versão (Várzea, incorreta)
A primeira análise apontou **Várzea** como melhor ROI (~52%), mas a auditoria revelou que **apenas 1 imóvel** sobreviveu aos filtros — amostra insuficiente. A IA aplicou o filtro mínimo `n ≥ 10` e corrigiu a recomendação para **Tabuleiro dos Oliveiras**.

### 3.2. Segunda versão (Tabuleiro dos Oliveiras/Morretes)
Com o filtro, **Tabuleiro dos Oliveiras** (ROI 17,3%, n=16) e **Morretes** (14,2%, n=74) lideravam. A recomendação priorizava esses dois bairros pelos ROI superiores.

### 3.3. Versão final (Centro + Morretes) — recomendação corrente
O usuário sinalizou uma preocupação importante: **Tabuleiro dos Oliveiras tem n=16 apenas**, uma amostra pequena que torna o ROI pouco confiável (risco de não ser reproduzível). Considerando uma abordagem **conservadora e segura**:
- **Centro (n=193)** tornou-se a **recomendação principal** — maior amostra, dados mais confiáveis, maior liquidez/mix de oferta e sazonalidade moderada.
- **Morretes (n=74)** permaneceu como **segunda opção** — ROI superior e sazonalidade menor (1,3x).
- **Tabuleiro dos Oliveiras** (n=16) foi mantido apenas como **cenário agressivo**, com aviso explícito de baixa confiabilidade amostral.

**Justificativa-chave incorporada ao relatório:** "Amostra importa tanto quanto ROI." Bairros com n pequeno devem ser tratados como indicativos, não garantias.

---

## 4. Auditorias e Correções de Consistência

A IA foi usada não só para gerar análise, mas também para **auditar a consistência interna do relatório** — garantindo que cada número citado conferisse com os dados reais.

### 4.1. Primeira auditoria — 18 divergências encontradas
Ao comparar os textos narrativos do relatório com os valores calculados no dataframe, a IA identificou **18 divergências**:

**Divergências graves (inversão de sinal / dados muito errados):**
1. Superhost indicado como "+22% receita" — na verdade **-12%**
2. "Casas têm receita bruta maior" — na verdade **apartamentos vencem**
3. "Superhosts cobram 22% mais por noite e faturam 21% mais" — na verdade **cobram/faturam menos**
4. "ROI 12,5%, payback 8 anos (1 banheiro)" — na verdade **10,6% / 9,4 anos**
5. Receita 2q "R$ 133k" — na verdade **R$ 110k**
6. Cenário C (Morretes 3q) ROI 8-10% — na verdade **18,7%**
7. Superhost "+22% no preço/noite" — na verdade **-12%**

**Divergências moderadas:** entrada 1q (~28% vs 17%), payback de perfil ideal, correlações de reviews, darocentro geral 11,7% vs 10,9%, payback cenário B, etc.

**Divergências mínimas:** contagem de banheiros (463 vs 460), % de mercado (97% vs 94,6%), small rounding diffs.

### 4.2. Correção — strings literais → f-strings
A causa raiz era que vários números haviam sido **copiados de análises anteriores** (com dados duplicados) **sem recálculo** após a limpeza. A correção consistiu em **reescrever todo texto narrativo como f-string calculado diretamente do dataframe**, eliminando números hardcoded.

### 4.3. Caso especial — Casas vs Apartamentos
Além de corrigir o número, a frase foi **reescrita estruturalmente** para refletir que apartamentos superam casas em receita e ROI. Foi adicionada uma **nota de limitação sobre o ROI**: o cálculo usa apenas condomínio + IPTU como custos, podendo haver taxas não capturadas (seguro, manutenção, administração) — um reconhecimento explícito de limitação.

### 4.4. Caso especial — Superhost invertido
Foi proposta uma **repactuação do insight**: em vez de afirmar que superhost é vantagem financeira, o relatório agora descreve o padrão real (preço e receita menores, mas **+117% mais reviews**) e levanta uma **hipótese de negócio plausível** — superhosts priorizam volume/ocupação a preços altos — **marcada explicitamente como hipótese não testada**, não como fato.

### 4.5. Segunda auditoria — ZERO divergências
Após as correções, uma segunda auditoria verificou **49 checkpoints** em todas as seções. Resultado: **ZERO DIVERGÊNCIAS** — todo número do relatório confere com os dados.

---

## 5. Análise de Sazonalidade (Estudo Complementar)

O usuário questionou se havia como mensurar sazonalidade. A IA verificou que:

- **Não existe** coluna de disponibilidade/status (`available: true/false`) em nenhuma tabela — **não é possível medir ocupação real**.
- Porém, o `Price_AV_Itapema.csv` (118.839 registros, Jan-Abr 2025) permite mensurar **sazonalidade de preço**.

**Achados da análise de sazonalidade:**

| Mês | Imóveis | Preço mediano | Índice |
|-----|---------|---------------|--------|
| Jan/25 | 675 | R$ 800 | 126 |
| Fev/25 | 899 | R$ 700 | 110 |
| Mar/25 | 931 | R$ 572 | 90 |
| Abr/25 | 806 | R$ 490 | 77 |

**Conclusões principais:**
- **Amplitude geral de 1,6x** (63% de variação entre pico e vale)
- **Apartamentos mais sazonais (1,7x)** que casas (1,5x)
- **2 quartos e 3+ quartos** têm amplitude de 1,7x
- **69% dos imóveis** mudam preço mais de 50% entre meses
- **Centro: sazonalidade 1,5x (50%); Morretes: 1,3x (31%)** — argumento usado a favor de ambas as recomendações
- **Ilhota** é o bairro mais volátil (2,2x)

**Direção de recomendação:** manter premissa de ocupação fixa de 65% (não há dados de ocupação real), mas o achado foi incorporado à **Seção 2 (Metodologia)** do relatório como **limitação analítica explícita** — Itapema é uma cidade de forte sazonalidade de verão, e os dados cobrem apenas 4 meses, sem alta temporada completa.

---

## 6. Como a IA Ajudou em Cada Tipo de Tarefa

| Tipo de Tarefa | Papel da IA |
|----------------|-------------|
| **EDA** | Explorar colunas, volumes, nulos, identificar padrões |
| **Limpeza** | Deduplicação, filtros P1-P99, merge VivaReal/Airbnb, parsing de `house_rules` |
| **Cálculo** | Receita anual, ROI líquido, payback, agregados por bairro/tipo/quartos |
| **Visualização** | 31 gráficos + 6 gráficos de sazonalidade (scatter, heatmap, boxplot, barras) |
| **Redação** | Geração de relatório markdown estruturado em 9 seções |
| **Auditoria** | Comparação automática texto↔dados, detecção de divergências |
| **Revisão crítica** | Questionar amostras pequenas, hipóteses não testadas, limitações |

---

## 7. Conclusão do Log

A utilização da IA foi **iterativa e orientada a validação**, não um processo de "deixar a IA fazer tudo". O usuário exerceu papel ativo de revisão crítica (questionando amostras pequenas e orientando a recomendação para uma abordagem conservadora), enquanto a IA forneceu:
1. Exploração e limpeza robusta dos dados.
2. Cálculos estatísticos transparentes e reproduzíveis.
3. Auditoria de consistência que **remodelou o relatório** para refletir a realidade dos dados.
4. Documentação explícita de limitações (sazonalidade, ocupação, taxa de retorno).

O artefato final é um **relatório auditado com zero divergências**, com recomendação conservadora e devidamente ressaltada.

---

*Log gerado automaticamente ao longo da sessão de interação com IA — opencode/big-pickle.*
