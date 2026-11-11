> Markdown conversion of the companion HTML guide. The original styled version is in [docs/html/four-languages-for-ai.html](html/four-languages-for-ai.html).

Four Languages for AI — Python, TypeScript, Go & Rust in Detail

 PythonTypeScriptGoRust

# Four Languages for AI

How Python, TypeScript, Go, and Rust are each used to build real AI systems — in detail: what layer each owns, what libraries matter, what code looks like, when to choose which, and how production systems combine all four.

Prepared for Ranadhir Ghosh • November 11, 2026 • Companion to “TypeScript for AI”

The One Idea That Organises Everything

## An AI system is not one program — it is layers

Ask “which language for AI?” and you get a religious war. Ask “which language for *this layer* of an AI system?” and you get engineering. A production AI system has roughly seven layers, and each of the four languages owns different ones:

| Layer | What happens there | Primary language(s) |
| --- | --- | --- |
| 1. Research & training | Experiments, training, fine-tuning, evaluation of models | Python (almost exclusively) |
| 2. Data & ML pipelines | Ingestion, feature engineering, batch jobs, dataset curation | Python, Go for high-throughput ingestion |
| 3. Inference & serving | Running models at scale, low latency, batching, GPU scheduling | Python frameworks on top; Rust / Go / C++ underneath and around |
| 4. Agent & application logic | LLM calls, RAG, tools, workflows, business rules | TypeScript and Python |
| 5. Product & UI | Chat interfaces, dashboards, mobile, streaming UX | TypeScript (only real option on web) |
| 6. Platform & infrastructure | Gateways, queues, observability, vector DBs, tokenisers, infra tooling | Go and Rust |
| 7. Edge & devices | On-device inference, embedded, WASM, privacy-sensitive ML | Rust, TypeScript (browser ML) |

**The short version:** Python *makes* models. TypeScript *products* them. Go *operates* them at scale. Rust *accelerates* them. Most serious AI organisations use at least three of the four — deliberately, per layer.

## Python — the language models are born in

The research, training, and data-science layer. If a paper has code, it is Python.

### Why Python won AI research

- **The ecosystem is the moat:** PyTorch, TensorFlow, JAX, Hugging Face Transformers, scikit-learn, NumPy, pandas — decades of compounding. Every new model, dataset, and technique ships Python-first, often Python-only.
- **Notebooks:** Jupyter's experiment loop (run a cell, see a plot, adjust) matches how research actually works.
- **Glue power:** Python calls C/C++/CUDA underneath — NumPy, PyTorch kernels, tokenisers — so it is slow as a language but fast as an orchestrator of fast code.

### How Python is used in AI, concretely

#### 1. Training and fine-tuning

```
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B")
tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B")
# Fine-tune (LoRA via peft), evaluate, export — all Python, all the time.
# No serious team trains in TypeScript, Go, or Rust directly.
```

#### 2. LLM applications (the other half of Python's AI life)

LangChain (Python original), LlamaIndex, DSPy, Instructor, Pydantic AI, CrewAI / AutoGen for multi-agent work, and FastAPI backends. Python's superpower here is **Pydantic**: typed data models that double as LLM structured-output schemas — the same contract-first pattern TypeScript gets from Zod.

```
from pydantic import BaseModel, Field

class Invoice(BaseModel):
    vendor: str
    total: float = Field(ge=0)
    due_date: str | None = None
# Pass Invoice as the response schema → validated, typed extraction.
```

#### 3. Data, evaluation, and MLOps

Dataset curation, embedding jobs, offline evals, experiment tracking (MLflow, Weights & Biases), and serving wrappers (vLLM and Triton expose Python-first interfaces, FastAPI / LiteLLM gateways).

### Python's limits — know them honestly

- **Concurrency:** the GIL makes CPU-bound parallelism awkward; async helps I/O, not compute.
- **Latency & footprint:** slow startup, heavy memory — painful for edge, CLIs, and tight-latency serving.
- **Type safety is opt-in:** type hints + mypy/Pydantic help enormously, but the runtime will not save you the way a compiler does.
- **Distribution:** shipping Python to end users (desktop, mobile, browser) is painful compared with a single Go/Rust binary or a web app.

**Choose Python when:** training, fine-tuning, research, data science, notebooks, evals, or when the library you need exists only in Python. That is a *lot* of AI — Python is not “one option”, it is the foundation.

