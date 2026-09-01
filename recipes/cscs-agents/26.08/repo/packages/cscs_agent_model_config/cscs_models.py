#!/usr/bin/env python3
"""List the models served by the CSCS production and Forno inference gateways.

READ-ONLY BY DESIGN
-------------------
Against CSCS services this script issues only metadata GETs:

    GET https://api.inference.cscs.ch/v1/models
    GET https://ai-gateway.forno-tds.tds.cscs.ch/v1/models
    GET https://ui.inference.cscs.ch/api/prices      (unless --no-pricing)
    GET https://docs.cscs.ch/services/inference/api/ (unless --no-docs)

The Forno gateway is queried only when CSCS_INFERENCE_API_KEY_FORNO is set.
None of these requests reaches a model replica, enqueues work on a GPU, or
consumes inference quota. No completion, embedding, or other inference request
is ever sent.

WHERE THE NUMBERS COME FROM
---------------------------
CONTEXT -- CSCS publishes the maximum context length of every hosted model in
the "Available models and pricing" table of its LLM Inference API docs. That
table is the authoritative figure: it is the window the deployment is actually
configured with, which is often *smaller* than the model's architectural
maximum (CSCS serves Apertus-8B-Instruct at 32k of its 64k, and GLM-5.2 at
976k of its 1M). The script scrapes that table and falls back to the snapshot
in PUBLISHED_CONTEXT below when the live page does not carry it yet.

OUTPUT -- CSCS publishes no output-token cap, and none of these models ships a
hard one either. vLLM (which CSCS runs) applies each model's own
generation_config.json by default, so the standard model defaults are already
in force server-side; where that file names a real `max_new_tokens` cap the
script uses it, and otherwise output is simply bounded by context minus
prompt. What lands in the generated configs is therefore a *client-side*
generation budget (--max-output), capped at half the published context so that
a prompt still fits in the window the two share.

EVERYTHING ELSE -- vision/audio inputs, architecture and the sampling defaults
vLLM applies come from each model's public Hugging Face config (huggingface.co),
a completely separate host. Sampling defaults are reported but never written
into the configs: the server already applies them, and re-sending them
client-side would only risk overriding them with stale values.

WHAT IT WRITES
--------------
  opencode.json            OpenCode provider blocks
  claude-code.sh           per-model `export` blocks for a `claude` session
  claude-code.settings.json  the same env, as a Claude Code settings.json block
  chatLanguageModels.json  VS Code Custom Endpoint provider array
  omp-models.yml           Oh-My-Pi ~/.omp/agent/models.yml providers block
  pi-cscs-provider.ts      Pi extensions calling pi.registerProvider()

The production gateway uses its Anthropic-compatible route, as recommended by
the CSCS documentation. Forno currently exposes only the OpenAI-compatible
Chat Completions route, so its OpenCode, Oh-My-Pi, VS Code and Pi providers use
that protocol. Claude Code output remains production-only because Claude Code
cannot use an OpenAI-compatible endpoint. Everything is written to --out-dir
(default: the current directory), contains only CSCS-managed blocks, and never
stores an API key.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

CSCS_BASE = os.environ.get(
    "CSCS_INFERENCE_BASE", "https://api.inference.cscs.ch"
).rstrip("/")
FORNO_BASE = os.environ.get(
    "CSCS_INFERENCE_BASE_FORNO",
    "https://ai-gateway.forno-tds.tds.cscs.ch",
).rstrip("/")
CSCS_DOCS = os.environ.get(
    "CSCS_INFERENCE_DOCS", "https://docs.cscs.ch/services/inference/api/"
)
CSCS_PRICES = "https://ui.inference.cscs.ch/api/prices"
HF_BASE = "https://huggingface.co"
SECRET_SH = Path.home() / ".local/share/secret-sh/secret.sh"
SECRET_NAME = "cscs-inference-api-key"
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "cscs-models"
TIMEOUT = 30

# Canonical credential names referenced by generated configs. Secret values are
# read only from the environment (or secret-sh for production) and never stored.
KEY_ENV = "CSCS_INFERENCE_API_KEY"
KEY_ALIASES = (KEY_ENV, "CSCS_API_KEY")
FORNO_KEY_ENV = "CSCS_INFERENCE_API_KEY_FORNO"
FORNO_PROVIDER_KEY = "cscs-forno"
FORNO_PROVIDER_NAME = "CSCS Forno (Experimental)"
FORNO_LABEL_SUFFIX = " [CSCS Forno]"
FORNO_FALLBACK_CONTEXT = 32768


@dataclass(frozen=True)
class Gateway:
    provider_key: str
    provider_name: str
    base_url: str
    key_env: str
    label_suffix: str
    api: str
    opencode_npm: str
    reasoning_default: bool = False


def production_gateway(args) -> Gateway:
    return Gateway(
        provider_key=args.provider_key,
        provider_name=args.provider_name,
        base_url=f"{CSCS_BASE}/v1",
        key_env=KEY_ENV,
        label_suffix=args.label_suffix,
        api="anthropic-messages",
        opencode_npm="@ai-sdk/anthropic",
    )


FORNO_GATEWAY = Gateway(
    provider_key=FORNO_PROVIDER_KEY,
    provider_name=FORNO_PROVIDER_NAME,
    base_url=f"{FORNO_BASE}/v1",
    key_env=FORNO_KEY_ENV,
    label_suffix=FORNO_LABEL_SUFFIX,
    api="openai-completions",
    opencode_npm="@ai-sdk/openai-compatible",
    reasoning_default=True,
)

# Maximum context length as published by CSCS, snapshot of the docs table taken
# 2026-08-20. Only used when the live docs page cannot be read or does not carry
# the table yet -- the scraped table always wins. Keep in sync with:
# https://docs.cscs.ch/services/inference/api/#available-models-and-pricing
PUBLISHED_CONTEXT = {
    "google/gemma-4-31B-it": 262144,
    "moonshotai/Kimi-K2.7-Code": 262144,
    "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16": 262144,
    "swiss-ai/Apertus-70B-Instruct-2509": 64000,
    "swiss-ai/Apertus-8B-Instruct-2509": 32768,
    "swiss-ai/Apertus-v1.5-70B": 262144,
    "swiss-ai/Apertus-v1.5-70B-thinking": 262144,
    "swiss-ai/Apertus-v1.5-8B": 262144,
    "swiss-ai/Apertus-v1.5-8B-thinking": 262144,
    "zai-org/GLM-5.2": 976000,
}

# "Note particularly that the -thinking variants of the Apertus models are
# served with tool use disabled." -- CSCS LLM Inference API docs. Agents that
# advertise tool calling against these get an "auto" tool choice requires
# --enable-auto-tool-choice error, so the configs must not claim tool support.
NO_TOOL_CALL = re.compile(r"apertus.*-thinking$", re.IGNORECASE)

# Tokenizers Oh-My-Pi ships, for model ids it cannot resolve on its own.
OMP_TOKENIZERS = (("kimi-k2", "kimi-k2"), ("glm-5", "glm5"), ("qwen3", "qwen3"))

# config.json keys that can hold the context window, in order of preference.
CONTEXT_KEYS = (
    "max_position_embeddings",
    "max_sequence_length",
    "max_seq_len",
    "n_positions",
    "seq_length",
)
# Nested sub-configs used by multimodal / composite models.
SUBCONFIGS = ("text_config", "llm_config", "language_config", "decoder")

# Sampling knobs vLLM picks up from generation_config.json (--generation-config
# auto is the default), i.e. the standard model defaults already in force.
SAMPLING_KEYS = ("temperature", "top_p", "top_k", "repetition_penalty")


# --------------------------------------------------------------------------- #
# credentials
# --------------------------------------------------------------------------- #
def get_api_key(
    aliases: tuple[str, ...], *, secret_name: str | None = None
) -> str | None:
    """Return a gateway key without logging or echoing it."""
    for name in aliases:
        key = os.environ.get(name)
        if key:
            return key.strip()
    if secret_name is None or not SECRET_SH.exists():
        return None
    # `secret` is a shell function, so it must be sourced before it can be called.
    proc = subprocess.run(
        ["bash", "-c", f'. "{SECRET_SH}" && secret dec {secret_name}'],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.exit(f"error: could not decrypt '{secret_name}': {proc.stderr.strip()}")
    key = proc.stdout.strip()
    if not key:
        sys.exit(f"error: '{secret_name}' decrypted to an empty value")
    return key


# --------------------------------------------------------------------------- #
# http
# --------------------------------------------------------------------------- #
def http_get(url: str, headers: dict[str, str] | None = None) -> tuple[int, str]:
    """GET a URL as text. Returns (status, body|error-string)."""
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")[:200]
    except (urllib.error.URLError, TimeoutError) as exc:
        return 0, str(exc)


def http_json(url: str, headers: dict[str, str] | None = None) -> tuple[int, object]:
    """GET a URL and parse JSON. Returns (status, payload|error-string)."""
    status, body = http_get(url, headers)
    if status != 200:
        return status, body
    try:
        return status, json.loads(body)
    except json.JSONDecodeError as exc:
        return 0, str(exc)


def auth(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}


def list_models(gateway: Gateway, api_key: str) -> list[dict]:
    """Return the models reachable through one gateway."""
    url = f"{gateway.base_url}/models"
    status, payload = http_json(url, auth(api_key))
    if status != 200:
        sys.exit(f"error: GET {url} returned HTTP {status}: {payload}")
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        sys.exit(f"error: unexpected {url} payload: {str(payload)[:200]}")
    return sorted(payload["data"], key=lambda m: m.get("id", ""))


def list_prices(api_key: str) -> dict[str, dict]:
    """CHF per token, per model. Empty dict if the endpoint is unavailable."""
    status, payload = http_json(CSCS_PRICES, auth(api_key))
    if status != 200 or not isinstance(payload, dict):
        return {}
    return {
        p["model"]: p
        for p in payload.get("prices", [])
        if isinstance(p, dict) and p.get("model")
    }


# --------------------------------------------------------------------------- #
# published context lengths (CSCS docs)
# --------------------------------------------------------------------------- #
class ContextTableParser(HTMLParser):
    """Pull the `Model | Maximum context length` table out of the docs page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def parse_context_table(html: str) -> dict[str, int]:
    """Model id -> maximum context length, from the docs' published table."""
    parser = ContextTableParser()
    parser.feed(html)

    header_seen = False
    published: dict[str, int] = {}
    for row in parser.rows:
        if len(row) < 2:
            continue
        first, second = row[0].lower(), row[1].lower()
        if "model" in first and "context" in second:
            header_seen = True
            continue
        if not header_seen:
            continue
        digits = re.sub(r"[^0-9]", "", row[1])
        if "/" in row[0] and digits:
            published[row[0].strip()] = int(digits)
        elif published:
            break  # table ended, don't wander into the next one
    return published


