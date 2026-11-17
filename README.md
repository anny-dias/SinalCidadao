# Sinal Cidadão RPA — FIAP Global Solution 2026.2

Automação operacional do MVP **Sinal Cidadão**, semáforo adaptativo CitizenTech. Processa leituras agregadas produzidas pelo simulador SUMO ou exportadas pelo módulo de visão computacional, valida lotes, remove duplicados, aplica regras de priorização, registra auditoria em SQLite e publica decisões em uma API e painel HTTP.

> **Limite de segurança:** demonstração acadêmica em simulação. Este software **não controla semáforos reais**. A presença de pedestres é um indicador agregado do simulador, não um sensor de segurança certificado.

## Execução (Python 3.10+, sem dependências externas)

```bash
python -m src.cli --input data/leituras.json --db data/citizenflow.db
python -m src.server --db data/citizenflow.db --port 8765
```

Acesse `http://localhost:8765` para consultar as decisões e `http://localhost:8765/api/decisions` para integrar com outro componente do MVP. Execute `python -m unittest discover -s tests -v` para os cenários de validação.

## Guia rápido — demonstração no Windows

Execute estes comandos **a partir da raiz do projeto** no PowerShell. Eles demonstram a automação de ponta a ponta: processamento de eventos, decisões, exceções, auditoria, testes, SUMO e integração ao dashboard.

### 1. Terminal A: iniciar o dashboard

```powershell
.\.venv\Scripts\python.exe -m src.server --port 8765
```

Abra `http://localhost:8765` e **deixe esse terminal aberto**. O servidor continua executando enquanto espera requisições.

### 2. Terminal B: processar eventos de demonstração

```powershell
.\.venv\Scripts\python.exe -m src.cli --input data/leituras.json --db data/video_demonstracao_01.sqlite --log logs/video_demonstracao_01.jsonl
Get-Content -Encoding utf8 logs/video_demonstracao_01.jsonl
```

Com um banco novo, a entrada sintética produz `4` processados, `1` duplicado e `1` inválido. A auditoria exibe as ações `GRANT_GREEN`, `HOLD_PEDESTRIAN_PHASE`, `FIXED_TIME_FALLBACK`, `SKIPPED_DUPLICATE` e `ERROR`. Se o banco já foi utilizado, novas execuções contarão duplicados; escolha outro nome de banco para um teste novo sem apagar o anterior.

### 3. Terminal B: demonstrar tratamento de falhas

```powershell
.\.venv\Scripts\python.exe -m src.cli --input data/arquivo_que_nao_existe.json --db data/video_demonstracao_01.sqlite --log logs/video_falha_01.jsonl
Get-Content -Encoding utf8 logs/video_falha_01.jsonl
```

**O primeiro comando deve falhar intencionalmente.** O segundo mostra o registro com `timestamp` e `level: ERROR`, comprovando a identificação e a auditoria de arquivo ausente.

### 4. Terminal B: executar os testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

O grupo validou `Ran 38 tests` e `OK`; confira o resultado atual no terminal.

### 5. Terminal B: demonstrar o SUMO-GUI

```powershell
.\.venv\Scripts\python.exe -m src.sumo_bridge --mode adaptive --pedestrians --demand high --gui
```

Mostre veículos, pedestres e mudança de fases. Deixe a simulação concluir os 600 passos para gerar métricas; **não feche o SUMO enquanto o Python estiver conectado**.

### 6. Navegador: demonstrar o MVP

1. Abra `http://localhost:8765` e clique em **Atualizar dados**.
2. Mostre os indicadores e o comparativo dos três cenários.
3. Role até **Laboratório de simulação**, mostre os três modos e os botões **Iniciar simulação**, **Comparar 3 cenários** e **Executar testes**.
4. Clique em **Executar testes** para demonstrar a integração dos comandos pelo painel.
5. Mostre **Últimas simulações** com os resultados já registrados.

**Atenção ao vídeo de até três minutos:** o botão **Comparar 3 cenários** executa três simulações completas, podendo levar vários minutos. Utilize resultados existentes ou cortes de tempo identificados, sem simular execução instantânea.

**Ordem de apresentação sugerida:** lote e falha no terminal → testes → SUMO → dashboard → métricas → conclusão. O roteiro resumido de falas está em `docs/roteiro-video.md`.

## SUMO conectado (experimental)

Confira [sumo/README.md](sumo/README.md). Requer os executáveis `sumo` e `netconvert` e o pacote `traci` (`pip install traci`). A ponte realiza leitura automática de veículos e pedestres simulados, registra eventos a cada cinco passos e gera métricas comparáveis entre os três cenários. O cenário com pedestres foi executado e validado no SUMO 1.28 local no Windows em 17/11/2026. O controle TraCI não muda a ordem de fases definida no SUMO.

