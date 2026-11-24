"""Cliente mínimo da API de embeddings da OpenAI (POST /v1/embeddings), só com a biblioteca padrão.

A chave vem de OPENAI_API_KEY (ou OPENAI_API, nome usado no .env do projeto) e nunca é impressa.
Nenhuma chamada de rede acontece ao importar o módulo ou criar o cliente; só em embed().
"""

from __future__ import annotations

import json
import math
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

MODEL = "text-embedding-3-small"
DIMENSIONS = 1536          # dimensão nativa do modelo; enviada explicitamente na requisição
PRICE_USD_PER_1M_TOKENS = 0.02   # preço de tabela do modelo (verificar em openai.com/api/pricing)
API_URL = "https://api.openai.com/v1/embeddings"
KEY_VARS = ("OPENAI_API_KEY", "OPENAI_API")
BATCH_SIZE = 64


class EmbeddingError(RuntimeError):
    pass


@dataclass
class EmbeddingResult:
    vectors: list[list[float]]
    prompt_tokens: int
    model: str


def api_key_from_env() -> str | None:
    for var in KEY_VARS:
        if os.environ.get(var):
            return os.environ[var]
    return None


def estimate_tokens(text: str) -> int:
    """Estimativa conservadora (limite superior) para custo: ~3 bytes UTF-8 por token.

    O tokenizer do modelo (cl100k_base) produz em média ~4 caracteres por token em inglês e um
    pouco menos em português. A contagem real é registrada em rag.index_runs.prompt_tokens.
    """
    return math.ceil(len(text.encode("utf-8")) / 3)


def estimate_cost_usd(tokens: int) -> float:
    return tokens * PRICE_USD_PER_1M_TOKENS / 1_000_000


Transport = Callable[[str, dict, dict, float], dict]


def _urllib_transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:500]
        raise _HTTPStatus(exc.code, body) from None


class _HTTPStatus(Exception):
    def __init__(self, code: int, body: str):
        super().__init__(f"HTTP {code}: {body}")
        self.code = code


class OpenAIEmbedder:
    def __init__(self, api_key: str | None = None, model: str = MODEL, dimensions: int = DIMENSIONS,
                 transport: Transport = _urllib_transport, timeout: float = 60.0, max_retries: int = 3,
                 sleep: Callable[[float], None] = time.sleep):
        self.api_key = api_key if api_key is not None else api_key_from_env()
        if not self.api_key:
            raise EmbeddingError(f"Chave da OpenAI ausente: defina {' ou '.join(KEY_VARS)} no ambiente ou no .env.")
        self.model = model
        self.dimensions = dimensions
        self._transport = transport
        self._timeout = timeout
        self._max_retries = max_retries
        self._sleep = sleep

    def _request(self, texts: list[str]) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "input": texts, "dimensions": self.dimensions, "encoding_format": "float"}
        for attempt in range(self._max_retries + 1):
            try:
                return self._transport(API_URL, headers, payload, self._timeout)
            except _HTTPStatus as exc:
                # 429 por falta de crédito/cota não se resolve com nova tentativa
                quota = "insufficient_quota" in str(exc) or "credit_balance_exhausted" in str(exc)
                retryable = (exc.code == 429 and not quota) or exc.code >= 500
                if not retryable or attempt == self._max_retries:
                    raise EmbeddingError(f"Falha na API de embeddings: {exc}") from None
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == self._max_retries:
                    raise EmbeddingError(f"Falha de rede na API de embeddings: {exc}") from None
            self._sleep(2 ** attempt)
        raise AssertionError("inalcançável")

    def embed(self, texts: list[str]) -> EmbeddingResult:
        vectors: list[list[float]] = []
        tokens = 0
        for start in range(0, len(texts), BATCH_SIZE):
            batch = texts[start:start + BATCH_SIZE]
            data = self._request(batch)
            items = sorted(data["data"], key=lambda d: d["index"])
            if len(items) != len(batch):
                raise EmbeddingError(f"API devolveu {len(items)} vetores para {len(batch)} textos")
            for item in items:
                if len(item["embedding"]) != self.dimensions:
                    raise EmbeddingError(f"Dimensão inesperada: {len(item['embedding'])} (esperado {self.dimensions})")
                vectors.append([float(x) for x in item["embedding"]])
            tokens += int(data.get("usage", {}).get("prompt_tokens", 0))
            if data.get("model") and not str(data["model"]).startswith(self.model):
                raise EmbeddingError(f"Modelo inesperado na resposta: {data['model']}")
        return EmbeddingResult(vectors=vectors, prompt_tokens=tokens, model=self.model)
