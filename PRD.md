# Product Requirements Document (PRD)
## Agente de Monitoramento de Páginas Web

**Data**: 13 de julho de 2026  
**Versão**: 1.0  
**Status**: Aprovado

---

## 1. Visão Geral

Um agente automatizado que monitora páginas web governamentais brasileiras, detectando e exibindo conteúdo novo ou modificado através de um dashboard público. O sistema verifica as páginas periodicamente, renderiza JavaScript para capturar o conteúdo completo, e armazena histórico de mudanças por 7 dias.

---

## 2. Objetivos

- Monitorar automaticamente conteúdo incluído diariamente em páginas governamentais
- Detectar e exibir mudanças de forma clara e contextualizada
- Fornecer interface de gerenciamento simples para adicionar/remover URLs
- Alertar sobre alterações recentes sem replicar notificações

---

## 3. Escopo

### URLs Monitoradas
- Inicialmente: **9 URLs** de páginas governamentais brasileiras
  - Exemplos: `https://www.gov.br/sped/pt-br/assuntos/escrituracoes-digitais/ecd`
  - `https://www.nfe.fazenda.gov.br/portal/principal.aspx`
- Escalável para mais URLs no futuro

### Tipo de Conteúdo
- Conteúdo textual/HTML que é **adicionado diariamente**
- Páginas sem autenticação obrigatória
- Páginas que utilizam **JavaScript para renderização** (necessário executar JS)

### Frequência de Monitoramento
- **A cada 2 horas**
- **Apenas dias úteis** (segunda a sexta)
- **Período**: 00h01 às 23h59

### Retenção de Dados
- Histórico de mudanças: **últimos 7 dias**
- Após 7 dias, dados são removidos automaticamente

---

## 4. Funcionalidades Principais

### 4.1 Dashboard de Visualização
- **Organização**: Agrupado por página monitorada (usando nome amigável)
- **Exibição**: Cada página mostra seu histórico de mudanças em ordem cronológica
- **Acesso**: Público (sem autenticação necessária)

### 4.2 Gerenciamento de URLs
- **Interface**: Formulário no dashboard
- **Campos**:
  - URL completa da página a monitorar
  - Nome amigável (label que será exibido no dashboard)
- **Ações**:
  - Adicionar nova URL
  - Remover URL existente
- **Ativação**: O monitoramento inicia no **próximo ciclo agendado** (a cada 2 horas)

### 4.3 Visualização de Mudanças
- **Apresentação**:
  - Conteúdo novo + contexto (linhas anteriores e posteriores)
  - Destaque visual do conteúdo novo
  - Opção de **expandir para ler tudo** (conteúdo completo)
- **Informações**:
  - Data e hora da detecção da mudança
  - Nome amigável da página
  - Diferença clara entre o que é novo e contexto

### 4.4 Notificações Popup
- **Trigger**: Quando uma atualização é detectada em qualquer página monitorada
- **Apresentação**:
  - Popup/toast notification no canto inferior direito do dashboard
  - Destaque visual chamativo (cor, ícone, som opcional)
  - Mensagem clara: "Nova atualização em [NOME AMIGÁVEL]"
- **Comportamento**:
  - Popup desaparece automaticamente após 5 segundos
  - Usuário pode clicar no popup para ir direto para a página monitorada
  - Popup não bloqueia interação com o dashboard

### 4.5 Tratamento de Erros
- **Quando a página não conseguir ser acessada**:
  - Exibir mensagem amigável de erro no dashboard
  - Permite que o usuário investigue manualmente a página original
  - Exemplos: "Não foi possível acessar a página no momento. Verifique se o servidor está disponível."

---

## 5. Comportamentos de UX

### 5.1 Adição de URL
1. Usuário acessa o dashboard
2. Clica em "Adicionar Nova URL"
3. Preenche formulário com:
   - URL completa
   - Nome amigável
4. Salva
5. A URL aparece no dashboard
6. Monitoramento inicia no próximo ciclo (máximo 2 horas)

### 5.2 Visualização de Mudanças
1. Usuário vê a página monitorada com seu nome amigável
2. Histórico de mudanças aparece em ordem cronológica (mais recente primeiro)
3. Cada mudança mostra:
   - Data/hora
   - Conteúdo novo (destacado)
   - Contexto
   - Link "Expandir" para ver conteúdo completo
4. Clicando em "Expandir", mostra toda a adição

