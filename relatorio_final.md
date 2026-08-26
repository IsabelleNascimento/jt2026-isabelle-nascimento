# Relatório Final - Análise de Investimento em Itapema/SC

**Hackathon JT 2026 - Seazone**

---

## 1. Resumo Executivo

Este relatório analisa o mercado de aluguel de curta duração em Itapema/SC
para orientar decisões de investimento da Seazone. Foram analisados **873** imóveis
com dados do Airbnb e VivaReal, utilizando **mediana** (não média) para evitar
distorção por outliers, e filtro estatístico P1-P99.

- **873** imóveis únicos com dados de preço válidos
- **826** apartamentos (95%)
- **530** guest favorites (61%)
- **Superhosts:** 44% dos imóveis
- Preço diário mediano: **R$ 580**
- Receita anual mediana: **R$ 135,720**
- ROI líquido mediano: **9.3%**
- Payback mediano: **10.8 anos**

**Respostas rápidas:**

| Pergunta | Resposta |
|----------|----------|
| Melhor perfil? | Apartamento, 2 quartos, 1-2 banheiros |
| Melhor localização? | Tabuleiro dos Oliveiras (ROI 17%), Morretes (14%) |
| Características-chave? | Superhost (-12% receita), Guest favorite (rating 4.96) |
| O que comprar? | Apartamento 1-2q em Tabuleiro dos Oliveiras ou Centro |

---

## 2. Metodologia

| Item | Detalhe |
|------|---------|
| Fonte de dados | Airbnb (Details, Prices, Hosts, Mesh) + VivaReal |
| Período | Dados históricos de preço Airbnb + listagens VivaReal |
| Ocupação estimada | 65% (premissa conservadora) |
| Medida central | Mediana (robusta a outliers) |
| Filtro de outliers | Percentis P1-P99 do preço diário |
| Dados insuficientes | Removidos imóveis com <30 dias de preço |
| Deduplicação | Cada imóvel contado uma única vez (sem duplicatas por data) |
| ROI calculado | Receita líquida (receita - condomínio - IPTU) / Preço de venda VivaReal |
| Payback | Preço de venda / Receita líquida anual |

**Limitação — Sazonalidade e ocupação:**
A análise de preços rastreados (Jan-Abr 2025) revelou forte sazonalidade em Itapema,
com amplitude de 1,6x entre o pico de verão (R$ 800/noite em janeiro) e o vale de outono
(R$ 490/noite em abril). Apartamentos são mais sazonais (amplitude 1,7x) que casas (1,5x),
e 69% dos imóveis oscilam mais de 50% entre meses. No entanto, os dados disponíveis cobrem
apenas 4 meses (Janeiro a Abril), não incluem a alta temporada completa (dezembro a fevereiro)
e não dispõem de taxa de ocupação real (o Airbnb não fornece status de disponibilidade nestas tabelas).
Por isso, mantemos a premissa de **ocupação fixa de 65%** nesta análise.
Estimativas de receita anual baseadas em apenas 4 meses de preço devem ser interpretadas
como indicativas, não como forecast preciso.

---

## 3. Qual seria o melhor perfil de imóvel para investir?

### 3.1 Tipo de Anúncio

| listing_type   |   n |   preco_mediano |   receita |   roi |   payback |   rating |
|:---------------|----:|----------------:|----------:|------:|----------:|---------:|
| apartamento    | 826 |           584.5 |    136773 |  9.29 |     10.8  |     4.94 |
| casa           |  38 |           500   |    117000 |  9.22 |     10.85 |     4.88 |
| hotel          |   1 |           330   |     77220 |  8.69 |     11.5  |     5    |
| outros         |   8 |           205   |     47970 |  5.38 |     18.85 |     4.96 |

> **Conclusão:** Apartamentos dominam (95% do mercado) com ROI de 9.3% e payback de 10.8 anos.
> Apartamentos superam casas em receita anual (R$ 136,773 vs R$ 117,000) e em ROI (9.3% vs 9.2%).
> **Nota sobre ROI:** O cálculo de ROI utiliza apenas condomínio e IPTU como custos.
> Podem existir taxas adicionais não capturadas (seguro, manutenção, administração, vacancy além da premissa de 65%),
> o que pode superestimar o ROI real. Esta é uma limitação da análise.

### 3.2 Quantidade de Quartos

