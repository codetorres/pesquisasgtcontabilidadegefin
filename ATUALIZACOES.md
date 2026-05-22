# Relatório de Atualizações — Portal de Pesquisas GT 06 Contabilidade

Registro cronológico de todas as atualizações de estatísticas e mudanças relevantes no portal.

---

## Como documentar uma nova atualização

Antes de atualizar as estatísticas:
1. Rodar `scripts/verificar-duplicidades.ps1` — verifica duplicidades por UF nos CSVs
2. Rodar `scripts/atualizar_estatisticas.py` — regenera o bloco `AUTO_STATS` do `index.html`
3. Registrar a atualização neste arquivo seguindo o modelo abaixo

---

## Histórico

---

### [v4] 22/05/2026 — `29e4086`

**Tipo:** Atualização de estatísticas (bases de 22/05/2026)
**Responsável:** Robson Torres

#### Participação

| Pesquisa | Anterior | Atual | Novos respondentes |
|---|---|---|---|
| P1 — Despesas Acessórias | 8 UFs (30%) | **12 UFs (44%)** | AL, AP, ES, GO |
| P2 — Conciliação Bancária | 11 UFs (41%) | **14 UFs (52%)** | AL, ES, SC |
| P3 — Precatórios Educação | 8 UFs (30%) | **12 UFs (44%)** | AL, AP, ES, GO |

> **Marco:** P2 ultrapassou 50% de participação (14 de 27 UFs).

#### UFs respondentes por pesquisa

- **P1:** AL, AP, CE, ES, GO, PE, PI, PR, RN, RR, RS, TO
- **P2:** AL, AP, CE, ES, GO, PE, PI, PR, RN, RR, RS, SC, SE, TO
- **P3:** AL, AP, CE, ES, GO, PE, PI, PR, RN, RR, RS, TO

#### Controle de qualidade

- Duplicidades detectadas: **nenhuma** (P1, P2, P3)
- Deduplicação aplicada: não foi necessária

#### Destaques dos resultados

**P1 — Despesas Acessórias (12 UFs)**
- Q4 (Tratamento patrimonial): "Obras em Andamento" consolida-se como prática dominante — 10/12 (83%)
- Q5 (TCE): 92% sem consulta formalizada (11/12)
- Q3 (Requisitos): Vinculação Direta lidera isolada (8/12), Rastreabilidade em 2º (7/12)
- Q1 (Classificação): "Outro" ainda lidera (5/12); corrente cresce para 4; capital para 3

**P2 — Conciliação Bancária (14 UFs)**
- Q1 (Dispõe de ferramenta): Sim consolida liderança — 8/14 (57%)
- Q2/Q3: Módulo nativo SIAFIC lidera em 2 (8/14); Q3 em empate triplo (4 cada: sem ferramenta, terceirizada, nativa)
- Q4 (Automação): nível médio segue líder isolado — 9/14 (64%)

**P3 — Precatórios Educação (12 UFs)**
- Q1 (Inclusão no MDE): 92% Não (11/12) — surge 1ª resposta "Sim"
- Q2 (Repasse ao TJ): Não lidera com 9/12, mas Sim cresce para 3
- Q5–Q7 (TCE/normativo): unanimidade mantida — 100% Não em todas
- Q4 (Unidade Gestora): empate entre "Não se aplica" e "Outro" (5 cada)

#### Arquivos alterados

- `index.html` — bloco `AUTO_STATS` regenerado
- `memoria-duplicidades.json` / `.md` — atualizados
- `tmp_stats/auto_stats_state.json` — atualizado

---

### [v3] 21/05/2026 — `a6ace1e`

**Tipo:** Atualização de estatísticas (bases de 21/05/2026)
**Responsável:** Robson Torres
**Script utilizado:** `atualizar_estatisticas.py` (primeira execução automatizada)

#### Participação

| Pesquisa | Anterior | Atual | Novos respondentes |
|---|---|---|---|
| P1 — Despesas Acessórias | 6 UFs | **8 UFs (30%)** | PR, RS |
| P2 — Conciliação Bancária | 5 UFs | **11 UFs (41%)** | GO, PI, PR, RN, RS, SE |
| P3 — Precatórios Educação | 2 UFs | **8 UFs (30%)** | PE, PI, PR, RN, RR, RS |

#### UFs respondentes por pesquisa