def fetch_published_context(url: str, refresh: bool) -> tuple[dict[str, int], str]:
    """Scrape the docs table, memoised on disk. Falls back to the snapshot."""
    cache = CACHE_DIR / "cscs-docs" / (re.sub(r"\W+", "-", url).strip("-") + ".json")
    if cache.exists() and not refresh:
        try:
            cached = json.loads(cache.read_text())
            if cached:
                return cached, f"{url} (cached)"
        except json.JSONDecodeError:
            pass  # corrupt cache entry, refetch

    status, body = http_get(url, {"User-Agent": "cscs-models/2.0"})
    if status != 200:
        return dict(PUBLISHED_CONTEXT), f"built-in snapshot (docs HTTP {status})"

    published = parse_context_table(body)
    if not published:
        return dict(PUBLISHED_CONTEXT), "built-in snapshot (no table on the docs page)"

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(published))
    return published, url


# --------------------------------------------------------------------------- #
# hugging face enrichment
# --------------------------------------------------------------------------- #
def hf_file(repo: str, filename: str, refresh: bool) -> dict | None:
    """Fetch a JSON file from a HF repo, memoised on disk. None if unavailable."""
    cache = CACHE_DIR / repo.replace("/", "__") / filename
    if cache.exists() and not refresh:
        try:
            return json.loads(cache.read_text())
        except json.JSONDecodeError:
            pass  # corrupt cache entry, refetch

    headers = {"User-Agent": "cscs-models/2.0"}
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    status, payload = http_json(f"{HF_BASE}/{repo}/resolve/main/{filename}", headers)
    if status != 200 or not isinstance(payload, dict):
        return None
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(payload))
    return payload


