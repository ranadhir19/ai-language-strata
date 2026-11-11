# ai-language-strata

**Four languages for AI — Python, TypeScript, Go & Rust: a layered tutorial with runnable examples.**

Most "which language for AI?" debates are asking the wrong question. An AI system is not one program — it is layers, and each layer rewards a different language:

> **Python makes models. TypeScript products them. Go operates them. Rust accelerates them.**

This repository teaches that map properly: two full guides, and one small runnable program per language that demonstrates the layer that language owns. No API keys, no accounts, no cost — every example runs locally on mock or built-in data.

## The layer map

| Layer | What happens there | Language that owns it |
|---|---|---|
| Research & training | Experiments, training, fine-tuning, model evaluation | **Python** |
| Data & ML pipelines | Ingestion, feature work, dataset curation | **Python** (Go for high-throughput ingestion) |
| Inference & serving | Running models at scale; the hot loops underneath | **Rust** (with Python frameworks on top) |
| Agent & application logic | LLM calls, RAG, tools, workflows | **TypeScript** and Python |
| Product & UI | Chat interfaces, dashboards, streaming UX | **TypeScript** |
| Platform & infrastructure | Gateways, queues, observability, vector databases | **Go** and Rust |
| Edge & devices | On-device inference, WASM, embedded ML | **Rust**, TypeScript (browser ML) |

## The guides

1. **[TypeScript for AI](docs/typescript-for-ai.md)** — a comprehensive tutorial: strict typing, generics, discriminated unions, validation with Zod, a step-by-step type-safe LLM call, and TypeScript's full AI footprint (agents and tool calling, RAG, structured outputs, streaming backends, browser ML, MCP servers, evals), plus a TypeScript-vs-Python decision guide, three capstone projects, and exercises. Styled HTML original: [docs/html/typescript-for-ai.html](docs/html/typescript-for-ai.html).

2. **[Four Languages for AI](docs/four-languages-for-ai.md)** — Python, TypeScript, Go, and Rust in detail: where each sits in the stack, how each is actually used, the libraries and systems that matter (PyTorch and Hugging Face; the Vercel AI SDK and MCP; Ollama and the LLM-gateway pattern; Qdrant, Candle, and Polars), honest limits for each, a nine-dimension comparison table, one worked architecture that combines all four, a five-question decision guide, and a learning path. Styled HTML original: [docs/html/four-languages-for-ai.html](docs/html/four-languages-for-ai.html).

## The examples

Each example is one self-contained file, dependency-free, demonstrating its language's layer. Header comment in each file explains what it shows.

| Example | Layer it demonstrates | Run it |
|---|---|---|
| [examples/python/extract_invoice.py](examples/python/extract_invoice.py) | Structured-output extraction + schema validation (pydantic if present, stdlib dataclass fallback) | `python3 examples/python/extract_invoice.py` |
| [examples/typescript/tool_call.ts](examples/typescript/tool_call.ts) | A schema-defined agent tool with validated dispatch — model-proposed calls are checked before execution | `npx tsx examples/typescript/tool_call.ts` |
| [examples/go/gateway.go](examples/go/gateway.go) | A streaming LLM-gateway handler: per-request timeout, one goroutine per request, stdlib only | `go run examples/go/gateway.go -selftest` |
| [examples/rust/vector_search.rs](examples/rust/vector_search.rs) | Cosine-similarity vector search — the retrieval inner loop, in miniature | `rustc -O examples/rust/vector_search.rs -o /tmp/vs && /tmp/vs` |

Every example ends in a self-check, not just printed output: if the behaviour is wrong, the program fails loudly.

## Verify the whole repo

```bash
python3 validate.py
```

The harness compiles or runs each example where its toolchain exists on the machine, honestly labels anything it must skip (with the reason), scans for stray secrets and internal references, and checks the docs are present and complete. A pass means what it says.

## The learning path

1. **Python first** — data intuition, one fine-tune, FastAPI + Pydantic.
2. **TypeScript second** — strict mode, Zod, one RAG app, one agent with tools.
3. **Go third** — goroutines, one streaming gateway, one ingestion worker. Go is deliberately quick to learn.
4. **Rust last, targeted** — ownership first, then one real component where speed or memory is measured to matter.

## The one rule worth keeping

Languages meet at contracts, never at shared memory. Define the schema once — JSON Schema, protobuf, OpenAPI — and validate on both sides. Then any layer can be rewritten in another language without drama, and the map above stays a set of choices instead of a set of regrets.

---

*Original tutorial content, written from first principles. Code examples are illustrative teaching patterns; check each library's current official docs before production use. MIT licensed — see [LICENSE](LICENSE). Compliance and provenance notes: [COMPLIANCE.md](COMPLIANCE.md).*
