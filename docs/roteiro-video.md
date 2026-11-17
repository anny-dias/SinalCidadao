# Roteiro de demonstração - Sinal Cidadão (até 3 minutos)

**Preparação:** abrir `http://127.0.0.1:8765`, manter servidor em execução e ter histórico com três cenários. Gravar previamente trechos curtos do SUMO-GUI: cada simulação completa leva mais tempo que o vídeo. Não fingir que um trecho gravado está ocorrendo em tempo real; identificar cortes quando necessário. Separar uma captura dos testes com `38 tests / OK`.

| Tempo | Cena | Narração sugerida |
| --- | --- | --- |
| 00:00-00:20 | Dashboard, título e proposta | "O Sinal Cidadão é um protótipo acadêmico que estuda a adaptação de semáforos com atenção à travessia de pedestres." |
| 00:20-00:50 | Terminal: execução do lote fictício e log JSONL | "O RPA recebe uma coleção de leituras, aplica regras de decisão e processa em lote. Neste exemplo, quatro foram processadas, uma duplicada e uma inválida auditada." |
| 00:50-01:10 | Terminal: falha intencional de arquivo ausente e log; 38 testes OK | "Se o arquivo estiver ausente, o programa registra ERROR e retorna falha identificável. Os 38 testes automatizados foram aprovados." |
| 01:10-01:35 | Trecho curto do SUMO-GUI em movimento | "No SUMO e TraCI simulamos veículos e pedestres. O controlador adapta fases com restrições e não atua em semáforos reais." |
| 01:35-02:00 | Dashboard: laboratório, controles e resultado dos três cenários | "O dashboard inicia as simulações e consome os resultados estruturados, integrando a automação ao MVP." |
| 02:00-02:35 | Dashboard: cards e comparativo | "Neste cenário simulado, a espera veicular passou de 27,24 para 15,27 segundos e a espera observada na faixa de 0,99 para 0,91. São reduções de 43,94% e 8,08%." |
| 02:35-02:50 | PDF: imagem do BPMN, PDD e lista de evidências | "O processo possui repetição, condições, tratamento de exceções, logs e documentação." |
| 02:50-03:00 | Encerrar com título e links GitHub | "Sinal Cidadão: mobilidade inteligente, pessoas em primeiro lugar. Código e documentação disponíveis no repositório." |

## Cuidados para avaliação

- **Demonstração de falha é obrigatória no vídeo:** use os dois comandos de `docs/EVIDENCIAS.md` e mostre que a falha de arquivo ausente gera log de erro. Não apague nem altere registros para simular sucesso.

- Não iniciar **Comparar 3 cenários** durante a gravação integral: leva muito mais de 3 minutos. Mostrar seu resultado já concluído ou usar cortes identificados.
- Não alegar redução comprovada de acidentes, emissões ou segurança física. Os indicadores são **de simulação**, com uma semente e duração fixa.
- Mencionar a troca de desempenho: o modo sem prioridade concluiu 328 viagens veiculares; o prioritário, 310.
- Gravar em 1080p se disponível, ampliar textos do navegador, manter notificações pessoais fechadas e garantir que nomes/RMs não sejam esquecidos na entrega.
- Conferir a URL do GitHub, vídeo e documentos antes de enviar.