| grupo_quartos   |   n |   preco |   receita |   roi |   payback |   rating | favorito   | superhost   |     preco_venda |
|:----------------|----:|--------:|----------:|------:|----------:|---------:|:-----------|:------------|----------------:|
| Studio/0        |   8 |     435 |    101790 |  5.58 |      18.2 |     4.88 | 50.0%      | 62.0%       |      1.825e+06  |
| 1 quarto        | 114 |     427 |     99918 | 11.08 |       9   |     4.91 | 52.0%      | 31.0%       | 890000          |
| 2 quartos       | 315 |     472 |    110448 | 10.42 |       9.6 |     4.93 | 62.0%      | 46.0%       |      1.075e+06  |
| 3 quartos       | 366 |     680 |    159120 |  8.36 |      12   |     4.94 | 65.0%      | 47.0%       |      1.8809e+06 |
| 4+ quartos      |  70 |    1000 |    234000 |  5.65 |      17.7 |     4.92 | 47.0%      | 36.0%       |      3.6e+06    |

> **Sweet spot: 2 quartos** — melhor equilíbrio entre ROI (10.4%), payback (9.6a) e receita (R$ 110,448).
> 1 quarto tem ROI levemente menor mas entrada ~17% mais barata (R$ 890,000 vs R$ 1,075,000).
> 3+ quartos: receita alta mas ROI cai e payback sobe.

### 3.3 Banheiros

|   number_of_bathrooms |   n |   preco |   receita |   roi |   payback |
|----------------------:|----:|--------:|----------:|------:|----------:|
|                     0 |   8 |   662.5 |    155025 |  9.88 |     10.2  |
|                     1 | 196 |   408.5 |     95589 | 10.58 |      9.45 |
|                     2 | 460 |   550   |    128700 |  8.99 |     11.1  |
|                     3 | 162 |   799.7 |    187130 |  8.95 |     11.15 |
|                     4 |  40 |   944.5 |    221013 |  8.59 |     11.65 |

> **1 banheiro = melhor ROI (10.6%)** e payback mais curto (9.4 anos).
> 2 banheiros: maior volume de imóveis (460) e receita moderadamente superior (R$ 128,700 vs R$ 95,589).

### 3.4 Política de Animais

| permite_animais   |   n |   preco |   receita |   roi |   reviews |
|:------------------|----:|--------:|----------:|------:|----------:|
| Nao               | 450 |  582.33 |    136266 |  9.52 |        14 |
| Sim               | 423 |  578    |    135252 |  8.95 |        20 |

> Diferença de receita mínima (~1%). Porém, imóveis que permitem pets recebem **43% mais reviews**
> — indicando maior demanda, mesmo sem cobrar mais.

### 3.5 Guest Favorite

| is_guest_favorite   |   n |   preco |   receita |   roi |   rating |   reviews | superhost   |
|:--------------------|----:|--------:|----------:|------:|---------:|----------:|:------------|
| False               | 343 |     600 |    140400 |  9.58 |     4.83 |        12 | 23.0%       |
| True                | 530 |     550 |    128700 |  9.1  |     4.96 |        19 | 57.0%       |

> Favoritos têm rating 4.96 vs 4.83 e 58% mais reviews.
> Porém, receita 8% menor — possivelmente imóveis menores/melhor avaliados.
> **Métrica mais importante:** busque imóveis com rating > 4.9.

### 3.6 Superhost

| is_superhost   |   n |   preco |   receita |   roi |   payback |   rating |   reviews |
|:---------------|----:|--------:|----------:|------:|----------:|---------:|----------:|
| False          | 492 |     600 |    140400 |  9.48 |     10.55 |     4.93 |        12 |
| True           | 381 |     531 |    124254 |  8.86 |     11.3  |     4.94 |        26 |

> Nesta amostra, superhosts cobram R$ 531/noite vs R$ 600 (-12%) e faturam R$ 124,254/ano vs R$ 140,400 (-12%).
> Porém, superhosts têm mais reviews (26.0 vs 12.0) e estão presentes em 44% dos imóveis.
> **Hipótese (não testada):** O preço/receita menor pode refletir que superhosts nesta amostra
> gerenciam imóveis menores ou em bairros com menor valorização, focando em volume de reviews
> e ocupação ao invés de preço alto. Alternativamente, o status de superhost pode ser mais
> acessível para imóveis com ticket menor. Seria necessário controlar por tipo, tamanho e bairro
> para validar se o efeito superhost é real ou resultado de composição da amostra.

