import zipfile

import gdown
import pandas as pd

import config
import banco


def baixar_zip():
    config.PASTA_DADOS.mkdir(exist_ok=True)
    caminho_zip = config.PASTA_DADOS / "viagens.zip"
    if caminho_zip.exists():
        print(f"[download] '{caminho_zip.name}' ja existe, pulando download.")
        return caminho_zip
    if config.DRIVE_FILE_ID.startswith("COLE_AQUI"):
        raise ValueError("DRIVE_FILE_ID nao configurado no config.py.")
    url = f"https://drive.google.com/uc?id={config.DRIVE_FILE_ID}"
    print("[download] baixando o zip do Drive...")
    gdown.download(url, str(caminho_zip), quiet=False)
    return caminho_zip


def extrair_zip(caminho_zip):
    with zipfile.ZipFile(caminho_zip) as z:
        z.extractall(config.PASTA_DADOS)


def localizar_csv(nome_csv):
    direto = config.PASTA_DADOS / nome_csv
    if direto.exists():
        return direto
    encontrados = list(config.PASTA_DADOS.rglob(nome_csv))
    if encontrados:
        return encontrados[0]
    raise FileNotFoundError(f"CSV '{nome_csv}' nao encontrado apos descompactar.")


def carregar_raw(conexao, info):
    caminho_csv = localizar_csv(info["csv"])
    tabela = info["tabela_raw"]
    banco.executar(conexao, f"TRUNCATE TABLE {tabela}")
    total = 0
    leitor = pd.read_csv(
        caminho_csv,
        sep=config.CSV_SEPARADOR,
        encoding=config.CSV_ENCODING,
        dtype=str,
        keep_default_na=False,
        chunksize=config.TAMANHO_BLOCO,
    )
    for bloco in leitor:
        n_colunas = bloco.shape[1]
        placeholders = ", ".join(["%s"] * n_colunas)
        sql_insert = f"INSERT INTO {tabela} VALUES ({placeholders})"
        linhas = [tupla for tupla in bloco.itertuples(index=False, name=None)]
        banco.inserir_em_lote(conexao, sql_insert, linhas)
        total += len(linhas)
        print(f"  [{tabela}] {total} linhas carregadas...")
    print(f"[{tabela}] OK - total de {total} linhas.")


def main():
    conexao = None
    try:
        caminho_zip = baixar_zip()
        extrair_zip(caminho_zip)
        conexao = banco.conectar()
        for info in config.ARQUIVOS.values():
            carregar_raw(conexao, info)
        print("\nFase 1 concluida: camada RAW carregada com sucesso.")
    except Exception as erro:
        print(f"\n[ERRO] a extracao falhou: {erro}")
    finally:
        if conexao is not None:
            conexao.close()


if __name__ == "__main__":
    main()