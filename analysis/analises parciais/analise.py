import pandas as pd
import os

pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)

files = [
    'data/Details_Itapema.csv',
    'data/Hosts_ids_Itapema.csv',
    'data/Mesh_Ids_Data_Itapema.csv',
    'data/Price_AV_Itapema.csv',
    'data/VivaReal_Itapema.csv'
]

def generate_markdown_table(df, filename):
    rows = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        nulos_qtd = int(df[col].isnull().sum())
        nulos_pct = round(nulos_qtd / len(df) * 100, 2)
        exemplo = df[col].dropna().iloc[0] if df[col].dropna().shape[0] > 0 else "VAZIO"
        rows.append(f"| {col} | {dtype} | {nulos_qtd} ({nulos_pct}%) | {exemplo} |")

    header = f"### Tabela de Dados — {filename}\n"
    header += "| Coluna | Tipo de Dado | Nulos (Qtd / %) | Exemplo de Valor |\n"
    header += "|--------|--------------|------------------|------------------|\n"
    return header + "\n".join(rows)

def perform_eda():
    print("Iniciando Análise Exploratória de Dados (EDA)...\n")

    md_output = "# EDA — Itapema (SC)\n\n"

    for file_path in files:
        if not os.path.exists(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            continue

        basename = os.path.basename(file_path)
        print(f"\n{'='*60}")
        print(f"  Arquivo: {basename}")
        print(f"{'='*60}")

        try:
            try:
                df = pd.read_csv(file_path)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin1')

            print(f"\nShape (Linhas, Colunas): {df.shape}")
            print(f"Duplicatas: {df.duplicated().sum()}")

            print(f"\nPrimeiras 5 linhas:")
            print(df.head().to_string())

            print(f"\nResumo Estatístico:")
            print(df.describe().to_string())

            md_output += generate_markdown_table(df, basename) + "\n\n"

        except Exception as e:
            print(f"Erro ao processar {file_path}: {e}")

    with open("eda_tables.md", "w", encoding="utf-8") as f:
        f.write(md_output)
    print(f"\nTabelas Markdown salvas em: eda_tables.md")

if __name__ == "__main__":
    perform_eda()