## TypeScript — the language AI products are built in

The application, agent, and experience layer. Full detail in the companion guide “TypeScript for AI”.

### Why TypeScript owns the product layer

- **It is the web's language:** every browser AI experience — streaming chat, copilots, dashboards — is TypeScript/React by necessity.
- **Typed SDKs for every provider:** OpenAI, Anthropic, Gemini, Azure OpenAI, plus the Vercel AI SDK and LangChain.js. Model APIs change fast; the compiler tells you where.
- **JSON-native:** AI is JSON in, JSON out. TypeScript + Zod turns untrusted model output into trusted, typed data.
- **One codebase, front to back:** UI, API, agent logic, and edge functions share types end-to-end.

### How TypeScript is used in AI, concretely

#### Agents & tool calling

Tools defined once with a Zod schema; every model-proposed call validated before execution. Agent loops, routers, and human-approval flows.

#### RAG products

Ingestion jobs, vector-store clients (Pinecone, Qdrant, pgvector), typed retrieval, citation-aware answers shared between API and UI.

#### Streaming AI APIs

Node / edge backends (Next.js, Hono, Fastify, NestJS) streaming tokens over SSE/WebSockets with low ceremony.

#### Browser & on-device ML

Transformers.js, TensorFlow.js, ONNX Runtime Web — real models running client-side for privacy, cost, and offline use.

#### MCP servers

The Model Context Protocol's reference SDK is TypeScript-first; most tools-for-agents ship as npm packages.

#### Evals & guardrails

promptfoo, typed eval datasets, output-schema middleware, cost and trace logging next to the product code.

```
import { tool } from "ai"; import { z } from "zod";
export const lookupOrder = tool({
  description: "Look up an order by id",
  inputSchema: z.object({ orderId: z.string().regex(/^ORD-\d+$/) }),
  execute: async ({ orderId }) => db.orders.find(orderId), // fully typed
});
```

### TypeScript's limits

- No training ecosystem — it calls models, it does not create them.
- Numeric / GPU work is borrowed (WASM, native bindings, or a Python service).
- Runtime is single-threaded per process; CPU-heavy work needs workers or another service.

**Choose TypeScript when:** building anything a user touches, agent/application logic around model APIs, RAG products, MCP tools, or a small team shipping a full-stack AI product fast and safely.

## Go — the language AI infrastructure runs on

The operations layer: fast, concurrent, single-binary services that move AI traffic at scale.

### Why Go won cloud infrastructure (and therefore AI infrastructure)

- **Concurrency is the product:** goroutines + channels make it natural to run thousands of simultaneous streaming LLM requests, each waiting on a slow model, without burning memory.
- **One static binary:** no runtime, no dependency hell — build once, deploy anywhere. Startup in milliseconds, tiny containers.
- **Boring on purpose:** a small language, fast compile, built-in formatting/testing/race detector. Large teams stay productive; this is why Docker, Kubernetes, Terraform, and much of the cloud-native stack are Go.
- **Strong standard library for networking:** HTTP servers, proxies, and gRPC are first-class without a framework war.

### How Go is used in AI, concretely

#### 1. LLM gateways, proxies, and routers

The traffic cop layer of production AI: a Go service in front of OpenAI / Anthropic / Azure / self-hosted models handling auth, rate limits, per-team token budgets, model routing (cheap model first, escalate when needed), fallbacks, caching, and audit logging. Go's concurrency + tiny footprint make it the default choice here; several commercial and open-source AI gateways are Go.

```
// A streaming proxy sketch: one goroutine per request, cheap and safe.
func handler(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 60*time.Second)
    defer cancel()
    stream, err := llm.Stream(ctx, r) // typed client call to the provider
    if err != nil { http.Error(w, "upstream", 502); return }
    for chunk := range stream { fmt.Fprint(w, chunk); w.(http.Flusher).Flush() }
}
```

#### 2. High-throughput data ingestion for AI

Event collectors, log pipelines, document crawlers, and streaming ETL feeding training sets and vector indexes — jobs where Python workers would need far more machines for the same throughput.

#### 3. Inference-adjacent services

Go wraps and orchestrates model servers: request batching/queueing in front of vLLM/Triton, autoscaling signals, health and load management, and multi-model routing. **Ollama** — the popular local-LLM runner — is written in Go, wrapping llama.cpp: a perfect example of Go as the operational shell around fast native inference.

