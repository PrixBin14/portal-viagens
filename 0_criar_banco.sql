-- =====================================================================
-- 0_criar_banco.sql
-- ---------------------------------------------------------------------
-- Cria o banco 'transparencia' e as 8 tabelas do pipeline:
--   4 tabelas RAW    -> copia fiel do CSV (tudo VARCHAR, sem constraints)
--   4 tabelas SILVER -> dados tipados, com PK, FK e constraints
-- Banco: MySQL / MariaDB (XAMPP)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS transparencia
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE transparencia;

-- ---------------------------------------------------------------------
-- Limpeza: derruba as tabelas na ordem INVERSA das dependencias
-- (as "filhas" com FK primeiro, depois a "mae" silver_viagem).
-- Assim o script pode ser re-executado sem erro de chave estrangeira.
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS silver_trecho;
DROP TABLE IF EXISTS silver_passagem;
DROP TABLE IF EXISTS silver_pagamento;
DROP TABLE IF EXISTS silver_viagem;
DROP TABLE IF EXISTS raw_trecho;
DROP TABLE IF EXISTS raw_passagem;
DROP TABLE IF EXISTS raw_pagamento;
DROP TABLE IF EXISTS raw_viagem;

-- =====================================================================
-- CAMADA RAW  -  copia fiel dos CSVs (todas as colunas VARCHAR)
-- Replica o CSV inteiro, inclusive colunas que a Silver nao usa
-- (cpf, funcao, dados de volta da passagem, etc.).
-- =====================================================================