### 3.7 Perfil Ideal Consolidado

| Característica | Recomendação | Justificativa |
|----------------|--------------|---------------|
| Tipo | Apartamento | 95% do mercado, melhor ROI, mais liquidez |
| Quartos | 1-2 quartos | ROI 10-11%, payback 9-10 anos |
| Banheiros | 1 banheiro | ROI 10.6%, payback 9 anos (dados limpos) |
| Animais | Permitir | Demanda maior, custo zero |
| Superhost | Buscar imóveis com histórico de superhost | Mais reviews e visibilidade |
| Rating alvo | > 4.9 | Correlaciona com favoritos e demanda |

---

## 4. Em qual localização o imóvel teria a melhor receita?

### 4.1 Ranking de Bairros por Receita e ROI

| suburb                  |   n |   preco |   receita |   roi |   payback |   rating |   quartos_medio |      preco_venda |
|:------------------------|----:|--------:|----------:|------:|----------:|---------:|----------------:|-----------------:|
| Varzea                  |   1 | 2000    |    468000 | 52.06 |      1.9  |     5    |            5    | 899000           |
| Tabuleiro dos Oliveiras |  16 |  642.81 |    150418 | 17.3  |      5.75 |     5    |            2.5  | 782900           |
| Ilhota                  |   9 |  500    |    117000 | 16.38 |      6.1  |     4.97 |            2.33 | 500000           |
| Morretes                |  74 |  485    |    113490 | 14.24 |      7    |     4.95 |            2.18 | 750000           |
| Casa Branca             |  13 |  350    |     81900 | 11.59 |      8.6  |     4.91 |            2.15 | 676450           |
| Centro                  | 193 |  580    |    135720 | 10.03 |     10    |     4.91 |            1.9  |      1.105e+06   |
| Canto da Praia          |   7 |  600    |    140400 |  9.17 |     10.9  |     4.94 |            2.29 |      1.22181e+06 |
| Meia Praia              | 560 |  598.5  |    140049 |  8.36 |     12    |     4.94 |            2.66 |      1.8809e+06  |

> **Nota:** Bairros com menos de 10 imóveis podem ter ROI distorcido por amostra pequena.
> Várzea (n=1), Ilhota (n=9) e Canto da Praia (n=7) devem ser interpretados com cautela.

### 4.2 Top 5 por ROI (mínimo 10 imóveis)

| suburb                  |   n |   preco |   receita |   roi |   payback |   rating |   quartos_medio |     preco_venda |
|:------------------------|----:|--------:|----------:|------:|----------:|---------:|----------------:|----------------:|
| Tabuleiro dos Oliveiras |  16 |  642.81 |    150418 | 17.3  |      5.75 |     5    |            2.5  | 782900          |
| Morretes                |  74 |  485    |    113490 | 14.24 |      7    |     4.95 |            2.18 | 750000          |
| Casa Branca             |  13 |  350    |     81900 | 11.59 |      8.6  |     4.91 |            2.15 | 676450          |
| Centro                  | 193 |  580    |    135720 | 10.03 |     10    |     4.91 |            1.9  |      1.105e+06  |
| Meia Praia              | 560 |  598.5  |    140049 |  8.36 |     12    |     4.94 |            2.66 |      1.8809e+06 |

### 4.3 Top 5 por Receita Anual

| suburb                  |   n |   preco |   receita |   roi |   payback |   rating |   quartos_medio |      preco_venda |
|:------------------------|----:|--------:|----------:|------:|----------:|---------:|----------------:|-----------------:|
| Varzea                  |   1 | 2000    |    468000 | 52.06 |      1.9  |     5    |            5    | 899000           |
| Tabuleiro dos Oliveiras |  16 |  642.81 |    150418 | 17.3  |      5.75 |     5    |            2.5  | 782900           |
| Canto da Praia          |   7 |  600    |    140400 |  9.17 |     10.9  |     4.94 |            2.29 |      1.22181e+06 |
| Meia Praia              | 560 |  598.5  |    140049 |  8.36 |     12    |     4.94 |            2.66 |      1.8809e+06  |
| Centro                  | 193 |  580    |    135720 | 10.03 |     10    |     4.91 |            1.9  |      1.105e+06   |