### 5.3 Remoção de URL
1. Usuário localiza a URL no dashboard
2. Clica em "Remover"
3. Confirma exclusão (ou não)
4. A página é removida da lista de monitoramento

### 5.4 Notificação de Atualização
1. Sistema detecta mudança em uma página monitorada durante ciclo de verificação
2. Popup aparece no canto inferior direito da tela:
   - Título: "Nova atualização em [NOME AMIGÁVEL]"
   - Ícone visual indicando atualização
   - Timestamp da detecção
3. Popup fica visível por 5 segundos
4. Usuário pode:
   - Deixar desaparecer automaticamente
   - Clicar no popup para ir direto para a página no dashboard
   - Continuar usando o dashboard normalmente

### 5.5 Página Inacessível
1. Sistema tenta acessar a página
2. Retorna erro (404, 500, timeout, etc.)
3. Dashboard exibe:
   - Nome amigável da página
   - Mensagem amigável: "Não foi possível acessar..."
   - Timestamp da tentativa
4. Usuário vê o alerta e pode investigar manualmente

---

## 6. Requisitos Técnicos

### 6.1 Renderização de Conteúdo
- **Execução de JavaScript**: Obrigatória
  - Usar ferramenta como Puppeteer, Playwright ou Selenium
  - Garante que conteúdo dinâmico seja capturado
  - Simula navegador real

### 6.2 Detecção de Mudanças
- Comparar conteúdo do ciclo anterior com o atual
- Identificar texto/HTML adicionado
- Extrair contexto (linhas antes e depois)

### 6.3 Armazenamento
- Banco de dados com histórico de:
  - URLs monitoradas (lista e nomes amigáveis)
  - Mudanças detectadas (timestamp, conteúdo antigo, novo, contexto)
  - Limpeza automática após 7 dias

### 6.4 Agendamento
- Job/cron que executa a cada 2 horas
- Somente em dias úteis
- Horário: 00h01 às 23h59

---

## 7. Edge Cases

### 7.1 Página com Conteúdo Dinâmico Pesado
- Sistema executa JavaScript e aguarda renderização
- Se timeout, exibe mensagem de erro

### 7.2 Redirecionamentos
- Sistema segue redirecionamentos HTTP (3xx) automaticamente
- Monitora o conteúdo final da página

### 7.3 Mudança Mínima ou Formatação
- Sistema detecta qualquer alteração no conteúdo
- Mudanças apenas de espaçamento/formatação são ignoradas (conteúdo igual)

### 7.4 URL Removida Durante Monitoramento
- Se URL for removida do dashboard, monitoramento cessa
- Dados históricos dos últimos 7 dias são preservados até serem descartados

### 7.5 Falha no Ciclo de Monitoramento
- Se um ciclo falhar, o próximo ciclo tenta novamente
- Não interrompe ciclos futuros

---

## 8. Fora do Escopo

❌ **Notificações externas**: Email, SMS, Slack, Discord, Telegram  
❌ **Autenticação/Login**: Dashboard sem proteção por senha  
❌ **Análise de conteúdo**: Resumos automáticos, IA de classificação  
❌ **Busca/filtros avançados**: Apenas visualização cronológica  
❌ **Versionamento de conteúdo**: Apenas comparação antes/depois  
❌ **Acesso a páginas com autenticação**: Apenas páginas públicas  
❌ **Análise de mudanças de CSS/design**: Apenas conteúdo textual/HTML  

---

## 9. Métricas de Sucesso

- ✅ Agente executa monitoramento a cada 2 horas em dias úteis
- ✅ Conteúdo novo é detectado e exibido no dashboard dentro de 2 horas
- ✅ Popup de notificação aparece imediatamente quando mudança é detectada
- ✅ Popup desaparece automaticamente após 5 segundos
- ✅ Histórico mantém mudanças dos últimos 7 dias
- ✅ Dashboard carrega em menos de 2 segundos
- ✅ Usuário consegue adicionar/remover URL em menos de 30 segundos
- ✅ Erros de acesso são exibidos de forma clara ao usuário
- ✅ Zero perda de dados de mudanças durante 7 dias
- ✅ Popup exibe corretamente o nome amigável da página atualizada

---

## 10. Roadmap Futuro (Não Incluído na v1.0)

- [ ] Notificações por email/Slack para mudanças críticas
- [ ] Filtros por palavras-chave
- [ ] Exportação de relatório de mudanças
- [ ] Autenticação opcional do dashboard
- [ ] Integração com webhooks
- [ ] Análise de tendências de conteúdo

