#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Callable
from zipfile import ZipFile


UFS_BR = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
    "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
    "SE", "SP", "TO",
]

AUTO_STATS_START = "<!-- AUTO_STATS_START -->"
AUTO_STATS_END = "<!-- AUTO_STATS_END -->"

RULE_TEXT = "Sempre verificar duplicidade por estado (UF) antes de consolidar as estatisticas."
CONSOLIDATION_RULE_TEXT = (
    "Se houver duplicidade por UF, consolidar pela resposta mais recente e registrar a UF duplicada na pre-analise."
)


@dataclass
class QuestionConfig:
    number: int
    title: str
    options: list[str]
    note: str
    mode: str
    wide: bool = False


@dataclass
class SurveyConfig:
    sid: str
    folder: str
    panel_id: str
    panel_title: str
    form_link: str
    questions: list[QuestionConfig]


SURVEYS: list[SurveyConfig] = [
    SurveyConfig(
        sid="1",
        folder="P1 - Despesas Acessórias",
        panel_id="stats-content-p1",
        panel_title="Classificação de Despesas Acessórias",
        form_link="https://docs.google.com/forms/d/1ilryjYC3szEtUpn8zbciLYAF4PhGecaAFqfmepv5QB8/viewform",
        questions=[
            QuestionConfig(
                number=1,
                title="Q1 - Classificação das despesas acessórias",
                options=[
                    "Sempre como Despesas Correntes (GND 3), independentemente do vínculo com a obra",
                    "Como Despesas de Capital, quando diretamente vinculada à obra (GND 4 - Investimento), integrando o custo da obra em andamento",
                    "Outro",
                ],
                note="Ranking por frequência das opções do formulário (Q1).",
                mode="single_exact_with_other",
            ),
            QuestionConfig(
                number=2,
                title="Q2 - Fundamentos para classificar como capital",
                options=[
                    "Princípio da Primazia da Essência sobre a Forma (NBC TSP Estrutura Conceitual)",
                    "Definição de custo de ativo imobilizado (NBC TSP 17 / MCASP), que inclui gastos diretos para colocar o ativo em condições de uso",
                    "Autorização expressa em leis orçamentárias ou em manuais/pareceres técnicos do Tesouro/Contadoria e/ou da Controladoria local",
                    "Outro",
                ],
                note="Ranking por frequência das opções do formulário (Q2, múltipla seleção).",
                mode="multi_exact_with_other",
            ),
            QuestionConfig(
                number=3,
                title="Q3 - Requisitos para registro como investimento",
                options=[
                    "Vinculação Direta: O gasto deve ser 100% vinculado à obra, sem rateio com atividades administrativas",
                    "Indispensabilidade: Demonstração de que, sem o gasto, a obra não ocorreria ou não seria fiscalizada",
                    "Rastreabilidade: Controle documental rigoroso (atesto de fiscais) vinculando o gasto ao projeto específico",
                    "Temporalidade: O gasto deve cessar obrigatoriamente com a conclusão da obra",
                    "Outro",
                ],
                note="Ranking por frequência das opções do formulário (Q3, múltipla seleção).",
                mode="multi_exact_with_other",
            ),
            QuestionConfig(
                number=4,
                title="Q4 - Tratamento contábil patrimonial",
                options=[
                    'Acumulados na conta de "Obras em Andamento" no Ativo Não Circulante e posteriormente incorporados ao bem',
                    "Registrados diretamente como variação patrimonial diminutiva (despesa do mês)",
                    "Registrados no ativo apenas após o recebimento definitivo da obra",
                    "Outro",
                ],
                note="Ranking por frequência das opções do formulário (Q4).",
                mode="single_exact_with_other",
            ),
            QuestionConfig(
                number=5,
                title="Q5 - Manifestação do TCE",
                options=[
                    "Sim, com parecer favorável à classificação como investimento em casos específicos",
                    "Sim, com parecer contrário (exigindo classificação sempre como corrente)",
                    "Não houve consulta formalizada até o momento",
                    "Outro",
                ],
                note="Ranking por frequência das opções do formulário (Q5).",
                mode="single_exact_with_other",
                wide=True,
            ),
        ],
    ),
    SurveyConfig(
        sid="2",
        folder="P2 - Conciliação Bancária",
        panel_id="stats-content-p2",
        panel_title="Sistemas/Módulos de Conciliação Bancária",
        form_link="https://docs.google.com/forms/d/15xOKtMrEUqY4HIlNanFYPbWaQmIOrjNqMZ37tL8Nfcc/viewform",
        questions=[
            QuestionConfig(
                number=1,
                title="Q1 - Estado dispõe de ferramenta de conciliação",
                options=["Sim", "Não"],
                note="Ranking por frequência das opções do formulário (Q1).",
                mode="single_exact",
            ),
            QuestionConfig(
                number=2,
                title="Q2 - Natureza da ferramenta no SIAFIC",
                options=[
                    "Módulo nativo integrado ao SIAFIC",
                    "Sem ferramenta / não se aplica",
                ],
                note="Ranking por frequência das opções do formulário (Q2).",
                mode="p2_q2_bucket",
            ),
            QuestionConfig(
                number=3,
                title="Q3 - Desenvolvimento da solução",
                options=[
                    "Sem ferramenta / não se aplica",
                    "Solução terceirizada",
                    "Solução nativa/interna (com ressalvas)",
                    "Outro",
                ],
                note="Ranking por frequência das opções do formulário (Q3).",
                mode="p2_q3_bucket",
            ),
            QuestionConfig(
                number=4,
                title="Q4 - Nível de automação da conciliação",
                options=[
                    "Baixo (predominantemente manual)",
                    "Médio (automação parcial)",
                    "Sem ferramenta / não se aplica",
                ],
                note="Ranking por frequência das opções do formulário (Q4).",
                mode="p2_q4_bucket",
            ),
        ],
    ),
    SurveyConfig(
        sid="3",
        folder="P3 - Precatórios Educação",
        panel_id="stats-content-p3",
        panel_title="Inclusão de despesas com Precatórios no Gasto de Pessoal",
        form_link="https://forms.gle/R3JVX1g1ShxZSvrK6",
        questions=[
            QuestionConfig(
                number=1,
                title="Q1 - Inclusão no MDE (RREO Anexo 8)",
                options=["Sim", "Não"],
                note="Ranking por frequência das opções do formulário (Q1).",
                mode="single_exact",
            ),
            QuestionConfig(
                number=2,
                title="Q2 - Repasse ao TJ a título de adiantamento",
                options=["Sim", "Não", "Não se aplica", "Outro"],
                note="Ranking por frequência das opções do formulário (Q2).",
                mode="single_exact_with_other",
            ),
            QuestionConfig(
                number=3,
                title="Q3 - Momento considerado para status de Ativo",
                options=[
                    "Data do ajuizamento da ação",
                    "Data da sentença",
                    "Data da inclusão na fila de Precatórios",
                    "Data do empenho",
                    "Não se aplica",
                    "Outro",
                ],
                note="Ranking por frequência das opções do formulário (Q3).",
                mode="single_exact_with_other",
            ),
            QuestionConfig(
                number=4,
                title="Q4 - Unidade Gestora Executora no SIAFIC",
                options=[
                    "Encargos Gerais do Estado",
                    "Órgão de origem do servidor",
                    "Não se aplica",
                    "Outro",
                ],
                note="Ranking por frequência das opções do formulário (Q4).",
                mode="single_exact_with_other",
            ),
            QuestionConfig(
                number=5,
                title="Q5 - Manifestação do TCE sobre a inclusão",
                options=["Sim", "Não", "Não se aplica"],
                note="Ranking por frequência das opções do formulário (Q5).",
                mode="single_exact",
            ),
            QuestionConfig(
                number=6,
                title="Q6 - TCE favorável à inclusão",
                options=["Sim", "Não", "Não se aplica"],
                note="Ranking por frequência das opções do formulário (Q6).",
                mode="single_exact",
            ),
            QuestionConfig(
                number=7,
                title="Q7 - Estado editou normativo específico",
                options=["Sim", "Não", "Não se aplica"],
                note="Ranking por frequência das opções do formulário (Q7).",
                mode="single_exact",
            ),
            QuestionConfig(
                number=8,
                title="Q8 - Anexo da norma informada",
                options=["Sem arquivo anexado", "Arquivo anexado"],
                note="Ranking por frequência das respostas registradas em Q8.",
                mode="p3_q8_upload",
                wide=True,
            ),
        ],
    ),
]


