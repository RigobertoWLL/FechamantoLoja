# 🏪 Sistema de Fechamento de Lojas - Refatorado

Sistema Python moderno e robusto para gerenciar fechamento de lojas em uma planilha Google Sheets com funcionalidades automatizadas, tratamento robusto de tipos e arquitetura melhorada.

## ✨ Novidades da Refatoração

### 🔧 Correções Críticas Implementadas
- **✅ Erro de comparação string/int RESOLVIDO:** Sistema agora trata automaticamente comparações entre tipos diferentes
- **✅ Convenção CamelCase:** Todos os arquivos seguem a convenção solicitada
- **✅ Configuração JSON:** Sistema centralizado de configurações
- **✅ Tratamento robusto de tipos:** Funções especializadas para normalização de dados
- **✅ Logging avançado:** Sistema modular com decorators e níveis configuráveis

### 🏗️ Nova Estrutura Organizada
```
/
├── modelos/                   # Modelos de dados
│   ├── __init__.py
│   └── resultado_fechamento.py
├── servicos/                  # Serviços de negócio
│   ├── __init__.py
│   ├── gerenciador_loja.py
│   ├── gerenciador_planilhas_google.py
│   └── gerenciador_firebird.py
├── configuracao/              # Configurações
│   ├── __init__.py
│   └── gerenciador_configuracao.py
├── utilitarios/               # Utilitários
│   ├── __init__.py
│   ├── logger.py
│   └── utilitarios.py
├── controladores/             # Controladores da aplicação
│   ├── __init__.py
│   ├── principal.py
│   └── menu_cmd.py
├── main.py                    # Ponto de entrada principal
├── menu.py                    # Menu interativo
├── config.json                # Configurações centralizadas
├── credentials.json           # Credenciais Google Sheets
└── requirements.txt           # Dependências Python
```

## 📋 Funcionalidades

### ABA "Gerenciador"
1. 🔍 Procura número da loja na coluna C (a partir da linha 6)
2. 📝 Na mesma linha encontrada:
   - Define status como "Fechada" na coluna D
   - Apaga conteúdo das colunas A e B

### ABA "Lojas Fechadas"
1. 📍 Encontra a próxima linha vazia
2. ➕ Adiciona as seguintes informações:
   - Coluna B: Nome da loja
   - Coluna C: Número da loja
   - Coluna D: "NÃO"
   - Coluna E: Data de fechamento
   - Coluna F: Observação

## 🚀 Instalação e Configuração

### 1. Dependências

```bash
pip install -r requirements.txt
```

### 2. Configuração das Credenciais

Edite o arquivo `credentials.json` com suas credenciais reais do Google Sheets:

```json
{
  "type": "service_account",
  "project_id": "seu-project-id",
  "private_key_id": "sua-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nSUA_PRIVATE_KEY_AQUI\n-----END PRIVATE KEY-----\n",
  "client_email": "seu-service-account@seu-project-id.iam.gserviceaccount.com",
  "client_id": "seu-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/seu-service-account%40seu-project-id.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```

### 3. Verificar Configuração

O arquivo `config.json` já está configurado com:
- **ID da planilha:** `17Chzn5vkJbouCatul_5iZJl-PW4_BHufMEWTg_-ZOY8`
- **Configurações otimizadas** para as abas "Gerenciador" e "Lojas Fechadas"
- **Mapeamento de colunas** configurável

## 💻 Uso

### Fechar uma loja

```bash
python main.py 123
```

### Fechar loja com observação personalizada

```bash
python main.py 456 "Fechamento por reforma"
```

### Verificar se loja existe (sem fechar)

```bash
python main.py --verificar 456  # Agora funciona sem erro!
```

### Fechar múltiplas lojas

```bash
python main.py --multiplas "123,456,789"
```

### Fechar múltiplas lojas com observação

```bash
python main.py --multiplas "100,200,300" "Fechamento em lote"
```

### Modo debug

```bash
python main.py --debug --verificar 456
```

### Ajuda

```bash
python main.py --help
```

### Menu Interativo

Para uma interface mais amigável, use o menu interativo:

```bash
python menu.py
```

O menu oferece as seguintes opções:
- 🏪 Fechar loja (Google Sheets + formatação)
- 🔥 Atualizar status da loja no Firebird
- 📊 Verificar loja (Google Sheets)
- 🔍 Verificar status loja (Firebird)
- 📋 Listar lojas por status
- 🔧 Verificar estrutura da tabela
- 📊 Estatísticas da tabela
- 🔌 Testar conexões