def dig_context(cfg: dict) -> tuple[int | None, str | None]:
    """Find the context window in a config.json, returning (value, config-path)."""
    for key in CONTEXT_KEYS:
        val = cfg.get(key)
        if isinstance(val, int) and val > 0:
            return val, key
    for sub in SUBCONFIGS:
        nested = cfg.get(sub)
        if isinstance(nested, dict):
            val, path = dig_context(nested)
            if val is not None:
                return val, f"{sub}.{path}"
    return None, None


def dig(cfg: dict, key: str):
    """Look a key up at the top level, then in known sub-configs."""
    if key in cfg:
        return cfg[key]
    for sub in SUBCONFIGS:
        nested = cfg.get(sub)
        if isinstance(nested, dict) and key in nested:
            return nested[key]
    return None


def has_key(cfg: dict, *names: str) -> bool:
    """True if any of `names` appears at the top level or in a known sub-config."""
    for name in names:
        if cfg.get(name) is not None:
            return True
    for sub in SUBCONFIGS:
        nested = cfg.get(sub)
        if isinstance(nested, dict) and has_key(nested, *names):
            return True
    return False


def finalize_context(row: dict, args) -> dict:
    """Give unresolved Forno models a conservative but usable client limit."""
    if (
        row["provider_key"] == FORNO_PROVIDER_KEY
        and row["context_window"] is None
        and args.forno_fallback_context > 0
    ):
        row["context_window"] = args.forno_fallback_context
        row["context_source"] = "forno-fallback"
        row["notes"].append(
            "Forno publishes no context metadata and public model metadata was "
            f"unavailable; using conservative {args.forno_fallback_context:,}-token "
            "fallback"
        )
    return row


def describe(
    model: dict,
    published: dict[str, int],
    prices: dict,
    gateway: Gateway,
    args,
) -> dict:
    """Build the settings record for one model id on one gateway."""
    repo = model.get("id", "")
    row: dict = {
        "provider_key": gateway.provider_key,
        "provider_name": gateway.provider_name,
        "base_url": gateway.base_url,
        "api_key_env": gateway.key_env,
        "api": gateway.api,
        "opencode_npm": gateway.opencode_npm,
        "label_suffix": gateway.label_suffix,
        "credential_available": bool(model.get("_credential_available", True)),
        "id": repo,
        "owned_by": model.get("owned_by"),
        "created": model.get("created"),
        "context_window": published.get(repo),
        "context_source": "cscs-docs" if repo in published else None,
        "architectural_context": None,
        "max_output_tokens": None,
        "max_output_source": None,
        "sampling_defaults": {},
        "sliding_window": None,
        "architecture": None,
        "model_type": None,
        "torch_dtype": None,
        "vocab_size": None,
        "rope_scaling_factor": None,
        "vision": False,
        "audio": False,
        "reasoning": gateway.reasoning_default
        or "thinking" in repo.lower()
        or "-think" in repo.lower(),
        "tool_call": not NO_TOOL_CALL.search(repo),
        "chf_per_mtok_in": None,
        "chf_per_mtok_out": None,
        "gateway_source": model.get(
            "_metadata_source", f"{gateway.base_url}/models"
        ),
        "metadata_source": None,
        "notes": [],
    }

    if not row["tool_call"]:
        row["notes"].append(
            "served with tool use disabled; not usable in agent mode "
            "(CSCS docs, 'Apertus models in agents')"
        )

    price = prices.get(repo)
    if price:
        row["chf_per_mtok_in"] = price.get("cost_per_input_token", 0) * 1_000_000
        row["chf_per_mtok_out"] = price.get("cost_per_output_token", 0) * 1_000_000
        if price.get("available") is False:
            row["notes"].append("priced but not currently loaded on the server")

    if args.no_enrich:
        return finalize_context(row, args)

    cfg = hf_file(repo, "config.json", args.refresh)
    if cfg is None:
        if row["context_window"] is None:
            row["notes"].append(
                "no published context length and no public config.json on Hugging "
                "Face (repo gated, private, or renamed); set HF_TOKEN if you have access"
            )
        return finalize_context(row, args)

    row["metadata_source"] = f"huggingface.co/{repo}/config.json"
    arch_ctx, ctx_key = dig_context(cfg)
    row["architectural_context"] = arch_ctx
    if row["context_window"] is None and arch_ctx:
        # CSCS did not publish this one: fall back to the architectural maximum,
        # which is an upper bound on whatever the deployment actually serves.
        row["context_window"] = arch_ctx
        row["context_source"] = f"huggingface config.json:{ctx_key}"
        row["notes"].append(
            "not in the CSCS table; context is the model's architectural maximum, "
            "which the deployment may not serve in full"
        )
    elif arch_ctx and row["context_window"] and arch_ctx > row["context_window"]:
        row["notes"].append(
            f"CSCS serves {row['context_window']:,} of the model's "
            f"{arch_ctx:,} architectural window"
        )

    arch = cfg.get("architectures") or dig(cfg, "architectures")
    row["architecture"] = arch[0] if isinstance(arch, list) and arch else arch
    row["model_type"] = cfg.get("model_type")
    row["torch_dtype"] = cfg.get("torch_dtype") or cfg.get("dtype") or dig(cfg, "torch_dtype")
    row["vocab_size"] = dig(cfg, "vocab_size")

    row["vision"] = has_key(cfg, "vision_config", "image_token_id", "image_token_index")
    row["audio"] = has_key(cfg, "audio_config", "audio_token_id", "audio_token_index")
    if row["audio"]:
        row["notes"].append(
            "accepts audio input, but generated agent configurations deliberately "
            "advertise only text and image inputs"
        )

    sw = dig(cfg, "sliding_window")
    if isinstance(sw, int) and sw > 0:
        row["sliding_window"] = sw
        row["notes"].append(f"interleaved sliding-window attention ({sw} tokens)")

    rope = dig(cfg, "rope_scaling")
    if isinstance(rope, dict):
        factor = rope.get("factor") or rope.get("rope_factor")
        row["rope_scaling_factor"] = factor
        if factor:
            row["notes"].append(f"context extended via RoPE scaling x{factor}")

    # Output cap and sampling defaults. vLLM loads generation_config.json by
    # default, so whatever is in there is what CSCS serves with. Only
    # `max_new_tokens` is a genuine cap on generated tokens; `max_length` bounds
    # prompt + output together, so it constrains the usable window instead.
    gen = hf_file(repo, "generation_config.json", args.refresh)
    if isinstance(gen, dict):
        new_tokens = gen.get("max_new_tokens")
        if isinstance(new_tokens, int) and new_tokens > 0:
            row["max_output_tokens"] = new_tokens
            row["max_output_source"] = "generation_config.json:max_new_tokens"
        total = gen.get("max_length")
        ctx = row["context_window"]
        if isinstance(total, int) and total > 0 and (ctx is None or total < ctx):
            row["notes"].append(
                f"generation_config.json caps prompt+output at {total} tokens"
            )
        row["sampling_defaults"] = {
            k: gen[k] for k in SAMPLING_KEYS if isinstance(gen.get(k), (int, float))
        }
    return finalize_context(row, args)