> **Melhor receita:** Tabuleiro dos Oliveiras (R$ 150,418), Centro (R$ 135,720) e Meia Praia (R$ 140,049)
> **Melhor ROI (com dados confiáveis):** Tabuleiro dos Oliveiras (17.3%), Morretes (14.2%), Casa Branca (11.6%)
> **Melhor equilíbrio:** Centro — maior oferta (n=193.0), ROI decente, alta liquidez

---

## 5. Quais características explicam as melhores receitas?

### 5.1 Impacto de Cada Variável na Receita

|    | Variável             |   Impacto R$ | Detalhe             |
|---:|:---------------------|-------------:|:--------------------|
|  2 | Quartos (3q vs 2q)   |        48672 | +R$ 48,672          |
|  5 | Banheiros (2b vs 1b) |        33111 | +R$ 33,111          |
|  0 | Tipo (casa vs apt)   |        19773 | Casa: +R$ -19,773   |
|  3 | Superhost            |        16146 | +R$ -16,146 (+-12%) |
|  4 | Guest Favorite       |        11700 | -8%                 |
|  1 | Quartos (2q vs 1q)   |        10530 | +R$ 10,530          |
|  6 | Permite animais      |         1014 | -1%                 |

### 5.2 Correlações-Chave

| Fator | Efeito na Receita | Efeito no ROI | Efeito na Demanda |
|-------|-------------------|---------------|-------------------|
| Mais quartos | ↑↑↑ Forte | ↓ (imóvel mais caro) | ↑ Moderado |
| Mais banheiros | ↑ Moderado | ↓ (imóvel mais caro) | — Neutro |
| Superhost | Variável (ver 3.6) | ↑ Moderado | ↑↑ Forte (+117% reviews) |
| Guest Favorite | ↓ Leve | ↓ Leve | ↑↑↑ Forte (+58% reviews) |
| Permite animais | — Neutro | ↓ Leve | ↑↑ Forte (+43% reviews) |
| Localização (bairro) | ↑↑↑ Muito forte | ↑↑↑ Determinante | — Variável |

> **Hierarquia de impacto:** Localização > Tipo > Quartos > Superhost > Banheiros > Animais

---

## 6. Qual imóvel a Seazone deveria comprar hoje?

### 6.1 Cenário A: Máximo ROI (Perfil Conservador)

| Critério | Especificação |
|-----------|---------------|
| Tipo | Apartamento |
| Quartos | 1-2 quartos |
| Banheiros | 1 banheiro |
| Bairro | Tabuleiro dos Oliveiras ou Morretes |
| Preço alvo | R$ 600k - R$ 900k |
| ROI esperado | 14-17% |
| Payback | 7-7 anos |
| Animais | Permitir |

**Justificativa:** ROI maximizado, entrada mais baixa, payback mais curto.
Risco menor por menor capital em jogo.

### 6.2 Cenário B: Melhor Equilíbrio (Perfil Recomendado)

| Critério | Especificação |
|-----------|---------------|
| Tipo | Apartamento |
| Quartos | 2 quartos |
| Banheiros | 1-2 banheiros |
| Bairro | Centro ou Morretes |
| Preço alvo | R$ 900k - R$ 1.2M |
| ROI esperado | 10-14% |
| Payback | 10-7 anos |
| Animais | Permitir |
| Superhost | Buscar imóveis geridos por superhosts |

**Justificativa:** Maior liquidez (Centro tem mais oferta/demanda), receita superior
às opções baratas, rating alto, e maior potencial de valorização.

### 6.3 Cenário C: Máxima Receita (Perfil Agressivo)

| Critério | Especificação |
|-----------|---------------|
| Tipo | Apartamento |
| Quartos | 3 quartos |
| Banheiros | 2-3 banheiros |
| Bairro | Morretes ou Centro |
| Preço alvo | R$ 0.8M - R$ 2.1M |
| ROI esperado | 19-8% |
| Payback | 5-12 anos |
| Receita estimada | R$ 148,590 - R$ 175,383 |
| Animais | Permitir |

**Atenção:** Este cenário baseia-se em Morretes 3q (n=10) e Centro 3q (n=42).
O número de imóveis é pequeno, tornando os valores de ROI e payback menos confiáveis.
Estes dados devem ser interpretados como indicativos, não como garantia de retorno.

**Justificativa:** Maior receita bruta (R$ 175k+/ano), mas capital maior e
payback mais longo. Indicado para investidores com mais capital disponível.

### 6.4 Justificativa Final

