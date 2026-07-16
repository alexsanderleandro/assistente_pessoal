# Monitor de Páginas — Agente de Monitoramento de Conteúdo

Agente automatizado que monitora páginas web governamentais brasileiras, detectando conteúdo novo e exibindo-o em um dashboard em tempo real com notificações via WebSocket.

**Consulte [PRD.md](PRD.md) para especificações completas e [CLAUDE.md](CLAUDE.md) para convenções de desenvolvimento.**

---

## Início Rápido

### 1. Instalar Dependências

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### 2. Ativar o Servidor

```bash
# No diretório backend/ (com venv ativo)
python -m uvicorn main:app --port 8000
```

Ou via Claude Code:

```bash
claude code --launch backend
```

### 3. Acessar o Dashboard

Abra no navegador:

```
http://localhost:8000
```

---

## Rodando como Serviço do Windows (sem deixar terminal aberto)

Para que o dashboard e o agendador (ciclos a cada 2h) continuem rodando mesmo
sem terminal aberto, sem usuário logado e com reinício automático em caso de
falha, o app pode ser registrado como Serviço do Windows via
[NSSM](https://nssm.cc/) (já instalado neste ambiente).

### Instalar o serviço

1. Garanta que o venv já existe e as dependências foram instaladas (seção
   "Instalar Dependências" acima).
2. Abra o PowerShell **como Administrador** e rode:

```powershell
cd backend
.\service_install.ps1
```

Isso cria o serviço `MonitorPaginasGov`, configurado para:
- Iniciar automaticamente no boot do Windows
- Reiniciar sozinho se o processo cair
- Gravar logs (incluindo saída do Uvicorn/APScheduler) em `backend/data/service.log`

### Gerenciar o serviço

```powershell
nssm start MonitorPaginasGov
nssm stop MonitorPaginasGov
nssm restart MonitorPaginasGov
```

Ou abra `services.msc` e procure por "Monitor de paginas GOV".

### Navegador do Playwright (cache compartilhado)

O serviço roda como `NT AUTHORITY\SYSTEM`, cujo `%LOCALAPPDATA%` é isolado do
perfil do usuário interativo. Por isso o `service_install.ps1` configura a
variável `PLAYWRIGHT_BROWSERS_PATH=C:\ProgramData\ms-playwright` no serviço, e
os navegadores devem ser instalados **nesse mesmo caminho compartilhado**, não
no perfil do usuário:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = "C:\ProgramData\ms-playwright"
backend\venv\Scripts\python.exe -m playwright install chromium
```

Se isso não for feito, o serviço falha para **todas** as páginas com o erro
`BrowserType.launch: Executable doesn't exist...`.

### Atualizar o código

Sempre que o código do backend for alterado, pare e reinicie o serviço para
que as mudanças tenham efeito:

```powershell
nssm restart MonitorPaginasGov
```

### Remover o serviço

```powershell
cd backend
.\service_uninstall.ps1
```

---

## Usando o Dashboard

### Adicionar Página para Monitorar

1. Preencha os campos:
   - **URL da página**: `https://www.gov.br/...`
   - **Nome amigável**: ex. `ECD - SPED`
2. Clique em **Adicionar**
3. A página aparece na lista e monitoramento começa no próximo ciclo (a cada 2h)

### Visualizar Mudanças

- Cada página monitorada mostra histórico de mudanças (últimos 7 dias)
- Conteúdo novo aparece em verde com contexto
- Clique em **Expandir contexto** para ler tudo
- Mudanças mais recentes aparecem primeiro

### Remover Página

- Clique em **Remover** ao lado do nome da página
- Confirme a remoção
- Monitoramento para imediatamente

### Notificações Popup

Quando um ciclo de monitoramento detecta conteúdo novo:
- Popup aparece no canto inferior direito
- Mostra: "Nova atualização em [Nome Amigável]"
- Desaparece automaticamente após 5 segundos
- Clique no popup para rolar até a página no dashboard

---

## Arquitetura

```
backend/
├── main.py                  # FastAPI app (rotas, WebSocket)
├── database.py              # Conexão SQLite
├── models.py                # ORM (MonitoredPage, Change)
├── schemas.py               # Pydantic (API contracts)
├── capture.py               # Motor de captura (Playwright)
├── diffing.py               # Detecção de diffs
├── scheduler.py             # APScheduler (ciclos + limpeza)
├── notifications.py         # WebSocket broadcast
├── templates/               # HTML/HTMX/Alpine
├── static/                  # JS (HTMX, Alpine.js)
├── data/
│   └── monitor.db           # SQLite (não versionar)
├── venv/                    # Ambiente virtual (não versionar)
└── requirements.txt         # Dependências
```

---

## Ciclo de Monitoramento

### O que Acontece a Cada 2 Horas

1. **Captura**: renderiza cada página (JavaScript habilitado)
2. **Comparação**: compara com snapshot anterior
3. **Detecção**: identifica linhas novas (ignorando espaçamento)
4. **Persistência**: salva mudanças no banco + notifica via WebSocket
5. **Tratamento de Erros**: página inacessível → mensagem amigável no dashboard

### Horários

- **Dias**: segundas a sextas (dias úteis)
- **Horas**: 00h01, 02h01, 04h01, ..., 22h01 (a cada 2h)
- **Limpeza**: 00h05 todo dia (remove mudanças com +7 dias)

---

## Rotas da API

### REST (JSON)

```bash
# Listar páginas
GET /api/monitored-pages

# Adicionar página
POST /api/monitored-pages
Content-Type: application/json
{"url": "https://...", "nome_amigavel": "..."}

# Remover página
DELETE /api/monitored-pages/{id}
```

### Dashboard (HTML)

```bash
GET /       # Dashboard visual
POST /paginas         # Adicionar (via HTMX)
DELETE /paginas/{id}  # Remover (via HTMX)
```

### WebSocket

```bash
WS /ws/notifications  # Conectar para receber notificações
```

---

## Dados no Banco

### Tabela `monitored_pages`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER | PK |
| url | STRING | URL da página |
| nome_amigavel | STRING | Nome exibido no dashboard |
| criado_em | DATETIME | Timestamp de criação |
| ultimo_conteudo | TEXT | Snapshot anterior (para diff) |
| ultima_verificacao | DATETIME | Última captura |
| ultimo_erro | TEXT | Erro da última tentativa (se houver) |

### Tabela `changes`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER | PK |
| page_id | INTEGER | FK → monitored_pages |
| conteudo_novo | TEXT | Texto adicionado |
| contexto | TEXT | Linhas antes/depois |
| detectado_em | DATETIME | Quando foi detectado |

---

## Troubleshooting

### Servidor não sobe

```bash
# Verificar se a porta 8000 está em uso
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # macOS/Linux

# Mudar porta
python -m uvicorn main:app --port 8001
```

### Playwright não consegue abrir páginas

```bash
# Reinstalar navegador (uso manual, fora do serviço)
python -m playwright install chromium
```

Se o erro (`BrowserType.launch: Executable doesn't exist...`) acontecer **só
quando rodando como serviço do Windows**, veja a seção
"Navegador do Playwright (cache compartilhado)" acima — o serviço roda como
SYSTEM e precisa dos navegadores instalados em
`PLAYWRIGHT_BROWSERS_PATH=C:\ProgramData\ms-playwright`, não no perfil do
usuário.

### Erro de SSL/certificado corporativo

```bash
# Usar --trusted-host para pip (rede corporativa)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Página adicionada mas não aparece mudança

- Aguarde o próximo ciclo (máximo 2h)
- Verifique se há erro no dashboard (ícone ⚠️)
- Confirme que a URL é pública (sem autenticação)

---

## Produção (Checklist)

- [ ] Testar com 9 URLs reais por pelo menos 1 semana
- [ ] Verificar se agendador dispara sozinho nos horários certos
- [ ] Considerar rodar em container (Docker)
- [ ] Usar banco Postgres em vez de SQLite (para acesso concorrente)
- [ ] Configurar reverse proxy (nginx, Caddy)
- [ ] Habilitar HTTPS
- [ ] Remover rota `/health` ou protegê-la (é pública agora)
- [ ] Considerar autenticação do dashboard (fora do escopo v1.0)

---

## Desenvolvimento

### Rodar testes manualmente

```bash
cd backend
# Listar páginas cadastradas
curl http://localhost:8000/api/monitored-pages

# Adicionar página
curl -X POST http://localhost:8000/api/monitored-pages \
  -H "Content-Type: application/json" \
  -d '{"url": "https://...", "nome_amigavel": "Test"}'

# Testar WebSocket (requer websockets CLI ou Python)
python -c "
import asyncio, websockets, json
async def test():
    async with websockets.connect('ws://127.0.0.1:8000/ws/notifications') as ws:
        msg = await ws.recv()
        print(json.loads(msg))
asyncio.run(test())
"
```

### Editar código

Veja [CLAUDE.md](CLAUDE.md) para convenções:
- Comentários em português (explicam o "por quê")
- Nomes em inglês, mas docstrings em português
- Sem biblioteca externa sem consultar antes

---

## Suporte

Erros ou dúvidas? Verifique:

1. [PRD.md](PRD.md) — especificação funcional
2. [CLAUDE.md](CLAUDE.md) — guia técnico
3. Logs do servidor: `python -m uvicorn main:app --port 8000` (no terminal)
4. Console do navegador: F12 → Abas "Console" e "Network"

---

**Versão**: 1.0 | **Última atualização**: julho 2026
