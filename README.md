# Hackathon Jovens Talentos AI Builder 2026 — Seazone

# Hackathon Jovens Talentos AI Builder 2026 — Seazone

# Seazone - Desafio IA Builder 2026

Este repositório contém a análise de inteligência de mercado e recomendação de investimento imobiliário para a Seazone no município de Itapema (SC), integrando dados do Airbnb e do VivaReal.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
- Python 3.10+
- Git

### Passo a Passo

1. Clonar o repositório:
   ```bash
   git clone https://github.com/SEU-USUARIO/jt2026-isabelle-nascimento.git
   cd jt2026-isabelle-nascimento
   ```

2. Instalar as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Executar o script de análise:
   ```bash
   python relatorio_final.py
   ```

*Nota: Certifique-se de executar o comando sempre de dentro da pasta raiz do projeto (`jt2026-isabelle-nascimento`) para garantir a localização correta da pasta `data/`.*

---

## 📌 Resumo Executivo das Respostas

| Pergunta | Resposta Sintética |
| --- | --- |
| **1. Melhor Perfil de Imóvel?** | Apartamento de 2 quartos, 1 banheiro, aceita pets, com foco em atingir status/rating > 4.9. |
| **2. Melhor Localização?** | **Centro** (melhor equilíbrio de oferta, liquidez e receita) e **Morretes** (maior ROI, amostra menor). |
| **3. Atributos da Receita?** | Localização (fator #1), tipo e número de quartos, notas altas/Guest Favorite (demanda de ocupação) e política Pet Friendly (+43% em reviews, sem impacto relevante em preço). |
| **4. Recomendação de Compra?** | **Cenário B (Equilibrado):** Apartamento 2q no Centro/Morretes (Ticket R$ 900k–1.2M, ROI Líquido 10–14%, Payback 7–10 anos). |

---

## 💡 Veredicto sobre a Tese dos Compactos no Centro

A hipótese interna apontava studio/1 quarto no Centro como a aposta mais eficiente. A análise confirma **parcialmente**:

* **1 Quarto no Centro:** menor ticket de entrada (R$ 890k) e ROI de 11,2% — competitivo e eficiente em capital.
* **2 Quartos:** ROI geral levemente superior (10,4% vs 11,1% do 1q na base completa), maior receita absoluta (R$ 110k/ano vs R$ 100k/ano) e payback similar (~9,6 anos).
* **O real diferencial não é o tamanho, é o rating:** dentro do Centro, um 1 quarto com selo de Guest Favorite atinge ROI de 11,9%, superando a maioria dos cortes por tamanho isolado.

**Conclusão:** a tese acerta a direção (Centro compacto é competitivo), mas erra o motivo — o que gera eficiência não é o tamanho reduzido, e sim a combinação de 1–2 quartos com rating/favorito alto. Detalhamento completo na Seção 7 do relatório.

---

## 📄 Documentação Completa

* Relatório Executivo Completo: [`relatorio_final.md`](./relatorio_final.md)
* Logs de Interação com IA: Pasta [`ai-log/`](./ai-log/)

---

## 🔮 Próximos Passos & Oportunidades de Modelagem Avançada

Como o payback médio dos imóveis mapeados varia de 7 a 10 anos, a análise de viabilidade de investimento deve evoluir de um modelo estático para um modelo preditivo dinâmico. Sugere-se a implementação das seguintes frentes técnicas em ciclos futuros:

### 1. Modelagem Preditiva de Sazonalidade (Time Series Analysis)
- **Coleta de Série Temporal de 12 a 36 Meses:** Aprimorar o pipeline de dados para capturar o ciclo anual completo do litoral de SC (Dez-Fev alta; Mar-Mai média; Jun-Ago baixa; Set-Nov pré-alta).
- **Modelos de Regressão / Forecast:** Utilizar algoritmos como **Prophet (Meta)** ou **SARIMAX** para projetar a curva de diárias e taxa de ocupação mensal simulada ao longo de cada ano — desde que se obtenha dado real de disponibilidade/calendário, hoje ausente na base.

### 2. Análise de Tendência de Longo Prazo e Machine Learning
- **Apreciação Imobiliária por Bairro:** Criar um modelo de *Machine Learning* (ex: XGBoost / Random Forest) treinado com dados históricos de preço do m² (VivaReal/INCC/ITBI) para prever a valorização patrimonial por micro-região em janelas de 5 a 10 anos.
- **Detecção de Polos de Expansão Urbana:** Mapear novos eixos de infraestrutura e lançamentos imobiliários em bairros emergentes (ex: Morretes e Tabuleiro dos Oliveiras) para identificar bairros com potencial de arbitragem de capital antes do pico de valorização.

### 3. Modelo Dinâmico de LTV e Churn de Proprietários
- Integrar os modelos preditivos ao algoritmo de precificação dinâmica da Seazone para calcular a resiliência da margem de gestão do investidor frente a variações de taxa de juros (Selic) e inflação da construção civil.