**Recomendação principal: Cenário B** (Apartamento 2q, Centro/Morretes)

1. **ROI competitivo** (~10%) sem exigir entrada muito baixa
2. **Maior liquidez** — Centro é o bairro com mais oferta, facilita revenda
3. **Receita sólida** — R$ 110k/ano (2q) vs R$ 100k/ano (1q)
4. **Payback gerenciável** — 9.6 anos
5. **Perfil mais procurado** — 2 quartos atende casais e famílias pequenas
6. **Potencial de superhost** — 28% dos 2q já são superhosts no Centro

---

## 7. Análise Extra: Centro — Validação da Hipótese

Uma análise preliminar interna sugeriu que **apartamentos compactos (studio/1 quarto)**
na região **Centro** seriam apostas mais eficientes. Esta seção valida essa hipótese.

### 7.1 Panorama do Centro (193 imóveis)

- Preço diário mediano: **R$ 580**
- Receita anual mediana: **R$ 135,720**
- ROI líquido mediano: **10.0%**
- Payback mediano: **10.0 anos**

### 7.2 ROI por Quartos no Centro

| grupo_quartos   |   n |   preco |   receita |   roi |   payback |   rating | favorito   |    preco_venda |
|:----------------|----:|--------:|----------:|------:|----------:|---------:|:-----------|---------------:|
| 1 quarto        |  79 |   450   |    105300 | 11.21 |      8.9  |     4.87 | 41.0%      | 890000         |
| 2 quartos       |  64 |   568.5 |    133029 | 11.48 |      8.7  |     4.97 | 55.0%      |      1.105e+06 |
| 3 quartos       |  42 |   749.5 |    175383 |  8.36 |     12    |     4.93 | 40.0%      |      2.1e+06   |
| 4+ quartos      |   8 |   875   |    204750 |  5.49 |     18.25 |     4.86 | 50.0%      |      3.73e+06  |

### 7.3 Favorito x Quartos no Centro (Insight-chave)

|                       |   n |   roi |   receita |   payback |   rating |
|:----------------------|----:|------:|----------:|----------:|---------:|
| ('1 quarto', False)   |  47 | 10.61 |     99918 |      9.4  |     4.77 |
| ('1 quarto', True)    |  32 | 11.87 |    111150 |      8.45 |     4.94 |
| ('2 quartos', False)  |  29 | 13.07 |    150696 |      7.6  |     4.81 |
| ('2 quartos', True)   |  35 | 10.03 |    117000 |     10    |     5    |
| ('3 quartos', False)  |  25 |  8.91 |    187200 |     11.2  |     4.83 |
| ('3 quartos', True)   |  17 |  6.69 |    140400 |     15    |     4.98 |
| ('4+ quartos', False) |   4 |  5.3  |    204750 |     18.95 |     4.72 |
| ('4+ quartos', True)  |   4 |  5.8  |    216450 |     17.35 |     4.94 |

### 7.4 Banheiros no Centro

|   number_of_bathrooms |   n |   preco |   receita |   roi |   payback |
|----------------------:|----:|--------:|----------:|------:|----------:|
|                     0 |   1 |  990    |    231660 | 11.03 |      9.1  |
|                     1 |  97 |  500    |    117000 | 12.53 |      8    |
|                     2 |  72 |  529.12 |    123815 |  8.57 |     11.7  |
|                     3 |  18 |  921    |    215514 | 10.26 |      9.75 |
|                     4 |   3 |  750    |    175500 |  6.69 |     15    |

### 7.5 Centro vs Mercado Geral (1 Quarto)

|                     |   n |   preco |   receita |   roi |   payback |   rating |
|:--------------------|----:|--------:|----------:|------:|----------:|---------:|
| Centro              |  79 |     450 |    105300 | 11.21 |       8.9 |     4.87 |
| Geral (excl Centro) |  35 |     400 |     93600 | 10.88 |       9.2 |     4.97 |

### 7.6 Veredicto: A Hipótese se Confirma?

| Aspecto | Hipótese | Resultado | Status |
|---------|----------|-----------|--------|
| 1q tem melhor ROI no Centro? | Sim | ROI 11.2% (2q tem 11.5%) | **Parcial** |
| Payback mais curto para 1q? | Sim | 8.9a (2q: 8.7a) | **Parcial** |
| Entry point menor? | Sim | R$ 0.9M vs R$ 1.1M (2q) | **Confirmado** |
| Centro competitivo vs geral? | Sim | ROI 11.2% vs geral 10.9% | **Sim** |
| 1 banheiro é sweet spot? | - | ROI 12.5%, payback 8a | **Confirmado** |

