# Vagas Hub — Monitor de Vagas

Dashboard web hospedado no GitHub Pages, atualizado automaticamente todo dia via GitHub Actions.

**Acesse em:** `https://SEU_USUARIO.github.io/vagas-hub`

---

## Configuração (10 minutos)

### 1. Criar o repositório no GitHub

```bash
# Clone ou faça upload desta pasta para um novo repositório público chamado "vagas-hub"
git init
git add .
git commit -m "setup inicial"
git remote add origin https://github.com/SEU_USUARIO/vagas-hub.git
git push -u origin main
```

### 2. Ativar GitHub Pages

1. Vá em **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / **/ (root)**
4. Salve — o site ficará disponível em `https://SEU_USUARIO.github.io/vagas-hub`

### 3. Rodar a busca pela primeira vez

1. Vá em **Actions → Busca de Vagas Diária**
2. Clique em **Run workflow**
3. Aguarde ~5 minutos
4. O `vagas.json` será atualizado e o dashboard exibirá as vagas

A partir daí, roda automaticamente todo dia às 08h (Brasília) sem precisar fazer nada.

---

## Estrutura do projeto

```
vagas-hub/
├── index.html                          ← dashboard web (GitHub Pages)
├── vagas.json                          ← dados das vagas (atualizado pelo bot)
├── buscar_vagas.py                     ← script de scraping
└── .github/
    └── workflows/
        └── buscar_vagas.yml            ← agendamento GitHub Actions
```

---

## Usar o dashboard

| Ação | Como fazer |
|------|-----------|
| Marcar como verificada | Botão ✓ na linha ou no modal |
| Marcar como enviada | Botão ✈ na linha ou no modal |
| Rejeitar vaga | Botão ✗ na linha ou no modal |
| Ver detalhes | Clicar em qualquer linha |
| Filtrar por área | Pills de área no topo |
| Filtrar por prioridade | Pills 🔴🟡🟢 |
| Buscar | Campo de texto |

Os status (verificado/enviado/rejeitado) são **salvos no seu browser** via localStorage — persistem entre sessões sem precisar de servidor.

---

## Personalização

Edite `buscar_vagas.py` e altere:

- `TERMOS_BUSCA` — adicione ou remova termos por área
- `PERFIL_KEYWORDS` — palavras que determinam a prioridade das vagas
- `MAX_POR_TERMO` — quantas vagas buscar por termo (padrão: 10)
- `DELAY` — tempo entre requisições (não reduza abaixo de 1.5s)

Para alterar o horário da busca, edite o cron em `.github/workflows/buscar_vagas.yml`:

```yaml
- cron: '0 11 * * *'   # UTC — 08h Brasília
```

---

## Custo

**Zero.** GitHub Actions oferece 2.000 minutos/mês gratuitos para repositórios públicos.
Cada execução leva ~3-5 minutos → ~150 minutos/mês.