### Experimento com pedestres — métricas e auditoria

```powershell
.\.venv\Scripts\python.exe -m src.sumo_bridge --mode fixed --pedestrians
.\.venv\Scripts\python.exe -m src.sumo_bridge --mode adaptive --pedestrians --gui
```

Cada execução cria `data/runs/<modo>-<data>.metrics.json` e `data/runs/<modo>-<data>.safety.jsonl`. O novo arquivo de auditoria registra solicitações de travessia pendentes (espera observada de 15 s ou mais) e extensões de verde autorizadas, sem identificadores de pessoas. As métricas `average_pre_crossing_wait_seconds` e `average_crossing_seconds` separam, respectivamente, espera antes de entrar na faixa e tempo efetivo observado na faixa. Ausência de observações produz `null`, não zero inventado.

**Limitação importante:** o pedido de travessia é monitorado e auditado. Na política atual v4, a prioridade reserva tempo na fase principal de verde já autorizada, sem saltar fases; a extensão só ocorre quando há ocupação de faixa autorizada. Estes números avaliam o protótipo simulado, não comprovam segurança de travessia real. IDs temporários de pedestres existem apenas em memória para calcular duração, nunca nos relatórios.

### Prioridade de pedestres e ensaio de alta demanda

A versão atual usa a **política v4**, documentada abaixo. A fase principal que autoriza a travessia pode reservar ao menos 18 segundos de verde; fases intermediárias e amarelas são preservadas. O registro `PRIORIDADE_PEDESTRE` documenta cada reserva. Trata-se de heurística de simulação, não apropriada para operação viária real.

O cenário `--demand high` aumenta a frequência de pedestres mantendo as mesmas rotas de veículos e uma semente fixa. Compare três execuções:

```powershell
.\.venv\Scripts\python.exe -m src.sumo_bridge --mode fixed --pedestrians --demand high
.\.venv\Scripts\python.exe -m src.sumo_bridge --mode adaptive --pedestrians --demand high --no-pedestrian-priority
.\.venv\Scripts\python.exe -m src.sumo_bridge --mode adaptive --pedestrians --demand high --gui
```

Os três cenários permitem diferenciar a vantagem do adaptativo e o efeito adicional da prioridade pedestre. Verifique `pedestrian_priority_adjustments`, `maximum_observed_pre_crossing_wait_seconds`, `average_pre_crossing_wait_seconds` e os indicadores veiculares. Não conclua superioridade sem comparar os resultados.

**Revisão do controlador após testes de alta demanda:** pedidos de travessia são mantidos na memória até o pedestre observado ingressar na faixa ou deixar o simulador. O campo `priority_block_reason_samples` explica as tentativas que não encurtaram a fase; o arquivo `.safety.jsonl` contém eventos `PRIORIDADE_NAO_APLICADA` com o motivo (`TRAVESSIA_AUTORIZADA_OCUPADA`, `VERDE_MINIMO_OU_TEMPO_INSUFICIENTE` ou `AGUARDANDO_LIMIAR`). O contador `pedestrian_wait_alerts` agora registra quando cada espera pendente ultrapassa 15 segundos, independentemente do instante da coleta periódica. Ainda é possível haver zero ajustes se todas as oportunidades estiverem bloqueadas por segurança; isso deve ser investigado, nunca mascarado.

**Controlador experimental v3 — pedido vinculado à faixa:** `traci.person.getNextEdge()` identifica a próxima aresta da caminhada. Se ela for uma faixa controlada, o pedido pendente é associado à faixa correspondente em `getControlledLinks()`. A fase verde veicular pode ser encurtada somente quando essa faixa está vermelha e existe tempo suficiente para preservar o mínimo. Ao abrir uma nova fase, os pedidos pendentes já são considerados. Se a próxima aresta ainda for uma área de caminhada, o pedido continua pendente sem prioridade específica até que a faixa seja identificável. O log distingue `SEM_FAIXA_VERMELHA_MAPEADA` dos demais bloqueios. Não são puladas fases nem modificados estados `r/y/g`. A versão exige ensaio visual no SUMO local e não equivale a controlador de tráfego homologado.