**Conclusão:** A premissa está **parcialmente correta**.
- 1 quarto no Centro tem ROI competitivo (11.2%) e entry point baixo (R$ 0.9M)
- Porém, **2 quartos** tem ROI levemente superior (11.5%) e payback similar (8.7a)
- O maior achado: **1q favorito** tem ROI de **11.9%** e payback de **8.4 anos**
- E **2q não-favorito** tem ROI de **13.1%** e payback de **7.6 anos**
- A melhor jogada não é apenas "1q no Centro", mas **1-2q com perfil de favorito**

---

## 8. Tabela Resumo Final

| Perfil | Bairro | ROI | Payback | Receita | Investimento | Risco |
|--------|--------|-----|---------|---------|--------------|-------|
| **A: Conservador** | Tab. Oliveiras/Morretes | 17-14% | 6-7a | R$ 113-150k | R$ 600k-900k | Baixo |
| **B: Equilibrado (Recomendado)** | Centro/Morretes | 10-14% | 10-7a | R$ 136k | R$ 900k-1.2M | Médio |
| **C: Agressivo** | Morretes/Centro | 19-8% | 5-12a | R$ 149-175k | R$ 1-2.5M | Médio-Alto |
| **D: Centro Compacto** | Centro | 11-11% | 9-9a | R$ 105k | R$ 0.9M | Baixo-Médio |

---

## 9. Considerações Finais

1. **Dados > Intuição:** A análise limpa revelou que casas NÃO faturam mais que
   apartamentos (artefato estatístico de dados duplicados). Sem a limpeza, a
   decisão seria errada.

2. **O bairro é o fator #1:** Tabuleiro dos Oliveiras tem ROI de 17% — maior entre
   bairros com dados confiáveis. A escolha do bairro impacta mais que qualquer outra variável.

3. **Superhost merece atenção:** Nesta amostra, superhosts cobram -12% por noite e
   faturam -12% ao ano, mas acumulam +117% mais reviews.
   O preço menor pode refletir composição da amostra (imóveis menores/menos valorizados).
   Seazone deveria investigar se o status de superhost é determinante ou se o efeito é de
   bairro/tamanho. Ação recomendada: buscar imóveis com histórico de superhost como
   sinal de gestão eficiente, não como garantia de retorno financeiro superior.

4. **Centro é competitivo para 1-2q:** A hipótese interna está parcialmente
   correta. O diferencial está em combinar 1-2 quartos com perfil de favorito.

5. **Animais = demanda:** Permitir pets não aumenta preço mas gera 43% mais
   reviews. É uma alavancagem de demanda sem custo.

6. **Payback realista:** Mesmo no melhor cenário, payback é de 7+ anos.
   Investimento de longo prazo, não especulativo.

---

*Relatório gerado automaticamente por analise consolidada*
*873 imóveis analisados | Filtro P1-P99 | Mediana como medida central*

### Gráficos de Referência

| Arquivo | Descrição |
|---------|-----------|
| `graficos/01_scatter_roi_payback.png` | Visão geral ROI vs Payback |
| `graficos/03_roi_por_bairro.png` | ROI por bairro |
| `graficos/04_heatmap_roi.png` | Heatmap quartos x bairro |
| `graficos/07_panorama_quartos.png` | Panorama por quartos |
| `graficos/08_superhost_roi.png` | Impacto do superhost |
| `graficos/09_oferta_demanda_roi.png` | Oferta vs Demanda |
| `graficos/13_animais_impacto.png` | Impacto de animais |
| `graficos/14_banheiros_impacto.png` | Impacto de banheiros |
| `graficos/15_favorito_impacto.png` | Impacto de favoritos |
| `graficos/21_tipo_overview_limpo.png` | Tipo de anúncio (limpo) |
| `graficos/27_centro_quartos.png` | Centro por quartos |
| `graficos/28_centro_favorito_quartos.png` | Centro favorito x quartos |
| `graficos/29_centro_scatter_roi_payback.png` | Centro scatter ROI |
| `graficos/30_centro_heatmap_roi.png` | Centro heatmap ROI |
| `graficos/31_centro_comparativo_1q_2q.png` | Centro 1q vs 2q |