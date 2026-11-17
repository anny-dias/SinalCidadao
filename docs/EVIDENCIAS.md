# Evidências de RPA — Sinal Cidadão

## Evidência executável disponível

O arquivo `data/leituras.json` contém **dados sintéticos** de seis eventos e permite reproduzir:

- quatro eventos processados com sucesso;
- uma duplicata registrada como `SKIPPED_DUPLICATE`;
- um evento inválido registrado como `ERROR`;
- fallback `FIXED_TIME_FALLBACK` quando a fonte simulada está indisponível;
- decisão `HOLD_PEDESTRIAN_PHASE` quando há pedestres na faixa.

O arquivo `logs/exemplo_auditoria.jsonl` foi **gerado executando a automação** sobre essa amostra. Os timestamps registram a execução do exemplo; os eventos simulados não representam medições de rua.

Para reproduzir sem misturar com o banco principal, no PowerShell a partir da raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m src.cli --input data/leituras.json --db data/evidencia_rpa.sqlite --log logs/evidencia_local.jsonl
```

Resultado esperado na primeira execução usando banco novo:

```json
{"processed": 4, "duplicates": 1, "failed": 1}
```

Para demonstrar uma falha de arquivo ausente, sem interromper o projeto:

```powershell
.\.venv\Scripts\python.exe -m src.cli --input data/arquivo_que_nao_existe.json --db data/evidencia_rpa.sqlite --log logs/evidencia_falha_local.jsonl
```

O comando deve terminar com erro **e** deixar registro de auditoria em `logs/evidencia_falha_local.jsonl`. Essa falha intencional é uma evidência de tratamento, não um problema de instalação.

## Testes

Execute:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**Resultado observado e informado pela equipe em 17/11/2026:** `Ran 38 tests` / `OK`. O script de testes é reexecutável, inclusive pelo dashboard. Os resultados de SUMO foram informados pela equipe após a comparação em três cenários.

## Capturas reais recebidas da equipe

Os seguintes arquivos foram fornecidos pela equipe em 17/11/2026 e estão em `assets/`:

1. `dashboard.png` — painel com os três cenários carregados.
2. `sumo_cruzamento.png` — SUMO-GUI com veículos e pedestres no cruzamento.
3. `testes_38_ok.png` — terminal ou dashboard exibindo `Ran 38 tests` e `OK`.
4. `tratamento_falha.png` — comando de arquivo ausente e log com erro registrado, sem dados pessoais. A captura foi refeita com leitura UTF-8 e acentuação correta.
5. `dashboard_comparativo.pdf` — exportação completa de três páginas do dashboard no navegador.

O arquivo `assets/fluxo_bpmn.png` é um diagrama **gerado a partir de `docs/fluxo.bpmn`**, não uma captura de execução.

Não altere screenshots ou saídas para simular resultados que não ocorreram. Para melhorar uma futura captura do erro, use `Get-Content -Encoding utf8 logs/evidencia_falha_local.jsonl` no PowerShell. Confirme com `git status` e publique usando `git add`, `git commit`, `git push`.
