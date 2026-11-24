# Workflows do n8n

Cópia versionada dos workflows das arquiteturas avaliadas, exportada do n8n local. Ela registra
exatamente o que foi executado nos experimentos (prompts, modelo, consultas e código dos nós).

| arquivo | workflow | webhook (produção) |
|---|---|---|
| `workflows/arquitetura_A_baseline.json` | TCC \| A - NL2SQL Baseline | `/webhook/tcc/baseline` |
| `workflows/arquitetura_B_rag.json` | TCC \| B - NL2SQL RAG | `/webhook/tcc/rag` |

Os arquivos contêm apenas a definição do workflow (`nodes`, `connections`, `settings`). As
credenciais aparecem só por nome e id; senhas e chaves ficam no n8n e no `.env`.

## Credenciais esperadas

| credencial | tipo | uso |
|---|---|---|
| `OpenAI account` | OpenAI | LLM (A e B) e embedding da pergunta (B) |
| `Postgres account` | Postgres, role `nl2sql_readonly`, host `db` | execução do SQL gerado (A e B) |
| `Postgres rag_reader` | Postgres, role `rag_reader`, host `db` | busca vetorial em `rag.documents` (B) |

## Importar

No n8n: **Workflows → Import from File**, selecione o JSON e associe as credenciais acima nos
nós que as usam. Depois **publique** o workflow: no n8n 2.x, salvar cria um rascunho e o webhook
de produção continua executando a versão publicada.

## Manter atualizado

Ao alterar um workflow no n8n, exporte-o de novo para esta pasta e faça o commit, para que a
versão versionada corresponda à usada nos experimentos. O campo `versionId` identifica a versão
exportada.