def strip_accents(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))


def normalize(text: str) -> str:
    cleaned = strip_accents((text or "").strip().lower())
    return re.sub(r"\s+", " ", cleaned)


def parse_timestamp(raw: str) -> datetime:
    if not raw:
        return datetime.min
    cleaned = re.sub(r"\s*GMT[+-]\d+\s*$", "", raw.strip())
    formats = [
        "%Y/%m/%d %I:%M:%S %p",
        "%Y/%m/%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return datetime.min


def percent_int(part: int, total: int) -> int:
    if total <= 0:
        return 0
    return int((part * 100.0 / total) + 0.5)


def percent_width(part: int, total: int) -> str:
    if total <= 0:
        return "0"
    pct = min(100.0, (part * 100.0) / total)
    return f"{pct:.1f}".rstrip("0").rstrip(".")


def plural_respostas(value: int) -> str:
    return "resposta" if value == 1 else "respostas"


def newest_zip(folder: Path) -> Path:
    zips = list_zip_files(folder)
    zips.sort(key=lambda p: (file_mtime(p), p.name), reverse=True)
    if not zips:
        raise FileNotFoundError(f"Nenhum .zip encontrado em: {folder}")
    return zips[0]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(long_path(path), "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 128), b""):
            h.update(chunk)
    return h.hexdigest()


def read_zip_csv_rows(zip_path: Path) -> tuple[list[dict[str, str]], str]:
    with ZipFile(long_path(zip_path), "r") as zf:
        csv_entries = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if not csv_entries:
            raise ValueError(f"ZIP sem CSV: {zip_path.name}")
        entry_name = csv_entries[0]
        raw = zf.read(entry_name)

    text = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise UnicodeDecodeError("utf-8", b"", 0, 1, "Não foi possível decodificar CSV")

    rows = list(csv.DictReader(StringIO(text)))
    return rows, entry_name


def find_state_col(headers: list[str]) -> str:
    for h in headers:
        if h == "Informe o Estado":
            return h
    for h in headers:
        if "Estado" in h:
            return h
    raise KeyError("Coluna de estado não encontrada.")


def long_path(path: Path) -> str:
    raw = str(path.resolve())
    if os.name != "nt":
        return raw
    if raw.startswith("\\\\?\\"):
        return raw
    if raw.startswith("\\\\"):
        return "\\\\?\\UNC\\" + raw.lstrip("\\")
    return "\\\\?\\" + raw


def list_zip_files(folder: Path) -> list[Path]:
    lp = long_path(folder)
    items: list[Path] = []
    for name in os.listdir(lp):
        if name.lower().endswith(".zip"):
            items.append(folder / name)
    return items


def file_mtime(path: Path) -> float:
    return os.stat(long_path(path)).st_mtime


def find_ts_col(headers: list[str]) -> str | None:
    for h in headers:
        if "Carimbo de data/hora" in h:
            return h
    return None


def dedup_rows_by_state(rows: list[dict[str, str]], state_col: str, ts_col: str | None) -> tuple[list[dict[str, str]], dict[str, list[str]]]:
    latest: dict[str, tuple[datetime, dict[str, str]]] = {}
    all_timestamps: dict[str, list[str]] = defaultdict(list)

    for row in rows:
        uf = (row.get(state_col, "") or "").strip().upper()
        if not uf:
            continue
        ts_raw = (row.get(ts_col, "") if ts_col else "") or ""
        ts_value = parse_timestamp(ts_raw)
        all_timestamps[uf].append(ts_raw.strip())

        current = latest.get(uf)
        if current is None or ts_value >= current[0]:
            latest[uf] = (ts_value, row)

    deduped = [latest[uf][1] for uf in sorted(latest.keys())]
    duplicates = {uf: all_timestamps[uf] for uf in sorted(all_timestamps.keys()) if len(all_timestamps[uf]) > 1}
    return deduped, duplicates


def find_question_col(headers: list[str], number: int) -> str:
    pattern = re.compile(rf"^\s*{number}\.\s*")
    for h in headers:
        if pattern.match(h):
            return h
    raise KeyError(f"Coluna da questão {number} não encontrada.")


def classify_single_exact(value: str, options: list[str]) -> str:
    nval = normalize(value)
    for opt in options:
        if nval and nval.startswith(normalize(opt)):
            return opt
    if "Outro" in options:
        return "Outro"
    return value.strip() if value.strip() else "Não informado"


def classify_multi_exact(value: str, options: list[str]) -> list[str]:
    normal_options = [opt for opt in options if opt != "Outro"]
    tokens = [tok.strip() for tok in (value or "").split(";") if tok.strip()]
    if not tokens:
        return ["Outro"] if "Outro" in options else ["Não informado"]

    labels: list[str] = []
    for tok in tokens:
        ntok = normalize(tok)
        matched = None
        for opt in normal_options:
            if ntok.startswith(normalize(opt)):
                matched = opt
                break
        if matched is not None:
            labels.append(matched)
        else:
            labels.append("Outro" if "Outro" in options else tok)
    return labels


def contains_any(text: str, fragments: list[str]) -> bool:
    return any(fragment in text for fragment in fragments)


def classify_p2_q2(value: str) -> str:
    n = normalize(value)
    if "modulo nativo integrado ao siafic" in n:
        return "Módulo nativo integrado ao SIAFIC"
    return "Sem ferramenta / não se aplica"


def classify_p2_q3(value: str) -> str:
    n = normalize(value)
    if "terceiriz" in n:
        return "Solução terceirizada"
    if contains_any(n, [" nativa", "nativa ", "solucao nativa", "interna"]):
        return "Solução nativa/interna (com ressalvas)"
    if contains_any(
        n,
        ["nao se aplica", "não se aplica", "nao ha", "não há", "nao temos", "não temos", "sem ferramenta"],
    ):
        return "Sem ferramenta / não se aplica"
    return "Outro" if n else "Sem ferramenta / não se aplica"


def classify_p2_q4(value: str) -> str:
    n = normalize(value)
    if "baixo" in n:
        return "Baixo (predominantemente manual)"
    if "medio" in n:
        return "Médio (automação parcial)"
    return "Sem ferramenta / não se aplica"


def classify_p3_q8(value: str) -> str:
    return "Arquivo anexado" if (value or "").strip() else "Sem arquivo anexado"


def count_question(rows: list[dict[str, str]], col: str, q: QuestionConfig) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        raw = row.get(col, "") or ""
        if q.mode == "single_exact":
            label = classify_single_exact(raw, q.options)
            counts[label] += 1
        elif q.mode == "single_exact_with_other":
            label = classify_single_exact(raw, q.options)
            counts[label] += 1
        elif q.mode == "multi_exact_with_other":
            for label in classify_multi_exact(raw, q.options):
                counts[label] += 1
        elif q.mode == "p2_q2_bucket":
            counts[classify_p2_q2(raw)] += 1
        elif q.mode == "p2_q3_bucket":
            counts[classify_p2_q3(raw)] += 1
        elif q.mode == "p2_q4_bucket":
            counts[classify_p2_q4(raw)] += 1
        elif q.mode == "p3_q8_upload":
            counts[classify_p3_q8(raw)] += 1
        else:
            raise ValueError(f"Modo não suportado: {q.mode}")

    for opt in q.options:
        counts.setdefault(opt, 0)
    return counts


def rank_items(counts: Counter[str], preferred_order: list[str]) -> list[tuple[int, str, int]]:
    order_index = {label: idx for idx, label in enumerate(preferred_order)}
    labels = list(counts.keys())
    labels.sort(key=lambda lbl: (-counts[lbl], order_index.get(lbl, 10_000), lbl))

    result: list[tuple[int, str, int]] = []
    rank = 0
    prev_count: int | None = None
    for idx, label in enumerate(labels, start=1):
        count = counts[label]
        if prev_count is None or count != prev_count:
            rank = idx
        result.append((rank, label, count))
        prev_count = count
    return result


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def build_question_card_html(question: QuestionConfig, counts: Counter[str], respondents: int) -> str:
    classes = "stats-card stats-card-wide" if question.wide else "stats-card"
    lines = [f'<article class="{classes}">', f"  <h4>{esc(question.title)}</h4>"]

    for rank, label, value in rank_items(counts, question.options):
        width = percent_width(value, respondents)
        lines.append('  <div class="stats-row">')
        lines.append(
            f'    <div class="stats-row-top"><span>{rank}º {esc(label)}</span><strong>{value} {plural_respostas(value)}</strong></div>'
        )
        lines.append(f'    <div class="stats-bar"><span style="width:{width}%"></span></div>')
        lines.append("  </div>")

    lines.append('  <div class="stats-note">')
    lines.append(f"    {esc(question.note)}")
    lines.append("  </div>")
    lines.append("</article>")
    return "\n".join(lines)


def build_panel_html(
    survey: SurveyConfig,
    rows: list[dict[str, str]],
    headers: list[str],
    updated_at: str,
    visible: bool,
) -> str:
    state_col = find_state_col(headers)
    participants = sorted({(row.get(state_col, "") or "").strip().upper() for row in rows if (row.get(state_col, "") or "").strip()})
    pendentes = [uf for uf in UFS_BR if uf not in participants]

    resp_count = len(participants)
    total_ufs = len(UFS_BR)
    pend_count = total_ufs - resp_count
    resp_percent_display = percent_int(resp_count, total_ufs)
    resp_width = percent_width(resp_count, total_ufs)
    pend_percent_display = percent_int(pend_count, total_ufs)
    pend_width = percent_width(pend_count, total_ufs)

    style_attr = "" if visible else ' style="display:none"'
    lines = [f'<section class="stats-panel" id="{survey.panel_id}"{style_attr}>']
    lines.append('  <div class="stats-head">')
    lines.append(f"    <h3>{esc(survey.panel_title)}</h3>")
    lines.append(
        f'    <span class="stats-badge"><i class="fa-solid fa-chart-column"></i> Prévia: {resp_count} UFs respondentes</span>'
    )
    lines.append("  </div>")
    lines.append('  <p class="stats-subtitle">')
    lines.append(f"    Resumo com base na versão preliminar de respostas (atualizado em {updated_at}).")
    lines.append("  </p>")
    lines.append("")
    lines.append('  <section class="stats-group">')
    lines.append('    <div class="stats-group-head">')
    lines.append('      <h4 class="stats-group-title">Controle da Coleta</h4>')
    lines.append("    </div>")
    lines.append("")
    lines.append('    <div class="stats-kpis stats-kpis-control">')
    lines.append('      <div class="kpi-card">')
    lines.append(f'        <div class="kpi-value">{resp_count}</div>')
    lines.append(f'        <div class="kpi-label">Estados participantes ({esc(", ".join(participants))})</div>')
    lines.append("      </div>")
    lines.append('      <div class="kpi-card">')
    lines.append(f'        <div class="kpi-value">{pend_count}</div>')
    lines.append(f'        <div class="kpi-label">Estados pendentes de resposta ({esc(", ".join(pendentes))})</div>')
    lines.append(
        f'        <a class="kpi-link" href="{esc(survey.form_link)}" target="_blank" rel="noopener noreferrer">'
    )
    lines.append('          <i class="fa-solid fa-link"></i> Clique para responder à pesquisa')
    lines.append("        </a>")
    lines.append("      </div>")
    lines.append("    </div>")
    lines.append("")
    lines.append('    <article class="stats-card">')
    lines.append("      <h4>Percentual de participação (UFs)</h4>")
    lines.append('      <div class="participacao-layout">')
    lines.append('        <div class="participacao-bars">')
    lines.append('          <div class="stats-row">')
    lines.append(
        f'            <div class="stats-row-top"><span>Respondentes</span><strong>{resp_count} de {total_ufs} ({resp_percent_display}%)</strong></div>'
    )
    lines.append(f'            <div class="stats-bar"><span style="width:{resp_width}%"></span></div>')
    lines.append("          </div>")
    lines.append('          <div class="stats-row">')
    lines.append(
        f'            <div class="stats-row-top"><span>Pendentes</span><strong>{pend_count} de {total_ufs} ({pend_percent_display}%)</strong></div>'
    )
    lines.append(f'            <div class="stats-bar"><span style="width:{pend_width}%"></span></div>')
    lines.append("          </div>")
    lines.append("        </div>")
    lines.append("")
    lines.append('        <div class="donut-wrap">')
    lines.append(f'          <div class="donut-chart" style="--respondentes:{resp_width}">')
    lines.append('            <div class="donut-center">')
    lines.append(f"              <strong>{resp_percent_display}%</strong>")
    lines.append("              <span>Respondentes</span>")
    lines.append("            </div>")
    lines.append("          </div>")
    lines.append('          <div class="donut-legend">')
    lines.append('            <div class="donut-legend-item">')
    lines.append('              <span class="donut-dot respondentes"></span>')
    lines.append("              <span>Respondentes</span>")
    lines.append("            </div>")
    lines.append('            <div class="donut-legend-item">')
    lines.append('              <span class="donut-dot pendentes"></span>')
    lines.append("              <span>Pendentes</span>")
    lines.append("            </div>")
    lines.append("          </div>")
    lines.append("        </div>")
    lines.append("      </div>")
    lines.append("    </article>")
    lines.append("  </section>")
    lines.append("")
    lines.append('  <section class="stats-group">')
    lines.append('    <div class="stats-group-head">')
    lines.append('      <h4 class="stats-group-title">Resultados prévio da Pesquisa</h4>')
    lines.append("    </div>")
    lines.append("")
    lines.append('    <div class="stats-grid">')

    for q in survey.questions:
        col = find_question_col(headers, q.number)
        counts = count_question(rows, col, q)
        card = build_question_card_html(q, counts, resp_count)
        lines.extend([f"      {ln}" for ln in card.splitlines()])
        lines.append("")

    if lines[-1] == "":
        lines.pop()
    lines.append("    </div>")
    lines.append("  </section>")
    lines.append("</section>")
    return "\n".join(lines)


def indent_block(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else "" for line in text.splitlines())


def replace_auto_stats_block(index_text: str, panels_html: str) -> str:
    pattern = re.compile(rf"{re.escape(AUTO_STATS_START)}.*?{re.escape(AUTO_STATS_END)}", flags=re.DOTALL)
    replacement = f"{AUTO_STATS_START}\n{indent_block(panels_html, 8)}\n        {AUTO_STATS_END}"
    if not pattern.search(index_text):
        raise RuntimeError("Marcadores AUTO_STATS_START/AUTO_STATS_END não encontrados em index.html")
    return pattern.sub(replacement, index_text, count=1)


def format_generated_at(now: datetime) -> str:
    base = now.strftime("%Y-%m-%d %H:%M:%S %z")
    return re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", base)


def build_duplicates_memory(project_root: Path, surveys: list[SurveyConfig], generated_at: str) -> tuple[dict, str]:
    survey_entries = []
    md_lines = [
        "# Memoria de duplicidades por estado",
        "",
        f"- Atualizado em: {generated_at}",
        f"- Regra: {RULE_TEXT}",
        f"- Consolidacao: {CONSOLIDATION_RULE_TEXT}",
        "",
    ]

    has_duplicates = False

    for survey in surveys:
        folder_path = project_root / survey.folder
        if not folder_path.exists():
            survey_entries.append(
                {
                    "survey_folder": survey.folder,
                    "status": "folder_not_found",
                    "files": [],
                }
            )
            continue

        file_entries = []
        for zip_path in sorted(list_zip_files(folder_path), key=lambda p: p.name):
            try:
                rows, entry_name = read_zip_csv_rows(zip_path)
            except Exception as exc:  # noqa: BLE001
                file_entries.append(
                    {
                        "file_name": zip_path.name,
                        "status": "open_error",
                        "error": str(exc),
                        "entries": [],
                    }
                )
                continue

            if not rows:
                file_entries.append(
                    {
                        "file_name": zip_path.name,
                        "status": "ok",
                        "entries": [
                            {
                                "entry_name": entry_name,
                                "status": "empty_csv",
                                "total_rows": 0,
                                "unique_states": 0,
                                "duplicate_states_count": 0,
                                "duplicate_rows_count": 0,
                                "duplicates": [],
                            }
                        ],
                    }
                )
                continue

            headers = list(rows[0].keys())
            try:
                state_col = find_state_col(headers)
            except Exception:  # noqa: BLE001
                file_entries.append(
                    {
                        "file_name": zip_path.name,
                        "status": "ok",
                        "entries": [
                            {
                                "entry_name": entry_name,
                                "status": "missing_state_column",
                                "total_rows": len(rows),
                                "unique_states": 0,
                                "duplicate_states_count": 0,
                                "duplicate_rows_count": 0,
                                "duplicates": [],
                            }
                        ],
                    }
                )
                continue

            ts_col = find_ts_col(headers)
            grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
            for row in rows:
                uf = (row.get(state_col, "") or "").strip().upper()
                if uf:
                    grouped[uf].append(row)

            duplicate_items = []
            duplicate_states_count = 0
            duplicate_rows_count = 0
            for uf in sorted(grouped.keys()):
                if len(grouped[uf]) > 1:
                    duplicate_states_count += 1
                    duplicate_rows_count += len(grouped[uf])
                    ts_list = []
                    for row in grouped[uf]:
                        ts_value = (row.get(ts_col, "") if ts_col else "") or ""
                        ts_list.append(ts_value.strip())
                    duplicate_items.append(
                        {
                            "state": uf,
                            "count": len(grouped[uf]),
                            "timestamps": sorted(ts_list),
                        }
                    )
            has_duplicates = has_duplicates or duplicate_states_count > 0

            entry_payload = {
                "entry_name": entry_name,
                "status": "ok",
                "state_column": state_col,
                "timestamp_column": ts_col,
                "total_rows": len(rows),
                "unique_states": len(grouped),
                "duplicate_states_count": duplicate_states_count,
                "duplicate_rows_count": duplicate_rows_count,
                "duplicates": duplicate_items,
            }
            file_entries.append({"file_name": zip_path.name, "status": "ok", "entries": [entry_payload]})

            md_lines.append(f"## {survey.folder}")
            md_lines.append(f"- Arquivo: {zip_path.name}")
            md_lines.append(f"- Linhas: {entry_payload['total_rows']}")
            md_lines.append(f"- UFs unicas: {entry_payload['unique_states']}")
            md_lines.append(f"- UFs em duplicidade: {entry_payload['duplicate_states_count']}")
            if duplicate_items:
                for item in duplicate_items:
                    ts_join = " | ".join(item["timestamps"]) if item["timestamps"] else "sem carimbo"
                    md_lines.append(f"- Duplicidade: {item['state']} ({item['count']} respostas) -> {ts_join}")
            else:
                md_lines.append("- Duplicidade: nenhuma")
            md_lines.append("")

        survey_entries.append({"survey_folder": survey.folder, "status": "ok", "files": file_entries})

    memory = {
        "generated_at": generated_at,
        "project_root": str(project_root),
        "rule": RULE_TEXT,
        "consolidation_rule": CONSOLIDATION_RULE_TEXT,
        "has_duplicates": has_duplicates,
        "surveys": survey_entries,
    }
    return memory, "\n".join(md_lines).rstrip() + "\n"


def run_git(project_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Atualiza estatísticas das pesquisas a partir dos CSVs ZIP das pastas P1/P2/P3."
    )
    parser.add_argument("--force", action="store_true", help="Força atualização mesmo sem arquivo novo.")
    parser.add_argument("--commit", action="store_true", help="Cria commit ao final.")
    parser.add_argument("--push", action="store_true", help="Executa push após commit (requer --commit).")
    parser.add_argument(
        "--message",
        default="Atualiza estatísticas automáticas das pesquisas",
        help="Mensagem do commit quando --commit for usado.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    index_path = project_root / "index.html"
    state_path = project_root / "tmp_stats" / "auto_stats_state.json"
    dup_json_path = project_root / "memoria-duplicidades.json"
    dup_md_path = project_root / "memoria-duplicidades.md"

    state_path.parent.mkdir(parents=True, exist_ok=True)

    latest_files = {}
    survey_latest_rows: dict[str, list[dict[str, str]]] = {}
    survey_latest_headers: dict[str, list[str]] = {}
    changed_surveys: list[str] = []

    old_state = {}
    if state_path.exists():
        try:
            old_state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            old_state = {}

    for survey in SURVEYS:
        folder_path = project_root / survey.folder
        zip_path = newest_zip(folder_path)
        signature = {
            "folder": survey.folder,
            "file_name": zip_path.name,
            "sha256": sha256_file(zip_path),
        }
        latest_files[survey.sid] = signature

        rows, _entry_name = read_zip_csv_rows(zip_path)
        if not rows:
            raise RuntimeError(f"CSV vazio para {survey.folder}: {zip_path.name}")
        headers = list(rows[0].keys())
        state_col = find_state_col(headers)
        ts_col = find_ts_col(headers)
        dedup_rows, _dups = dedup_rows_by_state(rows, state_col, ts_col)
        survey_latest_rows[survey.sid] = dedup_rows
        survey_latest_headers[survey.sid] = headers

        old_sig = (old_state.get("latest_files") or {}).get(survey.sid)
        if old_sig != signature:
            changed_surveys.append(survey.sid)

    if not changed_surveys and not args.force:
        print("Nenhum arquivo novo detectado. Estatísticas não foram alteradas.")
        return 0

    now = datetime.now().astimezone()
    updated_ptbr = now.strftime("%d/%m/%Y")
    generated_at = format_generated_at(now)

    # Regera bloco de estatísticas do index.html
    panels = []
    for survey in SURVEYS:
        panels.append(
            build_panel_html(
                survey=survey,
                rows=survey_latest_rows[survey.sid],
                headers=survey_latest_headers[survey.sid],
                updated_at=updated_ptbr,
                visible=(survey.sid == "1"),
            )
        )
        panels.append("")
    panels_html = "\n".join(panels).rstrip() + "\n"

    original_index = index_path.read_text(encoding="utf-8")
    updated_index = replace_auto_stats_block(original_index, panels_html)
    index_changed = updated_index != original_index
    if index_changed:
        index_path.write_text(updated_index, encoding="utf-8", newline="\n")

    # Regera memória de duplicidades
    memory_json, memory_md = build_duplicates_memory(project_root, SURVEYS, generated_at)
    dup_json_path.write_text(json.dumps(memory_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dup_md_path.write_text(memory_md, encoding="utf-8", newline="\n")

    new_state = {
        "generated_at": generated_at,
        "latest_files": latest_files,
    }
    state_path.write_text(json.dumps(new_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Pastas atualizadas por arquivo novo: {', '.join(changed_surveys) if changed_surveys else '(forçado)'}")
    print(f"index.html {'alterado' if index_changed else 'sem alterações visuais'}")
    print("Arquivos atualizados:")
    print(f"- {index_path.name}")
    print(f"- {dup_json_path.name}")
    print(f"- {dup_md_path.name}")
    print(f"- {state_path.relative_to(project_root)}")

    if args.commit:
        files_to_add = [
            "index.html",
            "memoria-duplicidades.json",
            "memoria-duplicidades.md",
            str(state_path.relative_to(project_root)).replace("\\", "/"),
        ]
        add_res = run_git(project_root, ["add", "--", *files_to_add])
        if add_res.returncode != 0:
            raise RuntimeError(f"Erro no git add:\n{add_res.stderr or add_res.stdout}")

        staged = run_git(project_root, ["diff", "--cached", "--name-only"])
        if staged.returncode != 0:
            raise RuntimeError(f"Erro ao verificar staged:\n{staged.stderr or staged.stdout}")
        staged_files = [line.strip() for line in staged.stdout.splitlines() if line.strip()]
        if not staged_files:
            print("Sem alterações para commit.")
            return 0

        commit_res = run_git(project_root, ["commit", "-m", args.message])
        if commit_res.returncode != 0:
            raise RuntimeError(f"Erro no git commit:\n{commit_res.stderr or commit_res.stdout}")
        print(commit_res.stdout.strip())

        if args.push:
            push_res = run_git(project_root, ["push", "origin", "main"])
            if push_res.returncode != 0:
                raise RuntimeError(f"Erro no git push:\n{push_res.stderr or push_res.stdout}")
            print(push_res.stdout.strip())
            if push_res.stderr.strip():
                print(push_res.stderr.strip())

    elif args.push:
        print("Ignorando --push porque --commit não foi informado.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