**Controlador experimental v4 — substitui a política de encurtamento da v3:** a auditoria mostrou que a tentativa de encurtar os verdes intermediários de limpeza (fases 1/4) nunca tinha margem, pois esses tempos já estavam no mínimo. A v4 **não altera as fases intermediárias nem os amarelos** no cenário com pedestres. Somente uma fase principal que explicitamente autoriza travessias pode ter o verde planejado para pelo menos **18 segundos** quando, ao início dela, houver pedido vinculado à sua faixa ou alguém ocupando uma faixa autorizada. A duração calculada por fila que já for maior é preservada. Esse planejamento registra `PRIORIDADE_PEDESTRE`; a extensão limitada de 2 em 2 segundos para quem ainda ocupa faixa permanece separada. `pedestrian_priority_adjustments` conta reservas adicionais de tempo, não saltos de fase. A política é experimental e pode aumentar espera de veículos ou de pedestres em outro sentido: comparar os três modos antes de considerar o resultado positivo.

**Visualização validada:** ao usar `--gui`, `src/sumo_bridge.py` carrega `sumo/sinal_cidadao.view.xml` com esquema visual **real world**, enquadramento confirmado pelo grupo e intervalo de 100 ms por passo. `src/visual_style.py` colore veículos conforme a aproximação e destaca pedestres. Estas ações são visuais e não alteram geometria, regras ou métricas. A rede não foi compactada, pois isso invalidaria as comparações históricas.

**Enquadramento validado no SUMO-GUI (17/11/2026):** substitua somente a linha `<viewport>` em `sumo/sinal_cidadao.view.xml` por `<viewport zoom="713.28" x="252.25" y="248.38" angle="0"/>` para reproduzir o enquadramento escolhido pelo grupo. O arquivo de visualização não interfere no controlador.

## Dashboard integrado aos relatórios SUMO

Após executar os três cenários de alta demanda indicados acima, mantenha os arquivos `.metrics.json` na pasta `data/runs` e, em **outro terminal**, execute:

```powershell
.\.venv\Scripts\python.exe -m src.server --port 8765
```

Abra **http://localhost:8765** no navegador. O painel mostra os três modos, indicadores veiculares e de pedestres, reduções percentuais em relação ao modo fixo, últimas execuções e prioridades acionadas. Atualize manualmente ou aguarde 15 segundos após outra simulação. Endpoints de leitura: `GET /api/runs` (até 100 relatórios recentes), `GET /api/comparison` (últimos três cenários compatíveis de 600 passos) e `GET /api/decisions` (decisões SQLite, que só aparecem se houver base gerada em `data/citizenflow.db`). O dashboard funciona mesmo sem SQLite, pois os indicadores SUMO vêm de `data/runs`. A API é local em `127.0.0.1`, não dá comandos ao SUMO nem controla semáforos físicos.

Se a porta 8765 estiver reservada, escolha outra porta livre e utilize o mesmo número no endereço do navegador. O terminal permanece aguardando requisições enquanto o servidor estiver aberto; encerre com `Ctrl+C`.

### Laboratório de simulação no dashboard

O painel possui três ações, além da visualização dos relatórios:

- **Iniciar simulação:** selecione o cenário fixo, adaptativo ou adaptativo com prioridade e clique em iniciar. O SUMO-GUI abre em janela separada, com a configuração visual definida em `sumo/sinal_cidadao.view.xml`.
- **Comparar 3 cenários:** executa os três cenários de demanda alta, sequencialmente, com SUMO-GUI. Cada janela fecha automaticamente quando os 600 passos terminam. Os relatórios novos aparecem na comparação após a execução.
- **Executar testes:** inicia os testes de unidade e integração offline (`unittest discover`) e apresenta o resultado e a saída detalhada no próprio painel.

**Atenção:** o servidor Python deve continuar aberto no terminal. Apenas um trabalho é permitido por vez; não feche manualmente o SUMO durante o trabalho, pois isso interrompe a conexão TraCI e registra falha. Caso uma execução termine com erro, consulte o detalhe da operação e tente novamente após resolver a causa. A API do laboratório aceita somente ações predefinidas em `POST /api/jobs`; consulte `GET /api/jobs` para progresso. Não são aceitos comandos arbitrários do navegador, e a API escuta apenas `127.0.0.1`. Não expor essa porta à internet nem usar o projeto para comandar equipamentos reais.

## Validação final dos três cenários