## 🔧 Melhorias Técnicas Implementadas

### 🛡️ Tratamento Robusto de Tipos

**Problema Original:**
```
'<' not supported between instances of 'str' and 'int'
```

**Solução Implementada:**
```python
# Novas funções para tratamento seguro de tipos
def normalizar_tipo_numero_loja(valor: Any) -> str
def comparar_numeros_loja(numero1: Any, numero2: Any) -> bool  
def safe_int(valor: Any, padrao: int = 0) -> int
```

### 📊 Sistema de Logging Avançado

```python
# Decorators para logging automático
@log_operacao
def fechar_loja(self, numero_loja: str) -> ResultadoFechamento:
    # Sistema registra automaticamente início/fim/erros
```

### ⚙️ Configuração Centralizada

```json
// config.json - Configurações centralizadas
{
  "planilha_id": "17Chzn5vkJbouCatul_5iZJl-PW4_BHufMEWTg_-ZOY8",
  "configuracoes_gerenciador": {
    "linha_inicio": 6  // Garantido como inteiro
  },
  "valores_padrao": {
    "status_fechada": "Fechada"
  }
}
```

### 🧪 Validação Automática

```python
# Validação automática de configurações
def validar_configuracao(self) -> bool:
    # Verifica tipos, arquivos, e configurações
```

## 📊 Formato da Planilha

### Aba "Gerenciador"
| A | B | C (Número Loja) | D (Status) | ... |
|---|---|-----------------|------------|-----|
| ... | ... | ... | ... | ... |
| Dados | Dados | 123 | Ativa | ... |
| Dados | Dados | 456 | Ativa | ... |

### Aba "Lojas Fechadas"
| A | B (Nome) | C (Número) | D (Status) | E (Data) | F (Observação) |
|---|----------|------------|------------|----------|----------------|
| ... | Loja A | 123 | NÃO | 15/01/2024 | Fechamento... |

## 🧪 Testes de Validação

### Teste do Erro Específico (Loja 456)
```bash
# Teste específico para o erro corrigido
python main.py --verificar 456  # Agora funciona!
```

### Teste de Tipos Mistos
```bash
# Sistema agora trata automaticamente:
# - Números como int: 123
# - Números como string: "456" 
# - Números como float: 789.0
# - Códigos alfanuméricos: "ABC123"
```

## 🛠️ Desenvolvimento

### Arquitetura Modular Organizada

- **modelos**: Classes de dados e entidades (`ResultadoFechamento`)
- **servicos**: Lógica de negócio (`GerenciadorLoja`, `GerenciadorPlanilhasGoogle`, `GerenciadorFirebird`)
- **configuracao**: Gerenciamento de configurações (`GerenciadorConfiguracao`)
- **utilitarios**: Funções auxiliares e logging (`logger`, `utilitarios`)
- **controladores**: Interface da aplicação (`principal`, `menu_cmd`)

### Padrões Implementados

- **Mixins**: `MixinLogger` para logging consistente
- **Decorators**: `@log_operacao` para logging automático  
- **Dataclasses**: `ResultadoFechamento` para resultados estruturados
- **Type Hints**: Tipagem completa para melhor manutenibilidade

## 🐛 Solução de Problemas

### ✅ Erro de comparação string/int (RESOLVIDO)
```
❌ Antes: '<' not supported between instances of 'str' and 'int'
✅ Agora: Sistema trata automaticamente todos os tipos
```

### Erro de autenticação
```
Erro de autenticação: Invalid credentials
```
**Solução:** Edite `credentials.json` com suas credenciais reais.

### Planilha não encontrada
```
Planilha não encontrada com ID: ...
```
**Solução:** Verifique se a planilha foi compartilhada com o service account.

### Configuração inválida
```
❌ Configuração inválida!
```
**Solução:** Sistema agora valida automaticamente e mostra o que corrigir.

## 📈 Benefícios da Refatoração

### 🔒 Robustez
- Tratamento automático de tipos mistos
- Validação completa de configurações
- Recuperação automática de erros

### 🚀 Performance
- Operações em lote otimizadas
- Cache de configurações
- Logging eficiente

### 🧹 Manutenibilidade
- Código modular e bem documentado
- Convenção CamelCase consistente
- Type hints completas

### 🔧 Flexibilidade
- Configurações JSON editáveis
- Sistema de logging configurável
- Arquitetura extensível

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

Para dúvidas ou problemas, abra uma issue no repositório GitHub.