#### 4. Vector and AI platform components

Parts of the modern data/AI infra stack are Go (e.g., Milvus's ecosystem includes large Go components; many feature stores, queues, and observability collectors are Go). Kubernetes operators for GPU fleets and model deployments are Go by definition.

#### 5. CLI and developer tooling for AI

Fast, single-binary CLIs for model management, dataset tools, and platform operations ship in Go because distribution is trivial.

### Go's limits for AI

- Almost no ML library ecosystem — no PyTorch, no notebooks, no data-science culture. You will not train in Go.
- The LLM SDK landscape exists (official and community clients, langchaingo) but is thinner and less idiomatic than Python/TypeScript.
- Generics arrived late and the type system is deliberately simple — complex typed domain modelling is more verbose/less expressive than TypeScript or Rust.

**Choose Go when:** the problem is *scale, concurrency, or operations* — gateways, ingestion, orchestration, infra tooling, platform services — especially where one deployable binary and predictable performance matter more than ML libraries.

## Rust — the language AI gets fast in

The performance layer: inference engines, tokenisers, vector search, and on-device ML — where milliseconds and memory are money.

### Why Rust matters more every year in AI

- **C/C++ speed, without C/C++ memory bugs:** the borrow checker guarantees memory safety at compile time — no garbage collector, no pauses, no segfaults in production.
- **AI is bottlenecked below the API:** tokenisation, tensor ops, vector search, and data loading decide cost and latency. Those hot paths are increasingly Rust (often replacing C++ in new code).
- **Rust is Python's secret engine:** many “Python” AI tools are Rust underneath, exposed to Python via bindings (PyO3).

### How Rust is used in AI, concretely — with receipts

| System | What Rust does there |
| --- | --- |
| Hugging Face Tokenizers | The fast tokeniser library used across the Python ecosystem — Rust core, Python face. |
| Candle (Hugging Face) | A Rust ML framework for efficient inference, including running LLMs — minimal, hackable, GPU + CPU. |
| mistral.rs / llama.cpp-adjacent servers | Rust LLM inference servers focused on fast, ergonomic local/self-hosted serving. |
| Qdrant | A production vector database written in Rust — HNSW search, filtering, and storage at low latency. |
| Polars | The Rust dataframe engine (Python's fastest alternative to pandas) — data prep for ML at a fraction of the time/memory. |
| ONNX Runtime / tokenisers / safetensors | Rust appears across the inference plumbing: model formats, runtimes, and loading paths. |
| Burn | A Rust deep-learning framework with a serious training story — the exception that shows where Rust ML is heading. |

#### 1. Inference engines and serving hot paths

When a team self-hosts models and the bill is GPU-hours, the serving layer's efficiency is profit. Rust is used to build inference servers, schedulers, and KV-cache-aware routers, and to write the CPU-side hot loops (tokenisation, sampling, detokenisation) that otherwise starve the GPU.

#### 2. Vector search and retrieval internals

ANN indexes (HNSW), embedding stores, and hybrid search engines are latency-critical data structures — Rust (Qdrant) and C++ (FAISS) territory. Your TypeScript/Python RAG app calls them; Rust makes them fast.

#### 3. Data infrastructure for ML

Polars, Arrow implementations, fast loaders and parsers: the unglamorous work of feeding training and inference, done 5–50× faster than pure Python equivalents.

#### 4. Edge, embedded, and WebAssembly ML

Rust compiles to WASM and to microcontrollers: on-device inference where memory is measured in megabytes, battery matters, and a garbage collector is not welcome. Privacy-sensitive and safety-critical ML (vehicles, medical devices, industrial) increasingly prefers Rust's guarantees.

```
// The Rust shape: errors are values, resources have owners, nothing is null.
fn embed_batch(texts: &[String]) -> Result<Vec<Vec<f32>>, EmbedError> {
    let tokens = tokenize(texts)?;          // `?` propagates a typed error
    model.forward(&tokens)                  // no GC, no data races — compiler-proven
}
```

### Rust's limits — be honest

- **Steepest learning curve of the four:** ownership and lifetimes take weeks to internalise; compile times are slow.
- The training/research ecosystem is young (Candle, Burn) next to PyTorch's universe.
- Iteration speed is the slowest of the four — wrong tool for experiments and demos.
- Hiring pool is the smallest; every Rust component is a long-term maintenance commitment.

**Choose Rust when:** the bottleneck is proven and expensive — inference hot paths, vector search, tokenisers, data engines, WASM/edge/on-device ML — or when memory safety is a hard requirement. Earn Rust with measurements; never adopt it on fashion.

Side by Side

## Comparison table

| Dimension | Python | TypeScript | Go | Rust |
| --- | --- | --- | --- | --- |
| AI home layer | Training, research, data | Products, agents, UI | Infra, gateways, ops | Inference internals, performance |
| Speed | Slow (fast via native libs) | Moderate (JIT) | Fast (native, GC) | Fastest (native, no GC) |
| Type safety | Optional hints | Strong (compile-time) | Strong, simple | Strongest (memory + types) |
| Concurrency | Weak CPU, OK I/O async | Async I/O, single-thread core | Excellent (goroutines) | Excellent (fearless concurrency) |
| ML ecosystem | ★★★★★ definitive | ★★★ SDKs, browser ML | ★★ clients only | ★★★ growing (Candle, Burn) |
| Time to first demo | Fastest | Fast | Moderate | Slowest |
| Deployment | Environments, containers | Web / Node / edge, trivial | Single binary, trivial | Single binary / WASM |
| Signature AI artefact | PyTorch, HF Transformers | Vercel AI SDK, MCP SDK | Ollama, K8s AI operators | Qdrant, Tokenizers, Polars |
| Biggest risk | Performance / GIL at scale | CPU-heavy work | No ML libraries | Learning curve, iteration speed |

How Real Systems Combine Them

## One product, four languages — a worked architecture

Imagine a production AI platform — a document-intelligence SaaS with chat, agents, and an API:

1. **TypeScript** — the web app (streaming chat, review UI), the public API, agent orchestration, tool calling, and the MCP server exposing the product to other agents.
2. **Python** — offline model fine-tuning for extraction quality, the evaluation harness that gates every release, dataset curation jobs, and a FastAPI extraction service using Pydantic schemas.
3. **Go** — the LLM gateway in front of three providers (budgets, routing, fallbacks, audit), the high-volume document-ingestion pipeline, and the Kubernetes operator managing GPU nodes.
4. **Rust** — inside the stack you bought or built: Qdrant for vector search, the HF tokeniser inside the Python services, Polars for data prep — plus a custom Rust WASM module doing on-device redaction in the browser before text ever leaves the user's machine.

Nobody “chose four languages”. Each layer chose the tool whose strengths matched its bottleneck, and the boundaries are APIs and schemas — which is why typed contracts (Pydantic, Zod, protobuf) matter more than any single language.

**Boundary rule:** languages meet at contracts, never at shared memory. Define the schema once (JSON Schema / protobuf / OpenAPI), generate or validate types on both sides, and any layer can be rewritten in another language without drama.

Decision Guide

## Choosing, in five questions

1. **Are you creating or improving a model?** → Python. Non-negotiable today.
2. **Are you building what a user sees and clicks?** → TypeScript.
3. **Is the hard part thousands of concurrent requests, gateways, or platform plumbing?** → Go.
4. **Is the hard part a measured hot path, memory limit, or safety guarantee?** → Rust.
5. **More than one answer?** → You have a layered system. Assign per layer, connect with schemas, and resist rewriting a working layer for purity.

### Learning path, if you want all four

- **Python first** (weeks): NumPy/pandas intuition, PyTorch basics, one fine-tune, FastAPI + Pydantic.
- **TypeScript second** (weeks): strict mode, Zod, one RAG app, one agent with tools, streaming UI.
- **Go third** (days–weeks): goroutines, one streaming LLM gateway, one ingestion worker. Go is deliberately quick to learn.
- **Rust last, targeted** (months, ongoing): ownership first, then one real component — a tokeniser-speed benchmark, a Candle inference demo, or a WASM module — not a rewrite of everything.

**Final takeaway:** Python makes models, TypeScript products them, Go operates them, Rust accelerates them. Senior AI engineering is not loyalty to a language — it is knowing which layer you are in, and reaching for the tool that layer rewards.

Four Languages for AI — Python, TypeScript, Go & Rust • Prepared for Ranadhir Ghosh • November 11, 2026 • Companion: “TypeScript for AI” (sent earlier today)

Code examples are illustrative teaching patterns; verify current library APIs in official docs before production use.
