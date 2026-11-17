# PDD - Sinal Cidadão | Global Solution FIAP 2026.2

**Status:** protótipo acadêmico validado em simulação SUMO 1.28 e Python 3.12 no Windows (17/11/2026). Não controla semáforos reais.

## 1. Objetivo e processo atual

**Problema:** decisões fixas ou manuais sobre o tempo semafórico não respondem diretamente às filas e aos pedidos de travessia observados no cruzamento simulado. A comparação de cenários e a produção de evidências também exigiriam operações manuais.

**AS-IS:** coletar/consultar os dados, estimar prioridades, avaliar tempos dos sinais e registrar comparações manualmente.

**TO-BE:** o simulador fornece contagens agregadas; a ponte TraCI gera eventos JSON; o RPA valida e deduplica; as decisões são registradas em SQLite e JSON Lines; o controlador ajusta *apenas a duração das fases permitidas*; métricas e auditoria são registradas; o dashboard exibe resultados, inicia simulações e executa testes por comandos predefinidos.

**Benefício potencial ao cidadão:** com validação adequada, o controle adaptativo poderia reduzir esperas desnecessárias de veículos e pedestres e melhorar a previsibilidade da travessia. A evidência atual é restrita ao cruzamento simulado; não comprova segurança nem ganhos em vias reais.

**Justificativa técnica:** Python facilita expressar e testar regras de lote e exceções; SUMO permite cenários controlados e reproduzíveis sem intervenção em ruas; TraCI conecta leituras e controle de duração das fases; SQLite mantém auditoria local estruturada; JSON/JSONL facilitam interoperabilidade com dashboard e análise posterior.

## 2. Entradas, recursos e fronteiras

| Entrada | Contrato / origem |
| --- | --- |
| Leituras | Lista JSON: `event_id`, `timestamp`, `camera_online`, `approaches[]` com via, fila, espera e pessoas na travessia. |
| Sensores simulados | TraCI: contagem de veículos parados, tempo de espera, fases do controlador e pessoas/faixas do SUMO. |
| Cenários | SUMO `sumo/cross_pedestrians_high.sumocfg`, 600 passos, semente fixa 42. |
| Comandos UI | API local restrita: simular fixo, adaptativo, adaptativo com prioridade, comparar os três ou executar testes. |

**Exclusões:** câmeras YOLO reais não integradas; nenhum controlador de tráfego físico, sem comunicação com hardware de semáforo, sem imagens/rostos/placas armazenados. Os dados de pedestres são agregados; identificadores temporários TraCI servem apenas para medir duração em memória.

## 3. Regras e decisões

1. Validar entrada; rejeitar JSON ausente/inválido e registrar erro; rejeitar individualmente eventos com campos inválidos e continuar com os demais.
2. Consultar chave `event_id` no SQLite e ignorar duplicados, emitindo `SKIPPED_DUPLICATE`.
3. Se `camera_online=false`, registrar `FIXED_TIME_FALLBACK` (demonstração de 30 s simulados).
4. Se houver pessoa cruzando, registrar `HOLD_PEDESTRIAN_PHASE`; em outros eventos escolher via por pontuação `fila × 2 + espera/10`, com bônus 100 quando espera >= 90 s. Verde nominal entre 10 e 45 s.
5. Controlador TraCI adaptativo: ajusta **duração** do verde veicular corrente de acordo com a fila. Não define novos estados vermelho/amarelo/verde e não salta fases.
6. Prioridade v4 de pedestres: somente na fase principal que já autoriza a travessia solicitada, planejar ao menos 18 s de verde quando a demanda pendente ou a ocupação autorizada justificar. Preservar tempos nativos das fases intermediárias e amarelas.
7. Quando a travessia autorizada está ocupada e o verde está acabando, prolongar a fase em blocos de 2 s, limitado a 10 s adicionais por fase. Registrar cada extensão em `.safety.jsonl`.
8. Eventos de espera pendente/impedimentos de prioridade geram registros com motivo; limiar de alerta de espera observado: 15 s.

**Importante:** `src.automation.decide` registra recomendações RPA; o controlador TraCI aplica sua própria política restrita, sempre subordinada ao programa semafórico SUMO. Os registros de auditoria não equivalem a comando físico.

## 4. Fluxo, exceções e saídas

**BPMN:** `docs/fluxo.bpmn` representa a validação, a deduplicação, os gateways de decisão, a repetição por evento e os caminhos de erro.

**Exceções:** arquivo inexistente ou malformado => log + erro; evento malformado => log + próximo evento; duplicado => ignorar sem nova decisão; câmera offline => fallback simulado; erro SQLite => erro e rollback; falha SUMO/TraCI => falha da operação no painel com saída para diagnóstico, sem atribuir sucesso.

**Saídas:**

- `data/runs/*.metrics.json`: resultados por cenário, incluindo viagens, tempos médios e ações do controlador.
- `data/runs/*.safety.jsonl`: trilha de prioridade e espera de pedestres.
- `data/runs/*.telemetry.jsonl` e `*.db`: eventos de leitura e decisões por execução.
- `data/validacao_final.json`: resultado do verificador offline dos três cenários.
- `GET /api/runs`, `/api/comparison`, `/api/decisions` e `/api/jobs`: dados do dashboard.
- `POST /api/jobs`: apenas ações locais de lista fechada; uma operação por vez.

## 5. Critérios de aceitação e evidências (17/11/2026)

| Critério | Evidência |
| --- | --- |
| Testes automatizados | 38/38 aprovados no Windows (relato de execução via dashboard). |
| Três cenários | Concluídos com botão do dashboard às 19:20, 19:21 e 19:22. |
| Modo fixo | 293 viagens veiculares concluídas, espera média veicular 27,24 s, espera pedestre 0,99 s, 0 ajustes. |
| Adaptativo sem prioridade | 328 viagens concluídas, espera veicular 15,44 s, pedestre 0,98 s, 19 ajustes, 0 prioridades. |
| Adaptativo com prioridade | 310 viagens concluídas, espera veicular 15,27 s, pedestre 0,91 s, 19 ajustes e 11 prioridades. |
| Comparação com fixo | Espera veicular -43,94%; espera antes da travessia -8,08% no cenário prioritário. |
| Integração dashboard | Abre SUMO-GUI, executa testes e comparação sequencial, atualiza histórico. |

Resultados obtidos **no mesmo cenário de 600 passos e semente 42**; não constituem experimento multissemente nem demonstram segurança viária real. O adaptativo com prioridade concluiu menos viagens do que o adaptativo sem prioridade (310 vs. 328), indicando uma troca entre objetivos de mobilidade e travessia.

## 6. Segurança e limites

Servidor escuta apenas `127.0.0.1`; POST verifica origem/host e só permite comandos predefinidos. Não expor a API em rede pública. Visualização e controles do SUMO-GUI são exclusivamente demonstrativos. Evitar conclusões de redução de acidentes, de emissões e de garantia operacional: esses desfechos não foram medidos.

## 7. Pendências de entrega

- Integrantes informados: Henrique Lima (RM 551528), Pedro Henrique Menezes (RM 97432) e Anny Dias (RM 98295). Confirmar professor/turma no enunciado e adicionar links finais.
- Conferir repositório informado pela equipe: https://github.com/anny-dias/SinalCidadao, preservando `.gitignore` e sem enviar `.venv`, dados pessoais ou arquivos temporários.
- Gravar vídeo de até 3 minutos (ver `docs/roteiro-video.md`).
- Confirmar que o PDF e os links exigidos pela disciplina correspondem ao enunciado vigente.
