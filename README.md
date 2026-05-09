# radardou-python

SDK oficial Python para a API do [Radar DOU](https://www.radar-dou.com) — Sistema de Monitoramento do Diário Oficial da União.

## Requisitos

- Python >= 3.8
- API Key válida de assinante do Radar DOU (gere em [www.radar-dou.com/api-keys](https://www.radar-dou.com/api-keys))

## Instalação

```bash
pip install git+https://github.com/Wandrys-dev/radardou-python.git
```

## Início rápido

```python
import os
from radardou import RadarDOU

# Carregue a API key de variável de ambiente — NUNCA hardcode no script
api_key = os.environ["RADAR_API_KEY"]

with RadarDOU(api_key=api_key) as client:
    # IMPORTANTE: pelo menos um filtro é obrigatório
    resultados = client.buscar(date_from="2026-05-01", limit=10)

    print(f"Total no banco: {resultados['pagination']['total']}")
    for pub in resultados["data"]:
        print(f"- [{pub['secao_codigo']}] {pub['titulo']}")
```

## Buscar publicações

```python
# Por data
client.buscar(date_from="2026-05-01", date_to="2026-05-08")

# Por palavra-chave
client.buscar(query="licitação", date_from="2026-05-01")

# Filtros combinados
client.buscar(
    query="edital",
    secao="DO3",         # DO1, DO2, DO3 ou Extra
    tipo="Edital",       # Portaria, Edital, Despacho, etc.
    date_from="2026-01-01",
    date_to="2026-05-08",
    page=1,
    limit=50,            # máx 100
)
```

**Filtro mínimo obrigatório.** A chamada `client.buscar()` sem nenhum dos parâmetros acima
levanta `APIError("FILTER_REQUIRED")`. Isso protege você (e o servidor) de scans amplos
da tabela de publicações (~7M+ linhas).

## Detalhes de uma publicação

A listagem retorna apenas o `texto_resumo`. Para obter o **texto completo**:

```python
ids = [p["id"] for p in resultados["data"]]
for id in ids:
    pub = client.obter_publicacao(id)
    print(pub["titulo"])
    print(pub["texto_puro"])    # texto completo
    print(pub["texto_html"])    # HTML completo
```

## Alertas

```python
# Listar alertas
alertas = client.listar_alertas()

# Criar alerta
client.criar_alerta(
    name="Concursos TI",
    search_criteria={"query": "desenvolvedor", "secao": "DO3"},
    frequency="daily",          # realtime | hourly | daily | weekly
    email_notification=True,
)
```

## Favoritos e coleções

```python
client.listar_favoritos()
client.adicionar_favorito(publication_id="12345")
client.remover_favorito(publication_id="12345")

client.listar_colecoes()
client.criar_colecao(name="Editais 2026")
```

## Vocabulário

```python
vocab = client.vocabulario()  # lista seções e tipos de ato disponíveis
```

## Tratamento de erros

```python
from radardou import RadarDOU
from radardou.exceptions import (
    AuthenticationError,
    SessionConflictError,
    RateLimitError,
    APIError,
)

try:
    with RadarDOU(api_key=os.environ["RADAR_API_KEY"]) as client:
        resultados = client.buscar(date_from="2026-05-01")
except AuthenticationError as e:
    print(f"Chave inválida ou expirada: {e}")
except SessionConflictError as e:
    print(f"Outra sessão já ativa em {e.active_ip}")
except RateLimitError as e:
    print(f"Rate limit atingido. Reset em {e.reset_at}")
except APIError as e:
    print(f"Erro {e.status_code}: {e}")
```

## Limites por plano

| Plano | Rate limit | Sessões simultâneas | Chaves |
|-------|-----------|---------------------|--------|
| Trial (5 dias) | 100 req/h | 1 | 1 |
| Profissional | 1.000 req/h | 1 | 2 |
| Premium | 5.000 req/h | 3 | 5 |
| Empresarial | 10.000 req/h | 10 | 10 |

## Licença

MIT
