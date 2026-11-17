# Publicação do Sinal Cidadão no GitHub

## Antes de publicar

1. Abra a pasta `C:\Users\anny.dias\Documents\SinalCidadao` no PowerShell.
2. Verifique se o projeto executa os 38 testes: `\.venv\Scripts\python.exe -m unittest discover -s tests -v` (no PowerShell, acrescente `.` antes da barra inicial: `.\.venv\Scripts\python.exe ...`).
3. Confira se não há senhas, tokens, nomes de pessoas nas amostras ou outros dados privados.
4. Inclua nomes e RMs dos integrantes no relatório e atualize o PDF antes da entrega.

## Publicar a partir da pasta do projeto

Crie um repositório **vazio**, preferencialmente chamado `sinal-cidadao`, no site do GitHub. Não marque as opções de criar README ou `.gitignore`, pois eles já existem neste projeto.

Execute os comandos abaixo, um de cada vez, no PowerShell:

```powershell
git init
git add .
git status
git commit -m "Entrega Sinal Cidadao - simulacao SUMO e dashboard"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/sinal-cidadao.git
git push -u origin main
```

Troque `SEU_USUARIO` pelo nome correto do perfil. Caso o projeto já tenha Git configurado, verifique primeiro com `git status` e `git remote -v` e não repita a inicialização nem substitua o remoto existente sem conferir.

O arquivo `.gitignore` exclui ambiente virtual, banco local, logs e histórico de simulações. **Confira a listagem de `git status` antes do commit.** O PDF pode ser versionado; o ZIP de distribuição é ignorado para evitar arquivos duplicados.

## Depois

- Confira se o GitHub mostra `README.md`, `src/`, `sumo/`, `tests/`, `docs/` e o PDF.
- Copie o link público do repositório para o relatório e para a descrição do vídeo.
- Grave a demonstração seguindo `docs/roteiro-video.md`.

Este guia prepara a publicação; não cria a conta nem publica o repositório automaticamente.