Use o verificador **sem abrir o SUMO novamente**. Ele lê apenas os relatórios que você já produziu e cria um arquivo JSON auditável:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m src.validate_experiments --output data/validacao_final.json
```

O relatório confere que existem três cenários equivalentes (600 passos, demanda alta, pedestres habilitados), que as travessias concluídas não excedem as iniciadas, que os tempos de espera não são negativos, que não houve alterações de fase no modo fixo e que não houve prioridade acionada nos modos sem prioridade. Também calcula as diferenças percentuais de espera do modo adaptativo prioritário em relação ao fixo. **A ausência de alertas de espera não comprova segurança viária real**. A seleção usa os relatórios mais recentes; preserve os arquivos originais de cada execução em `data/runs`.

## Arquitetura

`SUMO / YOLO (leituras agregadas JSON) -> RPA Python (validação, deduplicação, regras) -> SQLite (decisões e auditoria) -> API HTTP JSON -> painel / outro componente CitizenTech`

O adaptador de entrada usa JSON com `event_id`, `timestamp`, `approaches` e `camera_online`. Cada aproximação contém `id`, `queue_vehicles`, `wait_seconds` e `pedestrians_crossing`. A ponte opcional TraCI gera eventos desse formato diretamente do SUMO. O módulo YOLO ainda não está integrado.

## Regras

- Quando câmera offline: `FIXED_TIME_FALLBACK`, preservando a operação simulada em tempo fixo.
- Quando houver pedestre na travessia: `HOLD_PEDESTRIAN_PHASE`, respeitando limite de extensão no simulador.
- Caso contrário: maior pontuação `fila * 2 + espera_segundos / 10`; em empate, ordem de aproximações.
- Se `wait_seconds >= 90`, adiciona bônus de 100 à pontuação para reduzir risco de fome.
- Duração do verde calculada entre 10 e 45 segundos; extensão de pedestres limitada a 10 segundos por fase no simulador.

**Importante:** estes parâmetros são hipóteses de protótipo, não tempos oficiais de engenharia de tráfego. A fase amarela, o intervalo de segurança e os intertravamentos são responsabilidade do controlador de simulação e não podem ser ignorados.

## Falhas e auditoria

- JSON ausente/corrompido: falha explícita e exit code não zero.
- Registro inválido: `ERROR` no log e processamento dos demais itens.
- `event_id` repetido: item marcado `SKIPPED_DUPLICATE`, sem nova decisão.
- Falha no banco: rollback/transação e saída com erro.
- Logs estruturados em JSON Lines, sem imagens, rostos, placas ou credenciais.

## Estrutura

- `src/`: automação e servidor de integração.
- `data/`: eventos fictícios de demonstração.
- `docs/`: PDD, BPMN, diagrama gerado, guia de evidências e roteiro de vídeo.
- `tests/`: testes automatizados.
- `assets/`: fluxograma BPMN, capturas reais do dashboard, SUMO, testes, tratamento de falha e PDF comparativo.
- `logs/`: exemplo de auditoria com dados sintéticos; logs locais adicionais não são versionados.

## Publicação e entrega

1. Conferir integrantes/RMs e o endereço do GitHub já preenchidos; adicionar o link do vídeo no relatório PDF (gerado com `python docs/build_report.py` no ambiente com `reportlab`).
2. Publicar um repositório público GitHub com esta pasta; conferir que `.gitignore` exclui `.venv`, caches, logs e dados transitórios.
3. Gravar vídeo de até 3 minutos mostrando terminal, sucesso/erro, SUMO-GUI, integração ao dashboard, comparativo e testes. Siga o **Guia rápido — demonstração no Windows** deste README e o roteiro resumido `docs/roteiro-video.md`.
4. Conferir o enunciado e enviar PDF e links requeridos na plataforma da disciplina. O prazo informado pelo grupo foi 19/11/2026, 23h55; verificar antes do envio.

**Evidências para a rubrica:** `docs/EVIDENCIAS.md` contém comandos para demonstrar sucesso, regra de decisão, duplicidade e falha sem interromper a aplicação. O BPMN está em `docs/fluxo.bpmn` e como imagem em `assets/fluxo_bpmn.png` (também incluída no relatório). As capturas reais do dashboard, SUMO, testes e falha recebidas da equipe estão em `assets/` e nos anexos do PDF técnico.

**Resultados validados no Windows (17/11/2026):** o dashboard executou 38 testes com `OK` e realizou a comparação completa dos três modos SUMO-GUI. No cenário prioritário, o tempo médio de espera por viagem veicular caiu de 27,24 s para 15,27 s (-43,94%) e a espera observada antes da travessia de 0,99 s para 0,91 s (-8,08%) em relação ao fixo. O adaptativo sem prioridade concluiu mais viagens veiculares que o prioritário (328 contra 310). Esses valores dependem do cenário e da semente; não são garantia de comportamento em trânsito real.

## Equipe

- Henrique Lima — RM 551528
- Pedro Henrique Menezes — RM 97432
- Anny Dias — RM 98295

**Repositório informado pela equipe:** https://github.com/anny-dias/SinalCidadao

## Segurança / LGPD

O sistema só coleta contagens agregadas e tempos de espera simulados. Não grava frames, reconhecimento facial, placas ou dados pessoais. Para produção, aplicar autenticação, autorização, HTTPS, retenção de logs, controle de acesso e revisão por engenheiros de tráfego.
