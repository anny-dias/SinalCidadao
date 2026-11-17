"""Gera relatório técnico atualizado, preservando campos ainda não informados."""
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Relatorio_Tecnico_CitizenFlow_RPA.pdf"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
if FONT_DIR.is_dir():
    pdfmetrics.registerFont(TTFont("SC", str(FONT_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("SC-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("SC", normal="SC", bold="SC-Bold")
else:
    # Windows: ReportLab fornece Helvetica; os textos comuns permanecem válidos.
    pdfmetrics.registerFontFamily("Helvetica", normal="Helvetica", bold="Helvetica-Bold")
FONT = "SC" if FONT_DIR.is_dir() else "Helvetica"
BOLD = "SC-Bold" if FONT_DIR.is_dir() else "Helvetica-Bold"
NAVY = colors.HexColor("#091627")
BLUE = colors.HexColor("#19486A")
GREEN = colors.HexColor("#087B65")
GRAY = colors.HexColor("#53687F")
PALE = colors.HexColor("#EAF1F7")

ST = {
    "title": ParagraphStyle("scTitle", fontName=BOLD, fontSize=29, leading=37,
                            textColor=NAVY, spaceAfter=18),
    "subtitle": ParagraphStyle("scSubtitle", fontName=BOLD, fontSize=17, leading=23,
                               textColor=GREEN, spaceAfter=13),
    "heading": ParagraphStyle("scHeading", fontName=BOLD, fontSize=12.2, leading=18,
                              textColor=BLUE, spaceBefore=16, spaceAfter=8),
    "body": ParagraphStyle("scBody", fontName=FONT, fontSize=9.15, leading=15,
                           textColor=NAVY, spaceAfter=8),
    "small": ParagraphStyle("scSmall", fontName=FONT, fontSize=8.2, leading=12,
                            textColor=NAVY),
    "muted": ParagraphStyle("scMuted", fontName=FONT, fontSize=8.5, leading=13,
                            textColor=GRAY, spaceAfter=8),
}
story = []


def p(value, style="body"):
    story.append(Paragraph(value, ST[style]))


def h(value):
    story.append(Paragraph(value, ST["heading"]))


def grid(rows, widths):
    data = [[Paragraph(str(cell), ST["small"]) for cell in row] for row in rows]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#A6C4D8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F9FC")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)


def screenshot(filename, max_width=515, max_height=470):
    path = ROOT / "assets" / filename
    if not path.is_file():
        raise FileNotFoundError(f"Captura não encontrada: {path}")
    iw, ih = ImageReader(str(path)).getSize()
    scale = min(max_width / iw, max_height / ih)
    story.append(Image(str(path), width=iw * scale, height=ih * scale, hAlign="CENTER"))


story.append(Spacer(1, 76))
p("FIAP  /  GLOBAL SOLUTION 2026.2", "muted")
p("SINAL CIDADÃO", "title")
p("Relatório técnico de automação RPA", "subtitle")
p("Mobilidade inteligente, pessoas em primeiro lugar.")
story.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceBefore=8, spaceAfter=29))
grid([
    ["CAMPO", "IDENTIFICAÇÃO"],
    ["Equipe", "Henrique Lima - RM 551528<br/>Pedro Henrique Menezes - RM 97432<br/>Anny Dias - RM 98295"],
    ["Disciplina", "Robotic Process Automation (RPA)"],
    ["Repositório", "https://github.com/anny-dias/SinalCidadao"],
    ["Vídeo de até 3 minutos", "<b>PENDENTE:</b> URL da gravação"],
    ["Acesso ao MVP", "Dashboard local: http://127.0.0.1:8765"],
    ["Data da validação", "17 de novembro de 2026"],
], [150, 365])
story.append(Spacer(1, 28))
p("Status: protótipo acadêmico operacional local. A simulação e os testes foram executados no Windows; "
  "o endereço do repositório foi informado pela equipe e o link do vídeo segue pendente.", "muted")
p("<b>Benefício esperado para o cidadão:</b> uma política que considere filas e pedidos de travessia "
  "poderia reduzir esperas desnecessárias após validações específicas. Os ganhos observados neste "
  "trabalho são apenas simulados; não demonstram redução de acidentes ou segurança viária real.", "muted")
p("<b>Justificativa da tecnologia:</b> Python facilita regras e testes; SUMO cria cenários controlados; "
  "TraCI integra leituras e ajustes; SQLite mantém decisões auditáveis; JSON e JSONL compartilham "
  "resultados com o painel sem exigir infraestrutura externa.", "muted")
story.append(PageBreak())

h("01  Contexto e problema")
p("Semáforos de tempos fixos não respondem automaticamente ao volume de veículos e aos pedidos "
  "observados de travessia. O Sinal Cidadão investiga, em ambiente simulado, como regras rastreáveis "
  "podem adaptar tempos de verde e acompanhar impactos sobre mobilidade e pedestres.")
p("<b>Escopo:</b> cruzamento de quatro aproximações com calçadas e faixas, modelado no SUMO 1.28. "
  "Não há integração com câmera YOLO, ruas físicas, eletrônica de semáforos ou órgãos de trânsito.")

h("02  Processo automatizado: AS-IS e TO-BE")
grid([
    ["ANTES (AS-IS)", "DEPOIS (TO-BE)"],
    ["Inspeção manual de fluxos e tempos de espera.", "TraCI coleta métricas do SUMO e produz eventos agregados."],
    ["Consolidação manual de informações.", "Python valida, deduplica e processa eventos com regras explícitas."],
    ["Dificuldade para auditar decisões e repetir ensaios.", "SQLite, JSONL e métricas por execução com histórico no dashboard."],
    ["Execução de cenários por comandos isolados.", "Dashboard inicia SUMO-GUI, compara os três modos e executa testes."],
], [240, 275])

h("03  Arquitetura e integração")
p("<b>SUMO/TraCI → evento JSON → RPA Python → SQLite + auditoria JSONL → métricas por cenário → API local → dashboard.</b>")
p("O RPA recebe leituras com identificador, instante, disponibilidade da fonte, filas, tempos e pessoas "
  "por aproximação. O módulo <b>src/automation.py</b> processa lotes, enquanto "
  "<b>src/sumo_bridge.py</b> acompanha a simulação e regula durações permitidas. "
  "O dashboard é servido por <b>src/server.py</b>; <b>src/run_manager.py</b> executa apenas "
  "ações previamente autorizadas, uma por vez.")

h("04  Regras de decisão e segurança operacional")
p("O RPA rejeita registros inválidos, ignora identificadores repetidos e registra falhas sem derrubar "
  "o lote inteiro. Na ausência da fonte simulada de câmera, sinaliza fallback de tempo fixo. "
  "A pontuação das vias considera fila (peso 2), tempo de espera (dividido por 10) e bônus de 100 "
  "para espera igual ou superior a 90 segundos.")
p("Na política de prioridade de pedestres v4, apenas a fase principal que autoriza a faixa pode "
  "receber reserva de pelo menos 18 segundos de verde, quando há pedido ou ocupação pertinente. "
  "As fases intermediárias e amarelas não são reprogramadas. Travessias autorizadas ainda ocupadas "
  "podem estender o verde em blocos de 2 segundos, até 10 segundos por fase. "
  "O controlador não pula fases nem comanda sinais físicos.")

story.append(PageBreak())
h("Fluxo BPMN — automação ponta a ponta")
p("Diagrama gerado a partir do processo estruturado em <b>docs/fluxo.bpmn</b>. "
  "Inclui decisões, processamento repetitivo, falhas e publicação do resultado no MVP.", "muted")
bpmn_image = ROOT / "assets" / "fluxo_bpmn.png"
if not bpmn_image.is_file():
    raise FileNotFoundError("Gere o BPMN primeiro: python docs/render_bpmn.py")
story.append(Image(str(bpmn_image), width=349, height=648, hAlign="CENTER"))

story.append(PageBreak())
h("05  Cenários comparados (demanda alta, 600 passos, semente 42)")
grid([
    ["INDICADOR", "FIXO", "ADAPTATIVO", "COM PRIORIDADE"],
    ["Viagens veiculares concluídas", "293", "328", "310"],
    ["Espera média veicular/viagem", "27,24 s", "15,44 s", "15,27 s"],
    ["Espera observada antes da faixa", "0,99 s", "0,98 s", "0,91 s"],
    ["Ajustes verdes veiculares", "0", "19", "19"],
    ["Reservas de prioridade pedestre", "0", "0", "11"],
    ["Travessias observadas concluídas", "175", "173", "173"],
    ["Alertas de espera registrados", "0", "0", "0"],
], [198, 88, 105, 124])
story.append(Spacer(1, 13))
p("<b>Resultado comparado ao fixo:</b> o modo adaptativo com prioridade registrou "
  "<b>43,94% menos espera média veicular</b> e <b>8,08% menos espera observada "
  "antes da faixa</b>. O modo sem prioridade concluiu mais viagens (328 vs. 310), "
  "demonstrando uma troca entre objetivos que deve ser explicitada.")
p("Os números foram reproduzidos em novas execuções iniciadas pelo botão "
  "<b>Comparar 3 cenários</b> em 17/11/2026, às 19:20, 19:21 e 19:22. "
  "Tratam-se de resultados do cenário simulado, não de teste multissemente e "
  "não comprovam redução de acidentes ou risco viário real.")

h("06  Testes, rastreabilidade e tratamento de falhas")
p("<b>38/38 testes automatizados aprovados</b>, executados pelo dashboard no Windows. "
  "As verificações incluem entrada inválida, duplicidade, fallback, priorização, "
  "métricas, vínculo entre pedido e faixa, restrições de fases, integração do dashboard "
  "e bloqueio de operações simultâneas.")
grid([
    ["OCORRÊNCIA", "RESPOSTA DA AUTOMAÇÃO"],
    ["JSON inválido / inexistente", "Log de erro e retorno não zero."],
    ["Evento com dados inválidos", "Auditar falha e continuar com próximos eventos."],
    ["ID repetido", "Ignorar repetição, registrar SKIPPED_DUPLICATE."],
    ["Falha de fonte/câmera simulada", "Registrar FIXED_TIME_FALLBACK."],
    ["Erro SQLite ou SUMO/TraCI", "Sinalizar falha sem reportar conclusão bem-sucedida."],
    ["Duas operações solicitadas juntas", "Bloquear a segunda até o término da primeira."],
], [205, 310])

story.append(PageBreak())
h("07  Evidências disponíveis no projeto")
p("<b>logs/exemplo_auditoria.jsonl</b> - amostra real gerada pela automação com dados sintéticos.<br/>"
  "<b>assets/fluxo_bpmn.png</b> - representação visual do BPMN (incluída neste PDF).<br/>"
  "<b>data/runs/*.metrics.json</b> - métricas criadas localmente pelas simulações (não versionadas).<br/>"
  "<b>data/runs/*.safety.jsonl</b> - auditoria SUMO local (não versionada).<br/>"
  "<b>docs/fluxo.bpmn</b> - definição BPMN editável.<br/>"
  "<b>docs/EVIDENCIAS.md</b> - comandos e lista de capturas reais a anexar.<br/>"
  "<b>docs/PDD.md</b> - descrição detalhada do processo.<br/>"
  "<b>docs/roteiro-video.md</b> - roteiro de demonstração.")
p("<b>Execução de amostra:</b> 4 processados, 1 duplicado, 1 inválido. "
  "Entre os registros auditados: <b>GRANT_GREEN</b>, <b>HOLD_PEDESTRIAN_PHASE</b>, "
  "<b>FIXED_TIME_FALLBACK</b>, <b>SKIPPED_DUPLICATE</b> e <b>ERROR</b>.")

p("As próximas páginas contêm capturas reais enviadas pela equipe em 17/11/2026. "
  "O PDF completo exportado do painel acompanha o repositório em "
  "<b>assets/dashboard_comparativo.pdf</b>.", "muted")

h("08  Limitações e responsabilidade")
p("A simulação utiliza um único cruzamento simplificado, 600 passos e semente fixa. "
  "A métrica de espera de pedestres é derivada de amostras TraCI, não de sensores validados. "
  "Não foram medidos acidentes, emissões, conformidade normativa ou desempenho em escala de rede. "
  "O programa SUMO define as fases seguras; a heurística Python precisa de avaliação especializada "
  "antes de qualquer aplicação fora do ambiente acadêmico.")
p("O servidor escuta em 127.0.0.1 e aceita somente ações locais predefinidas; "
  "não deve ser exposto à internet nem conectado a controladores físicos.")

h("09  Preparação da entrega")
p("1. Conferir os nomes e RMs da equipe informados neste relatório.<br/>"
  "2. Conferir a publicação em https://github.com/anny-dias/SinalCidadao, sem .venv ou dados privados.<br/>"
  "3. Gravar vídeo de até três minutos, utilizando cortes para simulações longas.<br/>"
  "4. Inserir links válidos e conferir os requisitos do enunciado antes de enviar este PDF.")

h("10  Conclusão")
p("O Sinal Cidadão integra simulação, automação RPA, auditoria, regras adaptativas "
  "de prioridade de travessia e dashboard de execução e análise. "
  "A validação demonstrou funcionamento reprodutível no cenário testado, "
  "com documentação de limitações e sem alegações de implantação viária real.")

story.append(PageBreak())
h("Anexo A — Integração com o MVP e cenário simulado")
p("Captura do dashboard em execução, exibindo os três cenários comparáveis e seus indicadores.", "muted")
screenshot("dashboard.png", max_height=365)
story.append(Spacer(1, 12))
p("Cruzamento em execução no SUMO-GUI: veículos, travessias e estados de sinalização simulados.", "muted")
screenshot("sumo_cruzamento.png", max_height=260)

story.append(PageBreak())
h("Anexo B — Testes e tratamento de exceções")
p("Execução real da suíte de testes no Windows: 38 verificações concluídas com OK.", "muted")
screenshot("testes_38_ok.png", max_height=390)
story.append(Spacer(1, 16))
p("Falha intencional de entrada inexistente, seguida da leitura do registro de auditoria "
  "com codificação UTF-8. A ocorrência ERROR e o caminho ausente permanecem verificáveis.", "muted")
screenshot("tratamento_falha.png", max_height=110)


def footer(canvas, doc):
    canvas.setFont(FONT, 7.7)
    canvas.setStrokeColor(colors.HexColor("#D4E0EA"))
    canvas.line(42, 40, A4[0] - 42, 40)
    canvas.setFillColor(GRAY)
    canvas.drawString(42, 26, "SINAL CIDADÃO  |  FIAP Global Solution 2026.2")
    canvas.drawRightString(A4[0] - 42, 26, f"Página {doc.page}")


doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=40, rightMargin=40,
                        topMargin=44, bottomMargin=56)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUTPUT)
