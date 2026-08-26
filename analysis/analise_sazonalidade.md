# Análise de Sazonalidade - Itapema/SC

**Dados:** Price_AV_Itapema.csv (preços diários rastreados pelo Airbnb)
**Período:** Janeiro a Abril 2025
**Metodologia:** Mediana de preço diário por imóvel, agrupado por mês de coleta

---

## 1. Sazonalidade Geral

| Mês | Imóveis | Preço mediano | Índice preço | Índice volume |
|-----|---------|---------------|-------------|---------------|
| 2025-01 | 675 | R$ 800 | 126 | 79 |
| 2025-02 | 899 | R$ 700 | 110 | 106 |
| 2025-03 | 931 | R$ 572 | 90 | 109 |
| 2025-04 | 806 | R$ 490 | 77 | 94 |

**Amplitude sazonal (máx/mín):** 1.6x — preços no pico são 63% maiores que no vale.
**Meses de alta (>110% do baseline):** 2025-01
**Meses de baixa (<90% do baseline):** 2025-04

## 2. Sazonalidade por Tipo de Imóvel

| Mês | apartamento | casa |
|-----|--------|--------|
| 2025-01 | R$ 800 | R$ 750 |
| 2025-02 | R$ 700 | R$ 600 |
| 2025-03 | R$ 575 | R$ 500 |
| 2025-04 | R$ 484 | R$ 500 |

**Amplitude sazonal por tipo:**
- **apartamento:** 1.7x (variação de 65%)
- **casa:** 1.5x (variação de 50%)

## 3. Sazonalidade por Nº de Quartos

| Mês | Studio/0 | 1 quarto | 2 quartos | 3+ quartos |
|-----|--------|--------|--------|--------|
| 2025-01 | R$ 585 | R$ 564 | R$ 693 | R$ 990 |
| 2025-02 | R$ 550 | R$ 545 | R$ 599 | R$ 850 |
| 2025-03 | R$ 490 | R$ 471 | R$ 490 | R$ 700 |
| 2025-04 | R$ 380 | R$ 419 | R$ 400 | R$ 570 |

**Amplitude sazonal por quartos:**
- **Studio/0:** 1.5x (variação de 54%)
- **1 quarto:** 1.3x (variação de 35%)
- **2 quartos:** 1.7x (variação de 73%)
- **3+ quartos:** 1.7x (variação de 74%)

## 4. Sazonalidade por Bairro (Top 8)

| Mês | Canto da Praia | Casa Branca | Centro | Ilhota | Meia Praia | Morretes | Tabuleiro dos Oliveiras | Varzea |
|-----|---------|---------|---------|---------|---------|---------|---------|---------|
| 2025-01 | R$ 829 | R$ 399 | R$ 749 | R$ 896 | R$ 850 | R$ 615 | R$ 702 | R$ 1,500 |
| 2025-02 | R$ 648 | R$ 318 | R$ 663 | R$ 590 | R$ 765 | R$ 542 | R$ 700 | R$ 1,500 |
| 2025-03 | R$ 518 | R$ 300 | R$ 523 | R$ 490 | R$ 600 | R$ 490 | R$ 560 | R$ 2,000 |
| 2025-04 | R$ 500 | R$ 280 | R$ 499 | R$ 400 | R$ 492 | R$ 470 | R$ 480 | R$ 1,500 |

**Amplitude sazonal por bairro:**
- **Meia Praia:** 1.7x (variação de 73%)
- **Centro:** 1.5x (variação de 50%)
- **Morretes:** 1.3x (variação de 31%)
- **Tabuleiro dos Oliveiras:** 1.5x (variação de 46%)
- **Casa Branca:** 1.4x (variação de 43%)
- **Ilhota:** 2.2x (variação de 124%)
- **Canto da Praia:** 1.7x (variação de 66%)
- **Varzea:** 1.3x (variação de 33%)

## 5. Amplitude de Preço por Imóvel

Para imóveis com dados em 2+ meses:

| Métrica | Valor |
|---------|-------|
| Imóveis com 2+ meses de dados | 952 |
| Amplitude mediana | 1.8x |
| Amplitude média | 1.9x |
| Imóveis com amplitude > 1.5x | 657 (69%) |
| Imóveis com amplitude > 2x | 346 (36%) |

**Amplitude mediana por tipo:**
- **apartamento:** 1.8x (n=879)
- **casa:** 1.4x (n=63)

## 6. Impacto na Receita Anual Estimada

Compara dois cenários (mesmo imóvel, mesma ocupação de 65%):
- **A: Preço fixo** — mediana anual aplicada a 365 dias
- **B: Preço sazonal** — mediana mensal aplicada a cada mês

| Métrica | Valor |
|---------|-------|
| Imóveis com dados suficientes | 985 |
| Diferença mediana | -69.8% |
| Diferença média | -71.2% |
| Imóveis com receita SAZONAL > FIXA | 0 (0%) |
| Imóveis com receita FIXA > SAZONAL | 985 (100%) |

**Diferença mediana por tipo:**
- **apartamento:** -69.7% (n=907)
- **casa:** -72.7% (n=67)

**Diferença mediana por quartos:**

### Interpretação

> O cenário sazonal gera **menos receita** porque captura os meses de baixa.

**Limitação importante:** Temos apenas 4 meses de dados (Jan-Abr 2025).
O pico de verão (dez-fev) está sub-representado em janeiro (só 23 dias de coleta).
Uma estimativa de receita anual precisa de dados de 12 meses completos para ser confiável.

---

*Análise gerada por analise_sazonalidade.py*
*115991 registros de preço | 985 imóveis | Jan-Abr 2025*

### Gráficos Gerados

| Arquivo | Descrição |
|---------|-----------|
| `01_sazonalidade_geral.png` | Preço x Volume mensal |
| `02_sazonalidade_tipo.png` | Sazonalidade por tipo |
| `03_sazonalidade_quartos.png` | Sazonalidade por quartos |
| `04_sazonalidade_bairros.png` | Sazonalidade por bairro |
| `05_amplitude_por_imovel.png` | Distribuição de amplitude |
| `06_impacto_receita.png` | Fixa vs Sazonal |