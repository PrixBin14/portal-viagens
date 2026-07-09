# Acadêmica: Priscila Campagnolo Ferreira
# Análise de dados T1

# Portal Viagens — Pipeline de Dados (Arquitetura Medallion)

Pipeline de dados que **extrai, limpa e analisa** os dados de *Viagens a Serviço*
do Portal da Transparência do Governo Federal (janeiro a junho de 2025),
seguindo a **Arquitetura Medallion** (camadas Raw → Silver → Gold) com
**Python** e **MySQL**.

---

## O problema que este projeto resolve

Os dados de viagens a serviço são publicados de forma **bruta e desorganizada**:
valores com vírgula decimal, datas no formato brasileiro, campos em texto livre
e sem qualquer garantia de integridade referencial entre viagens, pagamentos,
passagens e trechos. Este pipeline automatiza a extração desses dados, aplica
tipagem e limpeza, e constrói uma camada de métricas agregadas — transformando
um arquivo bruto de mais de 340 mil viagens em respostas diretas para perguntas
de negócio sobre os gastos públicos.

## Tecnologias e técnicas utilizadas

- **Python 3** — orquestração do pipeline
- **MySQL / MariaDB (XAMPP)** — banco de dados relacional
- **pandas** — leitura dos CSVs em blocos (chunks) e manipulação dos dados
- **gdown** — download automatizado do arquivo `.zip` a partir do Google Drive
- **mysql-connector-python** — conexão do Python com o MySQL
- **matplotlib / seaborn** — visualização de dados
- **Jupyter Notebook** — análise da camada Gold
- **Arquitetura Medallion** — organização em camadas Raw, Silver e Gold
- **ETL** (Extract, Transform, Load) e modelagem relacional (PK, FK, constraints)

## Arquitetura

```
 Portal da Transparência (.zip com 4 CSVs)
              │
              │  1_extrair.py  (download automatizado + carga bruta)
              ▼
        ┌───────────┐
        │   RAW     │  cópia fiel do CSV, tudo VARCHAR, sem constraints
        └───────────┘
              │
              │  2_transformar.py  (tipagem, limpeza, colunas calculadas)
              ▼
        ┌───────────┐
        │  SILVER   │  dados tipados (DECIMAL, DATE), com PK, FK e constraints
        └───────────┘
              │
              │  3_analise.ipynb  (JOIN + GROUP BY, perguntas de negócio)
              ▼
        ┌───────────┐
        │   GOLD    │  métricas agregadas, tabela + view, gráficos
        └───────────┘
```

