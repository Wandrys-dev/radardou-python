# RadarDOU SDK Python

SDK oficial para integração com a API do [Radar DOU](https://radar-dou.com) - Sistema de Monitoramento do Diário Oficial da União.

## Requisitos

- Python 3.8+
- API Key válida de assinante do Radar DOU

## Instalação

```bash
pip install radardou
```

## Início Rápido

```python
from radardou import RadarDOU

# Inicialize o cliente com sua API Key
client = RadarDOU(api_key="sua_api_key_aqui")

# Buscar publicações
resultados = client.buscar("licitação")
print(f"Encontrados {resultados['total']} resultados")

# Ao finalizar, encerre a sessão
client.close()
```

### Usando Context Manager

```python
from radardou import RadarDOU

with RadarDOU(api_key="sua_api_key") as client:
    resultados = client.buscar("contrato", orgao="Ministério da Saúde")
    for pub in resultados["resultados"]:
        print(f"- {pub['titulo']}")
```

## Funcionalidades

### Busca de Publicações

```python
# Busca simples
resultados = client.buscar("edital")

# Busca com filtros
resultados = client.buscar(
    termo="pregão eletrônico",
    data_inicio="2024-01-01",
    data_fim="2024-12-31",
    orgao="Ministério da Educação",
    tipo="edital",
    secao=3,
    pagina=1,
    limite=50
)

# Obter publicação específica
publicacao = client.obter_publicacao("abc123")
```

### Gerenciamento de Alertas

```python
# Listar alertas
alertas = client.listar_alertas()

# Criar alerta
alerta = client.criar_alerta(
    nome="Monitorar Licitações Saúde",
    termos=["licitação", "pregão"],
    orgaos=["Ministério da Saúde"],
    email_notificacao=True
)

# Atualizar alerta
client.atualizar_alerta(alerta["id"], nome="Novo Nome")

# Excluir alerta
client.excluir_alerta(alerta["id"])
```

### Informações de Uso

```python
# Ver uso da API
uso = client.obter_uso()
print(f"Requisições hoje: {uso['requisicoes_hoje']}")
print(f"Limite por hora: {uso['limite_hora']}")

# Informações da conta
conta = client.obter_conta()
print(f"Plano: {conta['plano']}")
```

## Controle de Sessão

O SDK implementa controle automático de sessão para garantir que sua API Key seja usada apenas por você. Isso inclui:

- **Fingerprint de dispositivo**: Identifica unicamente seu computador
- **Heartbeat automático**: Mantém sua sessão ativa
- **Detecção de uso compartilhado**: Impede que outros usem sua API Key simultaneamente

### Comportamento de Sessão

Quando você inicializa o cliente, uma sessão é automaticamente criada. Se outro dispositivo tentar usar a mesma API Key, receberá um erro `SessionConflictError`.

```python
from radardou import RadarDOU, SessionConflictError

try:
    client = RadarDOU(api_key="sua_api_key")
except SessionConflictError as e:
    print(f"Erro: {e.message}")
    print(f"IP ativo: {e.active_ip}")
```

## Tratamento de Erros

```python
from radardou import (
    RadarDOU,
    AuthenticationError,
    SessionConflictError,
    RateLimitError,
    APIError
)

try:
    client = RadarDOU(api_key="sua_api_key")
    resultados = client.buscar("teste")

except AuthenticationError as e:
    print(f"Erro de autenticação: {e.message}")
    # API Key inválida ou expirada

except SessionConflictError as e:
    print(f"Conflito de sessão: {e.message}")
    print(f"Outro IP está usando: {e.active_ip}")

except RateLimitError as e:
    print(f"Limite atingido: {e.message}")
    print(f"Limite: {e.limit}")
    print(f"Reset em: {e.reset_at}")

except APIError as e:
    print(f"Erro da API: {e.message}")
    print(f"Status: {e.status_code}")
```

## Limites por Plano

| Plano | Requisições/hora | Usuários Simultâneos |
|-------|------------------|----------------------|
| Profissional | 1.000 | 1 |
| Premium | 5.000 | 3 |
| Enterprise | Ilimitado | Ilimitado |

## Obtenha sua API Key

Para usar este SDK, você precisa de uma API Key válida:

1. Acesse [radar-dou.com](https://radar-dou.com)
2. Crie uma conta ou faça login
3. Assine um plano
4. Gere sua API Key em [Configurações > API Keys](https://radar-dou.com/api-keys)

## Suporte

- 📧 Email: suporte@radar-dou.com
- 📖 Documentação: [radar-dou.com/docs](https://radar-dou.com/docs)
- 🐛 Issues: [GitHub Issues](https://github.com/radar-dou/radardou-python/issues)

## Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.
