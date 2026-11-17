"""Renderiza uma vista BPMN a partir dos nós e fluxos em docs/fluxo.bpmn.

Requer Graphviz (comando dot). A imagem é uma representação do XML,
não uma captura de execução nem substitui o arquivo BPMN editável.
"""

import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "fluxo.bpmn"
TARGET = ROOT / "assets" / "fluxo_bpmn.png"
NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}


def quote(value):
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def main():
    root = ET.parse(SOURCE).getroot()
    process = root.find("bpmn:process", NS)
    if process is None:
        raise ValueError("Processo BPMN não encontrado")
    shapes = {"startEvent": "circle", "endEvent": "doublecircle", "exclusiveGateway": "diamond", "task": "box"}
    nodes = {}
    lines = [
        "digraph SinalCidadao {",
        'graph [rankdir=TB, bgcolor="white", pad="0.25", nodesep="0.35", ranksep="0.34", splines=polyline];',
        'node [fontname="DejaVu Sans", fontsize=11, color="#1C4962", fontcolor="#08253A", style="filled", fillcolor="#EDF5F9", penwidth=1.4];',
        'edge [fontname="DejaVu Sans", fontsize=9, color="#47899B", arrowsize=0.7];',
    ]
    for child in process:
        name = child.tag.rsplit("}", 1)[-1]
        if name not in shapes:
            continue
        label = child.attrib.get("name", child.attrib["id"])
        # Colunas menores ajudam a manter as etapas legíveis no relatório A4.
        if len(label) > 22:
            words = label.split()
            rows, line = [], ""
            for word in words:
                if len(line + " " + word) > 22 and line:
                    rows.append(line)
                    line = word
                else:
                    line = (line + " " + word).strip()
            rows.append(line)
            label = "\n".join(rows)
        nodes[child.attrib["id"]] = name
        color = "#D6F5E7" if name in ("startEvent", "endEvent") else "#EDF5F9"
        if child.attrib["id"] in ("fileError", "failed", "skip"):
            color = "#FFF0E7"
        lines.append(f'{quote(child.attrib["id"])} [label={quote(label)}, shape={shapes[name]}, fillcolor={quote(color)}];')
    for flow in process.findall("bpmn:sequenceFlow", NS):
        source, target = flow.attrib["sourceRef"], flow.attrib["targetRef"]
        if source not in nodes or target not in nodes:
            raise ValueError(f"Fluxo inválido: {source} → {target}")
        condition = flow.find("bpmn:conditionExpression", NS)
        label = f', label={quote(condition.text or "")}' if condition is not None else ""
        lines.append(f'{quote(source)} -> {quote(target)} [{label.lstrip(", ")}];' if label else f'{quote(source)} -> {quote(target)};')
    lines.append("}")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["dot", "-Tpng", "-o", str(TARGET)], input="\n".join(lines), text=True, check=True)
    print(TARGET)


if __name__ == "__main__":
    main()