| Camada | O que é | Onde fica |
|--------|---------|-----------|
| **Raw** | Cópia fiel do CSV, tudo texto | `raw_viagem`, `raw_pagamento`, `raw_passagem`, `raw_trecho` |
| **Silver** | Dados limpos e tipados, com PK/FK | `silver_viagem`, `silver_pagamento`, `silver_passagem`, `silver_trecho` |
| **Gold** | Métricas de negócio agregadas | `gold_resumo_orgao` (tabela) e `gold_resumo_orgao_view` (view) |

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
└── data/               (zip e csvs baixados — ignorado pelo Git)
```

## Como executar

1. Clone o repositório e entre na pasta.
2. Crie e ative um ambiente virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Copie `.env.example` para `.env` e preencha suas credenciais do MySQL
   (confira a porta usada pelo seu MySQL/XAMPP — pode não ser a 3306 padrão).
5. Cole o `DRIVE_FILE_ID` no `config.py`.
6. Rode os passos na ordem:
   ```bash
   mysql -u root < 0_criar_banco.sql   # cria o banco e as 8 tabelas
   python3 1_extrair.py                # extração + camada Raw
   python3 2_transformar.py            # limpeza + camada Silver
   jupyter notebook 3_analise.ipynb    # camada Gold + análises
   ```

## Perguntas de negócio respondidas

**1. Quais os 5 órgãos com maior custo total em viagens?**

| Órgão | Custo total |
|---|---|
| Ministério da Justiça e Segurança Pública | R$ 490.813.500 |
| Ministério da Defesa | R$ 157.059.700 |
| Ministério da Educação | R$ 112.519.500 |
| Ministério do Meio Ambiente e Mudança do Clima | R$ 50.548.380 |
| Ministério da Previdência Social | R$ 40.921.480 |

O órgão líder concentra sozinho mais de **três vezes** o custo do segundo
colocado — um forte candidato a prioridade em políticas de controle de gastos.

**2. Quais os 3 destinos (UF) com maior custo médio por viagem?**

| UF de destino | Custo médio por viagem | Qtd. de viagens |
|---|---|---|
| Roraima | R$ 11.277,48 | 8.850 |
| Acre | R$ 8.378,20 | 5.399 |
| Rondônia | R$ 8.252,80 | 7.838 |

Os três destinos são estados da região Norte, o que é coerente com o maior
custo de deslocamento (passagens aéreas) e diárias associado à distância e à
menor oferta de transporte terrestre direto.

**3. Qual a viagem de maior duração e qual o seu custo total?**

A viagem mais longa (id `0000000000020699856`, Ministério da Previdência
Social) durou **383 dias** — quase 18 vezes a duração média das viagens (cerca
de 21 dias) — mas está registrada com **custo total de R$ 0,00**. Além disso,
sua data de término (31/01/2026) ultrapassa o período de 6 meses de 2025 que
o conjunto de dados deveria cobrir. Isso é tratado como um **ponto de atenção
de qualidade de dados** da fonte original (não um erro do pipeline): a viagem
provavelmente ainda está em andamento ou tem diárias/pagamentos que não foram
lançados até a data de extração.

**4. Qual órgão tem o maior valor médio por viagem?**

Respondida a partir da camada Gold (`gold_resumo_orgao`), considerando apenas
órgãos com pelo menos 5 viagens registradas (para evitar que um caso isolado
distorça a média). O **Ministério das Relações Exteriores** lidera com
**R$ 12.867,49** de valor médio por viagem — coerente com o perfil de viagens
internacionais, tipicamente mais caras que deslocamentos domésticos. É
interessante notar que esse não é o mesmo órgão da Pergunta 1: o Ministério da
Justiça e Segurança Pública tem o maior custo **total** (alto volume de
viagens), mas um valor médio por viagem bem mais baixo (R$ 6.480,07) —
evidenciando a diferença entre *volume* de gasto e *intensidade* de gasto por
viagem.

**5. Qual o tipo de pagamento com maior valor médio?**

| Tipo de pagamento | Valor médio | Qtd. de pagamentos |
|---|---|---|
| Diárias | R$ 2.078,28 | 401.463 |
| Passagem | R$ 1.878,34 | 188.985 |
| Serviço correlato: seguro | R$ 447,51 | 4.894 |
| Restituição | R$ 245,70 | 11.574 |

Diárias lideram o valor médio, o que faz sentido considerando que cobrem
hospedagem e alimentação ao longo de vários dias, enquanto restituições e
serviços correlatos são valores pontuais e menores.

**6. Qual o meio de transporte mais usado nos trechos?**

| Meio de transporte | Qtd. de trechos |
|---|---|
| Veículo Oficial | 386.424 |
| Aéreo | 232.666 |
| Rodoviário | 64.970 |
| Veículo Próprio | 42.846 |
| Inválido | 26.659 |
| Fluvial | 8.429 |

O veículo oficial domina, sinalizando que a maior parte dos trechos é de
deslocamento local/regional, enquanto o meio aéreo — mais caro — fica em
segundo lugar e concentra provavelmente a maior parte do custo com passagens.

## Possíveis melhorias

- Automatizar a execução periódica do pipeline (ex.: agendamento via cron ou
  Airflow), incluindo a atualização automática da camada Gold.
- Adicionar testes automatizados de qualidade de dados na camada Silver
  (ex.: checar duplicidade de IDs, percentual de valores nulos, viagens com
  datas fora do intervalo esperado como a encontrada na Pergunta 3).
- Manter histórico de execuções na camada Raw em vez de `TRUNCATE`
  (versionamento de cargas, permitindo auditoria de quando cada dado chegou).
- Criar um dashboard interativo (Streamlit ou Power BI) consumindo a camada
  Gold para consulta contínua, sem depender de reabrir o notebook.
- Expandir a análise para múltiplos anos, permitindo comparações históricas
  de gasto por órgão e identificação de tendências sazonais.
- Adicionar validação de CI (GitHub Actions) que rode o `0_criar_banco.sql`
  e um teste básico dos scripts a cada push, evitando regressões.

## Conclusões e insights

- A camada Gold (`gold_resumo_orgao` / `gold_resumo_orgao_view`) concentrou,
  em uma única tabela construída via `JOIN` + `GROUP BY`, métricas por órgão
  (quantidade de viagens, custo total, custo médio e duração média),
  permitindo responder várias perguntas de negócio sem reprocessar as
  camadas anteriores.
- Um cuidado técnico importante validado durante o desenvolvimento: unir
  `silver_viagem` diretamente com `silver_pagamento` duplica o `valor_total`
  da viagem uma vez para cada pagamento associado a ela (uma viagem pode ter
  mais de um pagamento). Pré-agregar os pagamentos por viagem antes do `JOIN`
  evitou essa duplicação — confirmado na prática, já que o valor total do
  Ministério da Justiça e Segurança Pública bateu de forma idêntica na
  Pergunta 1 (consulta direta) e na camada Gold (R$ 490.813.500 nos dois
  casos).
- Os dados confirmam uma concentração de gastos: um único órgão (Ministério
  da Justiça e Segurança Pública) responde por uma fatia desproporcional do
  custo total, enquanto o maior valor médio por viagem aparece em órgãos com
  perfil de deslocamento internacional (Relações Exteriores).
- A separação entre camada Raw (fiel ao CSV) e Silver (tipada e íntegra) se
  mostrou essencial não só para limpeza, mas também para *auditoria*: foi
  possível identificar uma anomalia real nos dados de origem (viagem com
  duração de 383 dias e custo zerado) sem alterar o dado bruto, apenas
  observando-o através da camada tratada.
