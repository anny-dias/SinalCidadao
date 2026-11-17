# Roteiro de demonstração - Sinal Cidadão (até 3 minutos)

**Preparação:** abrir `http://127.0.0.1:8765`, manter servidor em execução e ter histórico com três cenários. Gravar previamente trechos curtos do SUMO-GUI: cada simulação completa leva mais tempo que o vídeo. Não fingir que um trecho gravado está ocorrendo em tempo real; identificar cortes quando necessário. Separar uma captura dos testes com `38 tests / OK`.

| Tempo | Cena | Narração sugerida |
| --- | --- | --- |
| 00:00-00:20 | Dashboard, título e proposta | "O Sinal Cidadão é um protótipo acadêmico que estuda a adaptação de semáforos com atenção à travessia de pedestres." |
| 00:20-00:40 | Mostrar cruzamento SUMO e veículos/pedestres | "Usamos SUMO e TraCI para simular tráfego e coletar contagens agregadas. Não conectamos a semáforos físicos." |
| 00:40-01:05 | Explicar três opções do Laboratório | "O painel inicia o modo fixo, o adaptativo e o adaptativo com prioridade. O controlador respeita a sequência e os sinais definidos pelo SUMO." |
| 01:05-01:30 | Mostrar gravação curta do SUMO-GUI em movimento | "O RPA valida dados, evita duplicatas, registra decisões e audita pedidos de travessia; a prioridade v4 reserva verde autorizado sem modificar fases amarelas." |
| 01:30-02:05 | Dashboard: cards e barras | "Na demanda alta, a espera média veicular caiu de 27,24 para 15,27 segundos, e a espera observada antes da faixa de 0,99 para 0,91 segundo. São reduções de 43,94% e 8,08% no nosso cenário." |
| 02:05-02:30 | Laboratório: abrir detalhes dos testes | "Todos os 38 testes automatizados foram aprovados. Os resultados e eventos de segurança são armazenados para auditoria." |
| 02:30-02:50 | Mostrar PDD, BPMN e arquivos JSON | "Documentamos regras, exceções, fallback, integração por API e limitações do protótipo." |
| 02:50-03:00 | Encerrar com título e links GitHub | "Sinal Cidadão: mobilidade inteligente, pessoas em primeiro lugar. Código e documentação disponíveis no repositório." |

## Cuidados para avaliação

- Não iniciar **Comparar 3 cenários** durante a gravação integral: leva muito mais de 3 minutos. Mostrar seu resultado já concluído ou usar cortes identificados.
- Não alegar redução comprovada de acidentes, emissões ou segurança física. Os indicadores são **de simulação**, com uma semente e duração fixa.
- Mencionar a troca de desempenho: o modo sem prioridade concluiu 328 viagens veiculares; o prioritário, 310.
- Gravar em 1080p se disponível, ampliar textos do navegador, manter notificações pessoais fechadas e garantir que nomes/RMs não sejam esquecidos na entrega.
- Conferir a URL do GitHub, vídeo e documentos antes de enviar.
