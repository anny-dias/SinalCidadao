# Cruzamento virtual SUMO

## Gerar a rede (Windows ou Linux)

```bash
netconvert --node-files sumo/cross.nod.xml --edge-files sumo/cross.edg.xml --output-file sumo/cross.net.xml --tls.default-type static
```

Primeira execução em janela gráfica:

```bash
sumo-gui -c sumo/cross.sumocfg
```

O cenário inicial modela quatro aproximações com demandas distintas e semáforo gerado pelo SUMO. **Não inclui ainda pedestres nem câmera real**: o RPA recebe os veículos da simulação e possui testes de regras de travessia por dados fictícios. Qualquer demonstração deve deixar essa diferença explícita.

## RPA conectado ao SUMO

Instale `traci` em um ambiente Python virtual (`pip install traci`) e execute, na raiz do projeto:

```bash
python -m src.sumo_bridge --mode adaptive --gui
```

Para referência de tempo fixo:

```bash
python -m src.sumo_bridge --mode fixed
```

Cada execução cria arquivos separados em `data/runs/`, incluindo `.json` com métricas e `.jsonl` de telemetria, e registra as recomendações no banco de dados. A variante adaptativa ajusta **somente a duração do verde da fase atual**, sem pular amarelo ou trocar diretamente de fase. A ordem de fases permanece controlada pelo SUMO. Isso é uma estratégia experimental de baixo risco para o MVP, não uma política semafórica homologada.

## Versão 2.0: pedestres e tempos por viagem (experimental)

Primeiro, gere uma rede **separada da versão anterior** para preservar seu teste funcional:

```powershell
netconvert --node-files sumo/cross.nod.xml --edge-files sumo/cross.edg.xml --output-file sumo/cross_pedestrians.net.xml --tls.default-type static --sidewalks.guess true --sidewalks.guess.max-speed 20 --crossings.guess true
```

Em seguida, valide o cenário antes do RPA:

```powershell
sumo-gui -c sumo/cross_pedestrians.sumocfg --delay 100
```

Se aparecer erro de rota de pedestre, não continue com a integração: envie a saída completa do terminal para revisão das conexões de calçadas. Quando o cenário abrir e os pedestres se movimentarem:

```powershell
.\.venv\Scripts\python.exe -m src.sumo_bridge --mode fixed --pedestrians
.\.venv\Scripts\python.exe -m src.sumo_bridge --mode adaptive --pedestrians --gui
```

O programa registra `pedestrian_crossing_samples`, `pedestrian_hold_steps` e gera `*.tripinfo.xml` com registros de viagem. As métricas `average_vehicle_duration_seconds` e `average_vehicle_waiting_seconds` usam **somente viagens concluídas**, então sempre devem ser interpretadas junto aos totais de viagens concluídas e não concluídas.

**Correção do adaptativo com calçadas:** a versão atual consulta os veículos pelo identificador da **via** (`traci.edge`), não pelo índice fixo `_0` da faixa. Ao gerar calçadas, a faixa `_0` pode ser exclusiva de pedestres e os veículos passam a ocupar `_1`. O código também busca as conexões semafóricas sem presumir o índice da faixa. O teste `tests/test_sumo_bridge.py` cobre esse caso.

**Limite de segurança:** a extensão especial de travessia só é tentada quando uma travessia ocupada possuir verde no programa semafórico já gerado pelo SUMO. O adaptador pode acrescentar até 10 segundos por fase ao verde corrente, sem alterar o estado de nenhum sinal, abrir conflito ou pular o amarelo. É necessário validar visualmente que o programa gerado é seguro; a versão é acadêmica e não pode controlar infraestrutura real. Os novos trajetos começam perto do cruzamento para avaliar a travessia em vez de uma caminhada de 500 metros.