# --------------------------------------------------------------------------- #
# derived limits
# --------------------------------------------------------------------------- #
def limits(row: dict, args) -> tuple[int | None, int | None]:
    """Resolve (context, output budget) for a client config, or (None, None).

    Context is what CSCS publishes. CSCS publishes no output cap and none of
    these models ships a hard one, so the output figure is the client-side
    budget from --max-output -- unless the model's own generation_config.json
    names a real `max_new_tokens`, which wins.

    Either way the budget is capped at half the context. Prompt and completion
    share one window here, and clients derive the input allowance from the
    difference: VS Code computes maxInputTokens as contextWindow -
    maxOutputTokens, so a budget equal to the context would leave no room for
    a prompt at all.
    """
    ctx = row["context_window"] or (args.fallback_context or None)
    if ctx is None:
        return None, None
    requested = row["max_output_tokens"] or args.max_output
    return ctx, max(1024, min(requested, ctx // 2))


def agent_models(rows: list[dict], args) -> list[dict]:
    """Rows an agent can actually drive: known limits, and tool calling."""
    usable = [r for r in rows if limits(r, args)[0] is not None]
    if args.include_toolless:
        return usable
    return [r for r in usable if r["tool_call"]]


def pick_default(rows: list[dict], preferred: str) -> dict | None:
    """The model the generated configs select by default."""
    for row in rows:
        if row["id"] == preferred:
            return row
    return rows[0] if rows else None


def pick_background(rows: list[dict], default: dict | None) -> dict | None:
    """Cheapest tool-calling model, for Claude Code's Haiku-alias background work."""
    priced = [r for r in rows if r["chf_per_mtok_in"] is not None]
    if priced:
        return min(priced, key=lambda r: r["chf_per_mtok_in"])
    by_size = [r for r in rows if r["context_window"]]
    return min(by_size, key=lambda r: r["context_window"]) if by_size else default


# --------------------------------------------------------------------------- #
# output helpers
# --------------------------------------------------------------------------- #
def human(n) -> str:
    if not isinstance(n, int):
        return "-"
    if n >= 1048576 and n % 1048576 == 0:
        return f"{n // 1048576}M"
    if n >= 1024 and n % 1024 == 0:
        return f"{n // 1024}k"
    return str(n)


def short_name(model_id: str, suffix: str) -> str:
    """`moonshotai/Kimi-K2.7-Code` -> `Kimi-K2.7-Code [CSCS]`."""
    return model_id.rsplit("/", 1)[-1] + suffix


def gateway_groups(rows: list[dict]) -> list[tuple[dict, list[dict]]]:
    """Group rows by provider while preserving discovery order."""
    groups: dict[str, tuple[dict, list[dict]]] = {}
    for row in rows:
        key = row["provider_key"]
        if key not in groups:
            groups[key] = (row, [])
        groups[key][1].append(row)
    return list(groups.values())


def modalities(row: dict) -> list[str]:
    """Inputs the configs may advertise.

    Audio is deliberately left out even when public model metadata advertises
    it because client support differs across the generated API adapters.
    """
    return ["text"] + (["image"] if row["vision"] else [])


FIELDS = [
    "provider_key", "provider_name", "base_url", "api_key_env", "api",
    "credential_available",
    "id", "context_window", "context_source", "architectural_context",
    "max_output_tokens", "max_output_source", "sampling_defaults",
    "sliding_window", "architecture", "model_type", "torch_dtype", "vocab_size",
    "rope_scaling_factor", "vision", "audio", "reasoning", "tool_call",
    "chf_per_mtok_in", "chf_per_mtok_out", "gateway_source",
    "metadata_source", "owned_by", "created", "notes",
]

OPENCODE_FILE = "opencode.json"
CLAUDE_ENV_FILE = "claude-code.sh"
CLAUDE_SETTINGS_FILE = "claude-code.settings.json"
VSCODE_FILE = "chatLanguageModels.json"
OMP_FILE = "omp-models.yml"
PI_FILE = "pi-cscs-provider.ts"


# --------------------------------------------------------------------------- #
# opencode
# --------------------------------------------------------------------------- #
def build_opencode(rows: list[dict], default: dict | None, args) -> dict:
    """Build OpenCode provider blocks for both CSCS gateways."""
    providers: dict[str, dict] = {}
    for gateway, gateway_rows in gateway_groups(rows):
        models: dict[str, dict] = {}
        for row in gateway_rows:
            entry: dict = {"name": short_name(row["id"], row["label_suffix"])}
            ctx, out = limits(row, args)
            if ctx is not None:
                # OpenCode requires both fields when `limit` is present.
                entry["limit"] = {"context": ctx, "output": out}
            entry["tool_call"] = bool(row["tool_call"] and args.tool_call)
            if row["reasoning"]:
                entry["reasoning"] = True
            if row["vision"]:
                entry["modalities"] = {"input": modalities(row), "output": ["text"]}
                entry["attachment"] = True
            if row["chf_per_mtok_in"] is not None:
                # OpenCode reads `cost` as per-1M-token; CSCS bills in CHF, not USD.
                entry["cost"] = {
                    "input": round(row["chf_per_mtok_in"], 6),
                    "output": round(row["chf_per_mtok_out"], 6),
                }
            models[row["id"]] = entry

        options = {
            "baseURL": gateway["base_url"],
            "apiKey": f"{{env:{gateway['api_key_env']}}}",
        }
        if gateway["api"] == "anthropic-messages":
            options["systemMessageMode"] = "system"
        providers[gateway["provider_key"]] = {
            "npm": gateway["opencode_npm"],
            "name": gateway["provider_name"],
            "options": options,
            "models": models,
        }

    config = {"$schema": "https://opencode.ai/config.json"}
    if default is not None:
        config["model"] = f"{default['provider_key']}/{default['id']}"
    config["provider"] = providers
    return config


# --------------------------------------------------------------------------- #
# claude code
# --------------------------------------------------------------------------- #
def claude_env(row: dict, background: dict | None, args, *, with_token: bool) -> dict[str, str]:
    """The env Claude Code needs to drive one CSCS model.

    `with_token` covers the shell snippet, where
    ANTHROPIC_AUTH_TOKEN=$CSCS_INFERENCE_API_KEY expands. A settings.json `env`
    block takes literal strings only -- no shell expansion -- so there the
    credential comes from `apiKeyHelper` instead.
    """
    ctx, out = limits(row, args)
    env = {}
    if with_token:
        env["ANTHROPIC_AUTH_TOKEN"] = f"${row['api_key_env']}"
    # ANTHROPIC_BASE_URL is the host: Claude Code appends /v1/messages itself.
    env["ANTHROPIC_BASE_URL"] = row["base_url"].removesuffix("/v1")
    env["ANTHROPIC_MODEL"] = row["id"]
    if background is not None:
        # Unpinned, the haiku alias resolves to a Claude model the gateway does
        # not serve, and background work (titles, summaries) fails.
        env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = background["id"]
    env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = row["id"]
    env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = row["id"]
    if ctx is not None:
        # The id is not a Claude one and carries no [1m] marker, so Claude Code
        # takes this value directly and compacts against it.
        env["CLAUDE_CODE_MAX_CONTEXT_TOKENS"] = str(ctx)
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(out)
    if not row["reasoning"]:
        # On third-party providers 0 omits `thinking` rather than disabling it,
        # which is what a model without extended thinking needs.
        env["MAX_THINKING_TOKENS"] = "0"
    # CSCS serves /v1/models, so the picker can list the whole catalogue.
    env["CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY"] = "1"
    return env


def build_claude_env_script(rows, default, background, args) -> str:
    lines = [
        "# Claude Code against the CSCS inference service.",
        "#",
        f"# Source the block for the model you want, then run `claude`. Set {KEY_ENV}",
        "# first -- it is the only secret involved, and it is never stored here.",
        "#",
        "# CLAUDE_CODE_MAX_CONTEXT_TOKENS carries the context length CSCS publishes.",
        "# Without it Claude Code guesses a window for an unrecognised model id and",
        "# compacts at the wrong point. CLAUDE_CODE_MAX_OUTPUT_TOKENS is a client-side",
        "# budget (CSCS publishes no output cap); raising it eats into the context",
        "# available before auto-compaction runs.",
        "#",
        "# Add CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 if you want no telemetry or",
        "# auto-updates -- it also switches off the gateway model discovery enabled",
        "# below, so the /model picker falls back to the pinned aliases.",
        "#",
        f"# {CLAUDE_SETTINGS_FILE} carries the same settings for the default model. It",
        f"# leaves ANTHROPIC_AUTH_TOKEN out on purpose: a settings.json env block stores",
        "# literal strings and does not expand shell variables, so the key comes from",
        "# apiKeyHelper there instead.",
        "",
    ]
    for row in rows:
        ctx, out = limits(row, args)
        marker = "  <- default" if default is not None and row["id"] == default["id"] else ""
        lines.append(
            f"# --- {row['id']} (context {ctx:,}, output budget {out:,}){marker}"
        )
        for note in row["notes"]:
            lines.append(f"#     note: {note}")
        for key, value in claude_env(row, background, args, with_token=True).items():
            lines.append(f'export {key}="{value}"')
        lines.append("")

    if not rows:
        lines.append("# No model had a resolvable context length.")
        lines.append("")
    return "\n".join(lines)


def build_claude_settings(default, background, args) -> dict:
    """The same configuration as a Claude Code settings.json block.

    Covers the default model only -- the context and output keys describe one
    active model, so a settings file pins one. apiKeyHelper supplies the
    credential: its output is sent as both X-Api-Key and Authorization: Bearer,
    and the CSCS gateway accepts either.
    """
    settings: dict = {"apiKeyHelper": args.api_key_helper}
    if default is None:
        settings["env"] = {}
        return settings
    settings["env"] = claude_env(default, background, args, with_token=False)
    return settings


# --------------------------------------------------------------------------- #
# vs code
# --------------------------------------------------------------------------- #
def build_vscode(rows: list[dict], args) -> list[dict]:
    """Build one VS Code Custom Endpoint entry per gateway."""
    providers = []
    for gateway, gateway_rows in gateway_groups(rows):
        api_type = (
            "messages" if gateway["api"] == "anthropic-messages"
            else "chat-completions"
        )
        endpoint = (
            "messages" if api_type == "messages"
            else "chat/completions"
        )
        models = []
        for row in gateway_rows:
            entry: dict = {
                "id": row["id"],
                "name": short_name(row["id"], row["label_suffix"]),
                "url": f"{row['base_url']}/{endpoint}",
                "toolCalling": bool(row["tool_call"] and args.tool_call),
                "vision": bool(row["vision"]),
            }
            ctx, out = limits(row, args)
            if ctx is not None:
                entry["contextWindow"] = ctx
                entry["maxOutputTokens"] = out
            if row["reasoning"]:
                entry["thinking"] = True
            models.append(entry)

        input_name = (
            "cscsApiKey"
            if gateway["provider_key"] != FORNO_PROVIDER_KEY
            else "cscsFornoApiKey"
        )
        providers.append({
            "name": gateway["provider_name"],
            "vendor": "customendpoint",
            "apiKey": f"${{input:{input_name}}}",
            "apiType": api_type,
            "models": models,
        })
    return providers


# --------------------------------------------------------------------------- #
# pi / oh-my-pi
# --------------------------------------------------------------------------- #
def omp_tokenizer(model_id: str) -> str | None:
    lowered = model_id.lower()
    for needle, tokenizer in OMP_TOKENIZERS:
        if needle in lowered:
            return tokenizer
    return None


def yaml_scalar(value) -> str:
    """Quote only what YAML would otherwise misread."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if not text or re.search(r"[:#{}\[\],&*?|<>=!%@`'\"]|^\s|\s$", text):
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return text


def build_omp(rows: list[dict], args) -> str:
    """Build Oh-My-Pi providers for ~/.omp/agent/models.yml."""
    out_lines = [
        "# CSCS inference gateways for Oh-My-Pi.",
        "# `apiKey` names an environment variable; no key is stored here.",
        "# Production uses Anthropic Messages; Forno uses OpenAI Chat Completions.",
        "#",
        "# contextWindow is published deployment metadata where available, otherwise",
        "# public model metadata or the conservative Forno fallback. maxTokens is a",
        "# client-side output budget.",
        "providers:",
    ]
    for gateway, gateway_rows in gateway_groups(rows):
        out_lines.extend([
            f"  {gateway['provider_key']}:",
            f"    baseUrl: {gateway['base_url']}",
            f"    apiKey: {gateway['api_key_env']}",
            f"    api: {gateway['api']}",
            "    authHeader: true",
            "    disableStrictTools: true",
            "    models:",
        ])
        for row in gateway_rows:
            ctx, out = limits(row, args)
            fields = [
                ("id", row["id"]),
                ("name", short_name(row["id"], row["label_suffix"])),
                ("reasoning", bool(row["reasoning"])),
                ("contextWindow", ctx),
                ("maxTokens", out),
            ]
            tokenizer = omp_tokenizer(row["id"])
            if tokenizer:
                fields.insert(3, ("tokenizer", tokenizer))

            for note in row["notes"]:
                out_lines.append(f"      # {note}")
            head, *rest = fields
            out_lines.append(f"      - {head[0]}: {yaml_scalar(head[1])}")
            for key, value in rest:
                out_lines.append(f"        {key}: {yaml_scalar(value)}")
            out_lines.append(
                "        input: [" + ", ".join(modalities(row)) + "]"
            )
            if row["chf_per_mtok_in"] is not None:
                out_lines.append("        cost:  # CHF per 1M tokens, not USD")
                out_lines.append(f"          input: {round(row['chf_per_mtok_in'], 6)}")
                out_lines.append(f"          output: {round(row['chf_per_mtok_out'], 6)}")
                out_lines.append(f"          cacheRead: {round(row['chf_per_mtok_in'], 6)}")
                out_lines.append(f"          cacheWrite: {round(row['chf_per_mtok_in'], 6)}")
    out_lines.append("")
    return "\n".join(out_lines)


def build_pi(rows: list[dict], args) -> str:
    """Build a Pi extension registering every discovered CSCS gateway."""
    registrations = []
    for gateway, gateway_rows in gateway_groups(rows):
        models = []
        for row in gateway_rows:
            ctx, out = limits(row, args)
            entry = {
                "id": row["id"],
                "name": short_name(row["id"], row["label_suffix"]),
                "reasoning": bool(row["reasoning"]),
                "input": modalities(row),
                "cost": {
                    "input": round(row["chf_per_mtok_in"] or 0, 6),
                    "output": round(row["chf_per_mtok_out"] or 0, 6),
                    "cacheRead": round(row["chf_per_mtok_in"] or 0, 6),
                    "cacheWrite": round(row["chf_per_mtok_in"] or 0, 6),
                },
                "contextWindow": ctx,
                "maxTokens": out,
            }
            block = json.dumps(entry, indent=2)
            models.append("\n".join("      " + line for line in block.splitlines()))

        body = ",\n".join(models)
        registrations.append(
            f"""  pi.registerProvider("{gateway['provider_key']}", {{
    name: {json.dumps(gateway['provider_name'])},
    baseUrl: {json.dumps(gateway['base_url'])},
    apiKey: "${gateway['api_key_env']}",
    api: "{gateway['api']}",
    models: [
{body}
    ],
  }});"""
        )

    registration_body = "\n\n".join(registrations)
    return f"""// CSCS inference gateways for Pi.
// `apiKey` reads environment variables; no key is stored here.
import type {{ ExtensionAPI }} from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {{
{registration_body}
}}
"""


# --------------------------------------------------------------------------- #
# reports
# --------------------------------------------------------------------------- #
def print_table(rows: list[dict], context_source: str, args) -> None:
    cols = [
        ("PROVIDER", lambda r: r["provider_key"]),
        ("MODEL", lambda r: r["id"]),
        ("CONTEXT", lambda r: human(r["context_window"])),
        ("SOURCE", lambda r:
            "cscs" if r["context_source"] == "cscs-docs" else
            "hf" if r["context_source"] and r["context_source"].startswith("huggingface") else
            "fallback" if r["context_source"] == "forno-fallback" else "-"),
        ("ARCH MAX", lambda r: human(r["architectural_context"])),
        ("OUT BUDGET", lambda r: human(limits(r, args)[1])),
        ("TOOLS", lambda r: "yes" if r["tool_call"] else "NO"),
        ("CHF/MTOK IN", lambda r: "-" if r["chf_per_mtok_in"] is None
                                  else f"{r['chf_per_mtok_in']:.3f}"),
    ]
    table = [[h for h, _ in cols]] + [[f(r) for _, f in cols] for r in rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(cols))]
    for i, row in enumerate(table):
        print("  ".join(c.ljust(w) for c, w in zip(row, widths)).rstrip())
        if i == 0:
            print("  ".join("-" * w for w in widths))

    sources = ", ".join(
        f"{gateway['provider_key']}={len(gateway_rows)}"
        for gateway, gateway_rows in gateway_groups(rows)
    )
    print(f"\n{len(rows)} model(s): {sources}")
    print("CONTEXT source 'cscs': maximum context length published by CSCS at")
    print(f"  {context_source}")
    print(
        "  -- the window the production deployment serves. 'hf' is the public\n"
        "  architectural maximum and an upper bound on a gateway deployment.\n"
        "  'fallback' is the conservative Forno default used only when public\n"
        "  metadata is unavailable. ARCH MAX is shown for comparison.\n"
        "OUT BUDGET is a client-side generation budget clamped to the context."
    )
    flagged = [r for r in rows if r["notes"]]
    if flagged:
        print("\nNotes:")
        for r in flagged:
            for note in r["notes"]:
                print(f"  {r['provider_key']}/{r['id']}: {note}")


def write_or_print(text: str, filename: str, args) -> None:
    if args.stdout:
        print(f"// ---- {filename} ----")
        print(text, end="" if text.endswith("\n") else "\n")
        return
    path = Path(args.out_dir).expanduser() / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(f"wrote {path}", file=sys.stderr)


def write_json(payload, filename: str, args) -> None:
    write_or_print(json.dumps(payload, indent=2) + "\n", filename, args)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
FORMATS = ("configs", "opencode", "claude-code", "vscode", "pi", "table", "json", "csv")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--format", choices=FORMATS, default="configs",
        help="configs (default) writes every client config; opencode/claude-code/"
             "vscode/pi write one; table/json/csv report the raw model settings",
    )
    parser.add_argument(
        "--out-dir", default=".",
        help="directory to write the generated config files into (default: .)",
    )
    parser.add_argument(
        "--stdout", action="store_true",
        help="print the generated configs instead of writing files",
    )
    parser.add_argument(
        "--max-output", type=int, default=32768, metavar="N",
        help="client-side output-token budget, capped at half of each model's "
             "published context so a prompt still fits. CSCS publishes no output "
             "cap, so this is your choice, not the server's (default: 32768)",
    )
    parser.add_argument(
        "--fallback-context", type=int, default=0, metavar="N",
        help="context to assume for models CSCS does not publish and whose metadata "
             "could not be resolved; 0 (default) leaves them out of the configs "
             "rather than guessing",
    )
    parser.add_argument(
        "--forno-fallback-context",
        type=int,
        default=FORNO_FALLBACK_CONTEXT,
        metavar="N",
        help="context used only when a Forno model has no public metadata; this "
             "keeps newly deployed experimental models usable until metadata appears "
             f"(default: {FORNO_FALLBACK_CONTEXT})",
    )
    parser.add_argument(
        "--default-model", default="moonshotai/Kimi-K2.7-Code", metavar="ID",
        help="model the generated configs select by default, matching the CSCS "
             "docs (default: moonshotai/Kimi-K2.7-Code)",
    )
    parser.add_argument(
        "--api-key-helper", default=f"printenv {KEY_ENV}", metavar="CMD",
        help="command Claude Code's settings.json runs to obtain the key, since an "
             f"env block cannot expand ${KEY_ENV} itself "
             f"(default: printenv {KEY_ENV})",
    )
    parser.add_argument(
        "--include-toolless", action="store_true",
        help="also emit models CSCS serves with tool use disabled (the Apertus "
             "-thinking variants), which no agent can drive",
    )
    parser.add_argument("--provider-key", default="cscs", help="provider key / group name (default: cscs)")
    parser.add_argument("--provider-name", default="CSCS Inference", help="provider display name")
    parser.add_argument("--label-suffix", default=" [CSCS]", help="suffix appended to each model label")
    parser.add_argument(
        "--no-tool-call", dest="tool_call", action="store_false",
        help="do not advertise tool calling at all (VS Code hides non-tool-calling "
             "models from agent mode)",
    )
    parser.add_argument(
        "--docs-url", default=CSCS_DOCS, metavar="URL",
        help=f"page carrying the published context-length table (default: {CSCS_DOCS})",
    )
    parser.add_argument(
        "--no-docs", action="store_true",
        help="skip the docs lookup and use the built-in snapshot of the published "
             "context lengths",
    )
    parser.add_argument(
        "--no-pricing", action="store_true",
        help="skip the CSCS pricing lookup; configs are then emitted without costs",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help=f"bypass the metadata cache in {CACHE_DIR}",
    )
    parser.add_argument(
        "--no-enrich", action="store_true",
        help="use only what CSCS itself publishes, with no Hugging Face lookups",
    )
    args = parser.parse_args()

    production_key = get_api_key(KEY_ALIASES, secret_name=SECRET_NAME)
    forno_key = get_api_key((FORNO_KEY_ENV,))
    if production_key is None and forno_key is None:
        sys.exit(
            f"error: no CSCS inference key is available.\n"
            f"       Set {KEY_ENV}=... for production and/or "
            f"{FORNO_KEY_ENV}=... for Forno."
        )

    if args.no_docs:
        published, context_source = (
            dict(PUBLISHED_CONTEXT),
            "built-in snapshot (--no-docs)",
        )
    else:
        published, context_source = fetch_published_context(
            args.docs_url, args.refresh
        )

    work: list[tuple[dict, dict[str, int], dict, Gateway]] = []
    production = production_gateway(args)
    if production_key is not None:
        production_models = list_models(production, production_key)
        production_prices = (
            {} if args.no_pricing else list_prices(production_key)
        )
        for model in production_models:
            model["_credential_available"] = True
    else:
        # The launcher replaces its whole managed file atomically. Preserve the
        # production provider when only a Forno key is available by regenerating
        # it from the published model snapshot; it becomes selectable whenever
        # the production key is exported later.
        production_models = [
            {
                "id": model_id,
                "_credential_available": False,
                "_metadata_source": context_source,
            }
            for model_id in sorted(published)
        ]
        production_prices = {}
    work.extend(
        (model, published, production_prices, production)
        for model in production_models
    )

    if forno_key is not None:
        forno_models = list_models(FORNO_GATEWAY, forno_key)
        for model in forno_models:
            model["_credential_available"] = True
        # Forno has no pricing or deployment-context endpoint. Public model
        # metadata is used when available, then the conservative fallback.
        work.extend((model, {}, {}, FORNO_GATEWAY) for model in forno_models)

    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(
            pool.map(
                lambda item: describe(*item, args),
                work,
            )
        )

    if args.format == "json":
        json.dump(rows, sys.stdout, indent=2)
        print()
        return
    if args.format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **row,
                "notes": "; ".join(row["notes"]),
                "sampling_defaults": json.dumps(row["sampling_defaults"]),
            })
        return
    if args.format == "table":
        print_table(rows, context_source, args)
        return

    usable = agent_models(rows, args)
    available = [row for row in usable if row["credential_available"]]
    default = pick_default(available, args.default_model)
    claude_rows = [row for row in available if row["api"] == "anthropic-messages"]
    claude_default = pick_default(claude_rows, args.default_model)
    background = pick_background(claude_rows, claude_default)

    if args.format in ("configs", "opencode"):
        write_json(build_opencode(usable, default, args), OPENCODE_FILE, args)
    if args.format in ("configs", "claude-code"):
        write_or_print(
            build_claude_env_script(
                claude_rows, claude_default, background, args
            ),
            CLAUDE_ENV_FILE,
            args,
        )
        write_json(
            build_claude_settings(claude_default, background, args),
            CLAUDE_SETTINGS_FILE,
            args,
        )
    if args.format in ("configs", "vscode"):
        write_json(build_vscode(usable, args), VSCODE_FILE, args)
    if args.format in ("configs", "pi"):
        write_or_print(build_omp(usable, args), OMP_FILE, args)
        write_or_print(build_pi(usable, args), PI_FILE, args)

    print(f"\nproduction context lengths from: {context_source}", file=sys.stderr)
    if default is not None:
        print(
            f"default model:        {default['provider_key']}/{default['id']}",
            file=sys.stderr,
        )
    if background is not None and background is not claude_default:
        print(
            f"background model:     {background['id']} (Claude Code haiku alias)",
            file=sys.stderr,
        )

    dropped = [
        f"{row['provider_key']}/{row['id']}"
        for row in rows
        if row not in usable
    ]
    if dropped:
        print(
            f"\nnote: {len(dropped)} model(s) left out of the configs:\n  "
            + "\n  ".join(dropped)
            + "\n  Either CSCS serves them with tool use disabled (--include-toolless "
              "emits them\n  anyway) or no context length could be resolved (set "
              "HF_TOKEN for gated repos,\n  or pass --fallback-context N to assume a "
              "window).",
            file=sys.stderr,
        )
    print(
        f"\nreminder: no generated file contains an API key. Export {KEY_ENV} for "
        f"production and {FORNO_KEY_ENV} for Forno. OpenCode, Oh-My-Pi and Pi read "
        "those variables directly; Claude Code output is production-only; VS Code "
        "prompts for separate provider keys. Merge each block into your real config "
        "-- nothing was written to a live config location.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