CREATE TABLE raw_viagem (
    id_viagem               VARCHAR(255),
    num_proposta            VARCHAR(255),
    situacao                VARCHAR(255),
    viagem_urgente          VARCHAR(255),
    justificativa_urgencia  VARCHAR(4000),
    cod_orgao_superior      VARCHAR(255),
    nome_orgao_superior     VARCHAR(255),
    cod_orgao_solicitante   VARCHAR(255),
    nome_orgao_solicitante  VARCHAR(255),
    cpf_viajante            VARCHAR(255),
    nome_viajante           VARCHAR(255),
    cargo                   VARCHAR(255),
    funcao                  VARCHAR(255),
    descricao_funcao        VARCHAR(255),
    data_inicio             VARCHAR(255),
    data_fim                VARCHAR(255),
    destinos                VARCHAR(4000),
    motivo                  VARCHAR(4000),
    valor_diarias           VARCHAR(255),
    valor_passagens         VARCHAR(255),
    valor_devolucao         VARCHAR(255),
    valor_outros_gastos     VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE raw_pagamento (
    id_viagem            VARCHAR(255),
    num_proposta         VARCHAR(255),
    cod_orgao_superior   VARCHAR(255),
    nome_orgao_superior  VARCHAR(255),
    cod_orgao_pagador    VARCHAR(255),
    nome_orgao_pagador   VARCHAR(255),
    cod_ug_pagadora      VARCHAR(255),
    nome_ug_pagadora     VARCHAR(255),
    tipo_pagamento       VARCHAR(255),
    valor                VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE raw_passagem (
    id_viagem             VARCHAR(255),
    num_proposta          VARCHAR(255),
    meio_transporte       VARCHAR(255),
    pais_origem_ida       VARCHAR(255),
    uf_origem_ida         VARCHAR(255),
    cidade_origem_ida     VARCHAR(255),
    pais_destino_ida      VARCHAR(255),
    uf_destino_ida        VARCHAR(255),
    cidade_destino_ida    VARCHAR(255),
    pais_origem_volta     VARCHAR(255),
    uf_origem_volta       VARCHAR(255),
    cidade_origem_volta   VARCHAR(255),
    pais_destino_volta    VARCHAR(255),
    uf_destino_volta      VARCHAR(255),
    cidade_destino_volta  VARCHAR(255),
    valor_passagem        VARCHAR(255),
    taxa_servico          VARCHAR(255),
    data_emissao          VARCHAR(255),
    hora_emissao          VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE raw_trecho (
    id_viagem         VARCHAR(255),
    num_proposta      VARCHAR(255),
    sequencia_trecho  VARCHAR(255),
    origem_data       VARCHAR(255),
    origem_pais       VARCHAR(255),
    origem_uf         VARCHAR(255),
    origem_cidade     VARCHAR(255),
    destino_data      VARCHAR(255),
    destino_pais      VARCHAR(255),
    destino_uf        VARCHAR(255),
    destino_cidade    VARCHAR(255),
    meio_transporte   VARCHAR(255),
    numero_diarias    VARCHAR(255),
    missao            VARCHAR(255)
) ENGINE=InnoDB;

-- =====================================================================
-- CAMADA SILVER  -  dados tipados, com PK, FK e constraints
-- Cada tabela Silver tem, ALEM da PK (e da FK quando aplicavel),
-- 2 constraints extras declaradas dentro do CREATE TABLE.
-- =====================================================================

-- silver_viagem e a tabela "mae": precisa existir ANTES das que a
-- referenciam por chave estrangeira (pagamento, passagem, trecho).
CREATE TABLE silver_viagem (
    id_viagem            VARCHAR(20)   NOT NULL,
    num_proposta         VARCHAR(20),
    situacao             VARCHAR(50),
    viagem_urgente       VARCHAR(5),
    cod_orgao_superior   VARCHAR(20),
    nome_orgao_superior  VARCHAR(255)  NOT NULL,        -- constraint extra 1 (NOT NULL)
    nome_viajante        VARCHAR(255),
    cargo                VARCHAR(255),
    data_inicio          DATE,
    data_fim             DATE,
    destinos             VARCHAR(4000),
    motivo               VARCHAR(4000),
    valor_diarias        DECIMAL(10,2),
    valor_passagens      DECIMAL(10,2),
    valor_devolucao      DECIMAL(10,2),
    valor_outros_gastos  DECIMAL(10,2),
    valor_total          DECIMAL(12,2),                 -- coluna calculada (2_transformar.py)
    duracao_dias         INT,                           -- coluna calculada (2_transformar.py)
    CONSTRAINT pk_viagem PRIMARY KEY (id_viagem),
    CONSTRAINT chk_viagem_diarias CHECK (valor_diarias >= 0)  -- constraint extra 2 (CHECK)
) ENGINE=InnoDB;

CREATE TABLE silver_pagamento (
    id_pagamento        INT           NOT NULL AUTO_INCREMENT,
    id_viagem           VARCHAR(20)   NOT NULL,
    num_proposta        VARCHAR(20),
    nome_orgao_pagador  VARCHAR(255),
    nome_ug_pagadora    VARCHAR(255),
    tipo_pagamento      VARCHAR(50)   NOT NULL,         -- constraint extra 1 (NOT NULL)
    valor               DECIMAL(10,2),
    CONSTRAINT pk_pagamento PRIMARY KEY (id_pagamento),
    CONSTRAINT fk_pagamento_viagem
        FOREIGN KEY (id_viagem) REFERENCES silver_viagem (id_viagem),
    CONSTRAINT chk_pagamento_valor CHECK (valor >= 0)   -- constraint extra 2 (CHECK)
) ENGINE=InnoDB;

CREATE TABLE silver_passagem (
    id_passagem         INT           NOT NULL AUTO_INCREMENT,
    id_viagem           VARCHAR(20)   NOT NULL,
    meio_transporte     VARCHAR(50),
    pais_origem_ida     VARCHAR(60),
    uf_origem_ida       VARCHAR(40),
    cidade_origem_ida   VARCHAR(80),
    pais_destino_ida    VARCHAR(60),
    uf_destino_ida      VARCHAR(40),
    cidade_destino_ida  VARCHAR(80),
    valor_passagem      DECIMAL(10,2),
    taxa_servico        DECIMAL(10,2),
    data_emissao        DATE,
    CONSTRAINT pk_passagem PRIMARY KEY (id_passagem),
    CONSTRAINT fk_passagem_viagem
        FOREIGN KEY (id_viagem) REFERENCES silver_viagem (id_viagem),
    CONSTRAINT chk_passagem_valor CHECK (valor_passagem >= 0),  -- constraint extra 1 (CHECK)
    CONSTRAINT chk_passagem_taxa  CHECK (taxa_servico   >= 0)   -- constraint extra 2 (CHECK)
) ENGINE=InnoDB;

CREATE TABLE silver_trecho (
    id_trecho         INT           NOT NULL AUTO_INCREMENT,
    id_viagem         VARCHAR(20)   NOT NULL,
    sequencia_trecho  INT,
    origem_data       DATE,
    origem_uf         VARCHAR(40),
    origem_cidade     VARCHAR(80),
    destino_data      DATE,
    destino_uf        VARCHAR(40),
    destino_cidade    VARCHAR(80),
    meio_transporte   VARCHAR(50),
    numero_diarias    DECIMAL(10,2),
    CONSTRAINT pk_trecho PRIMARY KEY (id_trecho),
    CONSTRAINT fk_trecho_viagem
        FOREIGN KEY (id_viagem) REFERENCES silver_viagem (id_viagem),
    CONSTRAINT chk_trecho_diarias CHECK (numero_diarias >= 0),      -- constraint extra 1 (CHECK)
    CONSTRAINT uq_trecho_seq UNIQUE (id_viagem, sequencia_trecho)   -- constraint extra 2 (UNIQUE)
) ENGINE=InnoDB;
