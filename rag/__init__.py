"""Indexação semântica dos metadados para a arquitetura B (RAG).

Módulos:
    documents   metadados (JSON) -> documentos semânticos (função pura, determinística)
    embeddings  cliente HTTP da API de embeddings da OpenAI (sem dependências externas)
    store       DDL e acesso às tabelas rag.documents / rag.index_runs
    indexer     CLI: --dry-run, --index, --status
"""
