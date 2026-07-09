from decimal import Decimal, InvalidOperation
from datetime import datetime

import banco


def texto_para_decimal(valor):
    valor = (valor or "").strip()
    if not valor:
        return None
    try:
        return Decimal(valor.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def texto_para_data(valor):
    valor = (valor or "").strip()
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%d/%m/%Y").date()
    except ValueError:
        return None


def buscar_raw(conexao, sql):
    cursor = conexao.cursor()
    cursor.execute(sql)
    linhas = cursor.fetchall()
    cursor.close()
    return linhas


def transformar_viagem(conexao):
    linhas = buscar_raw(conexao, """
        SELECT id_viagem, num_proposta, situacao, viagem_urgente, cod_orgao_superior,
               nome_orgao_superior, nome_viajante, cargo, data_inicio, data_fim,
               destinos, motivo, valor_diarias, valor_passagens, valor_devolucao,
               valor_outros_gastos
        FROM raw_viagem
    """)

    preparadas = []
    for linha in linhas:
        (id_viagem, num_proposta, situacao, viagem_urgente, cod_orgao_superior,
         nome_orgao_superior, nome_viajante, cargo, data_inicio, data_fim,
         destinos, motivo, valor_diarias, valor_passagens, valor_devolucao,
         valor_outros_gastos) = linha

        d_inicio = texto_para_data(data_inicio)
        d_fim = texto_para_data(data_fim)
        v_diarias = texto_para_decimal(valor_diarias) or Decimal("0")
        v_passagens = texto_para_decimal(valor_passagens) or Decimal("0")
        v_devolucao = texto_para_decimal(valor_devolucao) or Decimal("0")
        v_outros = texto_para_decimal(valor_outros_gastos) or Decimal("0")

        valor_total = v_diarias + v_passagens + v_devolucao + v_outros
        duracao_dias = (d_fim - d_inicio).days if d_inicio and d_fim else None

        preparadas.append((
            id_viagem, num_proposta, situacao, viagem_urgente, cod_orgao_superior,
            nome_orgao_superior or "NAO INFORMADO", nome_viajante, cargo,
            d_inicio, d_fim, destinos, motivo,
            v_diarias, v_passagens, v_devolucao, v_outros,
            valor_total, duracao_dias,
        ))

    banco.executar(conexao, "SET FOREIGN_KEY_CHECKS=0")
    banco.executar(conexao, "TRUNCATE TABLE silver_trecho")
    banco.executar(conexao, "TRUNCATE TABLE silver_passagem")
    banco.executar(conexao, "TRUNCATE TABLE silver_pagamento")
    banco.executar(conexao, "TRUNCATE TABLE silver_viagem")
    banco.executar(conexao, "SET FOREIGN_KEY_CHECKS=1")

    sql_insert = """
        INSERT INTO silver_viagem (
            id_viagem, num_proposta, situacao, viagem_urgente, cod_orgao_superior,
            nome_orgao_superior, nome_viajante, cargo, data_inicio, data_fim,
            destinos, motivo, valor_diarias, valor_passagens, valor_devolucao,
            valor_outros_gastos, valor_total, duracao_dias
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    for inicio in range(0, len(preparadas), 2000):
        banco.inserir_em_lote(conexao, sql_insert, preparadas[inicio:inicio + 2000])

    print(f"[silver_viagem] OK - {len(preparadas)} linhas.")


def transformar_pagamento(conexao):
    linhas = buscar_raw(conexao, """
        SELECT id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora,
               tipo_pagamento, valor
        FROM raw_pagamento
    """)

    ids_validos = obter_ids_viagem(conexao)
    preparadas = []
    for id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora, tipo_pagamento, valor in linhas:
        if id_viagem not in ids_validos:
            continue
        preparadas.append((
            id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora,
            tipo_pagamento or "NAO INFORMADO", texto_para_decimal(valor) or Decimal("0"),
        ))

    sql_insert = """
        INSERT INTO silver_pagamento (
            id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora,
            tipo_pagamento, valor
        ) VALUES (%s,%s,%s,%s,%s,%s)
    """
    for inicio in range(0, len(preparadas), 2000):
        banco.inserir_em_lote(conexao, sql_insert, preparadas[inicio:inicio + 2000])

    print(f"[silver_pagamento] OK - {len(preparadas)} linhas.")


def transformar_passagem(conexao):
    linhas = buscar_raw(conexao, """
        SELECT id_viagem, meio_transporte, pais_origem_ida, uf_origem_ida,
               cidade_origem_ida, pais_destino_ida, uf_destino_ida, cidade_destino_ida,
               valor_passagem, taxa_servico, data_emissao
        FROM raw_passagem
    """)

    ids_validos = obter_ids_viagem(conexao)
    preparadas = []
    for (id_viagem, meio_transporte, pais_origem_ida, uf_origem_ida, cidade_origem_ida,
         pais_destino_ida, uf_destino_ida, cidade_destino_ida, valor_passagem,
         taxa_servico, data_emissao) in linhas:
        if id_viagem not in ids_validos:
            continue
        preparadas.append((
            id_viagem, meio_transporte, pais_origem_ida, uf_origem_ida, cidade_origem_ida,
            pais_destino_ida, uf_destino_ida, cidade_destino_ida,
            texto_para_decimal(valor_passagem) or Decimal("0"),
            texto_para_decimal(taxa_servico) or Decimal("0"),
            texto_para_data(data_emissao),
        ))

    sql_insert = """
        INSERT INTO silver_passagem (
            id_viagem, meio_transporte, pais_origem_ida, uf_origem_ida, cidade_origem_ida,
            pais_destino_ida, uf_destino_ida, cidade_destino_ida, valor_passagem,
            taxa_servico, data_emissao
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    for inicio in range(0, len(preparadas), 2000):
        banco.inserir_em_lote(conexao, sql_insert, preparadas[inicio:inicio + 2000])

    print(f"[silver_passagem] OK - {len(preparadas)} linhas.")


def transformar_trecho(conexao):
    linhas = buscar_raw(conexao, """
        SELECT id_viagem, sequencia_trecho, origem_data, origem_uf, origem_cidade,
               destino_data, destino_uf, destino_cidade, meio_transporte, numero_diarias
        FROM raw_trecho
    """)

    ids_validos = obter_ids_viagem(conexao)
    vistos = set()
    preparadas = []
    for (id_viagem, sequencia_trecho, origem_data, origem_uf, origem_cidade,
         destino_data, destino_uf, destino_cidade, meio_transporte, numero_diarias) in linhas:
        if id_viagem not in ids_validos:
            continue
        try:
            seq = int(sequencia_trecho) if sequencia_trecho else None
        except ValueError:
            seq = None
        chave = (id_viagem, seq)
        if chave in vistos:
            continue
        vistos.add(chave)
        preparadas.append((
            id_viagem, seq, texto_para_data(origem_data), origem_uf, origem_cidade,
            texto_para_data(destino_data), destino_uf, destino_cidade, meio_transporte,
            texto_para_decimal(numero_diarias) or Decimal("0"),
        ))

    sql_insert = """
        INSERT INTO silver_trecho (
            id_viagem, sequencia_trecho, origem_data, origem_uf, origem_cidade,
            destino_data, destino_uf, destino_cidade, meio_transporte, numero_diarias
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    for inicio in range(0, len(preparadas), 2000):
        banco.inserir_em_lote(conexao, sql_insert, preparadas[inicio:inicio + 2000])

    print(f"[silver_trecho] OK - {len(preparadas)} linhas.")


def obter_ids_viagem(conexao):
    cursor = conexao.cursor()
    cursor.execute("SELECT id_viagem FROM silver_viagem")
    ids = {linha[0] for linha in cursor.fetchall()}
    cursor.close()
    return ids


def main():
    conexao = None
    try:
        conexao = banco.conectar()
        transformar_viagem(conexao)
        transformar_pagamento(conexao)
        transformar_passagem(conexao)
        transformar_trecho(conexao)
        print("\nFase 2 concluida: camada SILVER carregada com sucesso.")
    except Exception as erro:
        print(f"\n[ERRO] a transformacao falhou: {erro}")
    finally:
        if conexao is not None:
            conexao.close()


if __name__ == "__main__":
    main()