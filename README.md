# Portal Viagens — Pipeline de Dados (Arquitetura Medallion)

Pipeline de dados que **extrai, limpa e analisa** os dados de *Viagens a Serviço*
do Portal da Transparência do Governo Federal, seguindo a **Arquitetura Medallion**
(camadas Raw → Silver → Gold) com **Python** e **MySQL**.

---

## O problema que este projeto resolve

Os dados de viagens a serviço são publicados de forma **bruta e desorganizada**:
valores com vírgula decimal, datas no formato brasileiro, campos vazios como texto
e sem qualquer garantia de integridade. Este pipeline transforma esse dado cru em
**informação confiável** para apoiar a tomada de decisão sobre os gastos públicos.

## Tecnologias e técnicas utilizadas

- **Python 3** — orquestração do pipeline
- **MySQL / MariaDB (XAMPP)** — banco de dados relacional
- **pandas** — leitura dos CSVs em blocos (chunks)
- **gdown** — download automatizado do arquivo no Google Drive
- **mysql-connector-python** — conexão do Python com o MySQL
- **matplotlib / seaborn** — visualização de dados
- **Jupyter Notebook** — análise da camada Gold
- **Arquitetura Medallion** — organização em camadas Raw, Silver e Gold
- **ETL** — Extract, Transform, Load

## Arquitetura

<!-- TODO: inserir aqui o diagrama do pipeline (Raw -> Silver -> Gold) -->

| Camada | O que é | Onde fica |
|--------|---------|-----------|
| **Raw** | Cópia fiel do CSV, tudo texto | `raw_viagem`, `raw_pagamento`, `raw_passagem`, `raw_trecho` |
| **Silver** | Dados limpos e tipados, com PK/FK | `silver_viagem`, `silver_pagamento`, `silver_passagem`, `silver_trecho` |
| **Gold** | Métricas de negócio e gráficos | `3_analise.ipynb` + tabelas `gold_*` |

## Estrutura do projeto

```
portal-viagens/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── config.py           (pronto)
├── banco.py            (pronto)
├── 0_criar_banco.sql
├── 1_extrair.py
├── 2_transformar.py
├── 3_analise.ipynb
└── data/               (dados baixados — ignorado pelo Git)
```

## Como executar

1. Clone o repositório e entre na pasta.
2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Copie `.env.example` para `.env` e preencha suas credenciais do MySQL.
5. Cole o `DRIVE_FILE_ID` no `config.py`.
6. Rode os passos na ordem:
   ```bash
   # 1) cria o banco e as tabelas (rode o SQL no phpMyAdmin do XAMPP)
   #    0_criar_banco.sql
   python 1_extrair.py       # extração + camada Raw
   python 2_transformar.py   # limpeza + camada Silver
   # abra o 3_analise.ipynb   # camada Gold + análises
   ```

## Perguntas de negócio respondidas

<!-- TODO: preencher no final, com o resumo das respostas e insights -->

## Possíveis melhorias

<!-- TODO: ex.: agendar execução, validar dados, dashboard interativo... -->

## Conclusões e insights

<!-- TODO: preencher com as conclusões extraídas dos gráficos -->