- **P1:** CE, PE, PI, PR, RN, RR, RS, TO
- **P2:** AP, CE, GO, PE, PI, PR, RN, RR, RS, SE, TO
- **P3:** CE, PE, PI, PR, RN, RR, RS, TO

#### Controle de qualidade

- Duplicidades detectadas: **nenhuma** (P1, P2, P3)
- Deduplicação aplicada: não foi necessária

#### Destaques dos resultados

**P1 — Despesas Acessórias (8 UFs)**
- Q4 (Tratamento patrimonial): Consenso em "Obras em Andamento" — 7/8 (88%)
- Q5 (TCE): 88% dos estados não consultou o TCE formalmente
- Q3 (Requisitos): Empate triplo — Vinculação Direta, Indispensabilidade e Rastreabilidade (5/8 cada)
- Q1 (Classificação): "Outro" lidera (4/8); empate entre corrente e capital (2 cada)

**P2 — Conciliação Bancária (11 UFs)**
- Q1 (Dispõe de ferramenta): virada — maioria agora possui ferramenta (6 Sim / 4 Não / 1 outra)
- Q4 (Automação): nível médio lidera com 8/11 (73%)
- Q2/Q3: módulo nativo SIAFIC lidera (6), seguido de sem ferramenta (5)

**P3 — Precatórios Educação (8 UFs)**
- Q1 (Inclusão no MDE): 88% Não incluem no cômputo (7/8)
- Q5–Q7 (TCE/normativo): unanimidade — nenhum estado consultou TCE nem editou normativo específico
- Q4 (Unidade Gestora): empate entre "Não se aplica" e "Outro" (3 cada)

#### Arquivos alterados

- `index.html` — bloco `AUTO_STATS` regenerado
- `memoria-duplicidades.json` / `.md` — atualizados
- `scripts/atualizar_estatisticas.py` — adicionado ao repositório (novo)
- `scripts/verificar-duplicidades.ps1` — adicionado ao repositório (novo)
- `tmp_stats/auto_stats_state.json` — adicionado ao repositório (novo)
- `README.md` — documentação do fluxo de duplicidades adicionada

---

### [v2] 20/05/2026 — `818825f`

**Tipo:** Atualização de estatísticas + prazos
**Responsável:** Robson Torres

#### Participação

| Pesquisa | Anterior | Atual | Observação |
|---|---|---|---|
| P1 — Despesas Acessórias | — | **6 UFs (22%)** | Primeira prévia da P1 |
| P2 — Conciliação Bancária | — | **5 UFs (19%)** | AP com 2 envios — consolidado pela resposta mais recente |
| P3 — Precatórios Educação | — | **2 UFs (7%)** | Primeiras respostas da P3 |

#### UFs respondentes por pesquisa

- **P1:** CE, PE, PI, RN, RR, TO
- **P2:** AP, CE, PE, RR, TO *(AP: duplicidade detectada e tratada — mantida resposta de 15/05 às 20h07)*
- **P3:** CE, RN

#### Controle de qualidade

- P2: **AP duplicado** (2 respostas em 15/05/2026 às 12h44 e 20h07) — consolidado pela mais recente

#### Prazos atualizados nesta versão

- P1: prazo originalmente 20/05/2026 → prorrogado para **31/05/2026**
- P2 e P3: prazo definido em **31/05/2026**

#### Arquivos alterados

- `index.html` — primeiro bloco completo de estatísticas das 3 pesquisas; prazos atualizados
- `memoria-duplicidades.json` / `.md` — criados

---

### [v1] 15/05/2026 — `fdfac41` / `9afb4cc`

**Tipo:** Lançamento e configuração inicial do portal
**Responsável:** Robson Torres

#### Pesquisas publicadas

- **P1 — Despesas Acessórias** (`0a77851`): primeira pesquisa ao vivo, demanda PE
- **P2 — Conciliação Bancária** (`9afb4cc`): DATA_POINT_02 adicionado, demanda PE
- **P3 — Precatórios Educação** (`fdfac41`): DATA_POINT_03 adicionado com link e prazo, demanda corrigida de PE para CE (`01e3724`)

#### Ajustes pós-lançamento

- `25eb057` — Identificadores DATA_POINT removidos dos cards e do modal
- `1889c15` / `c51142c` — Título da P2 corrigido e simplificado

---
