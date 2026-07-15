# CLAUDE.md - Guia de Desenvolvimento

## Visão Geral

Agente de monitoramento de páginas web governamentais brasileiras com dashboard público em tempo real. Detecta e exibe conteúdo novo em 9 URLs inicialmente, com histórico de 7 dias.

## Arquitetura em Uma Página

```
┌─────────────────────────────────────┐
│      Agendador (Cron a cada 2h)     │
├─────────────────────────────────────┤
│  Monitorador (Puppeteer/Playwright) │
│  • Renderiza JS                     │
│  • Extrai conteúdo                  │
│  • Detecta mudanças                 │
├─────────────────────────────────────┤
│   Banco de Dados (URLs + histórico) │
│   • Retenção: 7 dias                │
│   • Limpeza automática              │
├─────────────────────────────────────┤
│    API / Backend (rotas do agente)  │
├─────────────────────────────────────┤
│  Dashboard Frontend (público)       │
│  • Visualização de mudanças         │
│  • Gerenciamento de URLs            │
│  • Notificações popup               │
└─────────────────────────────────────┘
```

## Escopo do Projeto

Veja @PRD.md para detalhes completos. **Resumo**:
- Monitorar 9 URLs, escalável
- Renderizar JavaScript obrigatoriamente
- Frequência: 2h, dias úteis, 00h01–23h59
- Histórico: 7 dias
- Sem autenticação no dashboard
- Sem notificações externas (email/Slack)

## Regras de Comportamento

1. **Planejar primeiro**: Toda mudança não-trivial (multi-arquivo ou que altere comportamento) precisa de plano aprovado antes de executar.
2. **Bibliotecas**: Não adicione dependências externas, CDNs ou pacotes sem consultar antes.
3. **Comentários**: Em português. Explicam **por quê** do código, não o **quê**.
4. **Arquivos novos**: Justifique antes de criar novos arquivos além dos 3 principais (backend, frontend, agendador).
5. **Conflitos PRD**: Se pedido conflitar com @PRD.md, aviso antes de implementar.

## Convenções de Código

- **Nomenclatura**: camelCase para variáveis/funções, PascalCase para classes
- **Banco de dados**: schema com snake_case
- **Rotas API**: kebab-case (`/api/monitored-urls`)
- **Componentes frontend**: PascalCase (`.tsx`)
- **Máximo 100 caracteres por linha**

## Como Rodar

```bash
# Instalar dependências
npm install

# Variáveis de ambiente (.env)
DATABASE_URL=postgresql://...
MONITOR_INTERVAL=2h
RENDER_TIMEOUT=30000

# Rodas o agendador + backend
npm run dev

# Dashboard estará em http://localhost:3000
```

