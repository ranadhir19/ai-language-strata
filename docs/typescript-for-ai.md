> Markdown conversion of the companion HTML guide. The original styled version is in [docs/html/typescript-for-ai.html](html/typescript-for-ai.html).

TypeScript for AI — A Comprehensive Learning & Tutorial Guide

 Learning GuideTutorialAI Engineering

# TypeScript for AI

How TypeScript became one of the most practical languages for building real AI products — LLM applications, agents, RAG systems, AI APIs, and full-stack AI platforms — and when you should (and should not) use it.

Prepared for Ranadhir Ghosh • November 11, 2026 • A comprehensive, self-contained tutorial

Start Here

## What this guide covers

TypeScript is JavaScript with a static type system. That one sentence understates its importance. In modern AI engineering, most of the *product layer* — the user interface, API, agent orchestration, tool calling, streaming, evaluation harness, and integration glue — is increasingly written in TypeScript, even when model training itself stays in Python.

This guide teaches TypeScript from the ground up, then shows exactly where it fits in the AI stack: calling LLMs safely, building agents that cannot pass malformed arguments to tools, validating structured outputs, streaming tokens to a UI, connecting vector databases, building MCP servers, and shipping production AI systems on Node.js, browsers, and the edge.

**The core idea:** AI systems are probabilistic. Your application code around them should not be. TypeScript gives you contracts — for prompts, tool inputs, model outputs, API payloads, and state — so failures are caught at compile time instead of in production.

### Who this is for

- Engineers who know some JavaScript or another language and want TypeScript properly, not just syntax tips.
- AI builders moving from Python notebooks to production products.
- Architects deciding between Python, TypeScript, or a hybrid stack for an AI system.

### How to use this tutorial

1. Read Part 1–2 for the mental model.
2. Type every code example yourself — do not just read them.
3. Do the exercises at the end of each major section.
4. Build the three capstone projects in Part 6.

Part 1 — The Case

## 1. Why TypeScript matters now

### 1.1 JavaScript won distribution; TypeScript won maintainability

JavaScript runs everywhere: browsers, Node.js servers, mobile (React Native), desktop (Electron), and edge runtimes (Cloudflare Workers, Vercel Edge, Deno). That ubiquity made it the default language for product interfaces. But large JavaScript codebases become fragile: a function expects `{ userId: string }`, someone passes a number, and nothing fails until runtime.

TypeScript adds static types that are erased at compile time — you get safety during development with zero runtime cost. The compiler, editor autocomplete, and refactoring tools become a second pair of eyes on every change.

### 1.2 The five superpowers

#### 1. Contracts

Interfaces describe exactly what data a function, API, tool, or model must receive and return.

#### 2. Refactoring confidence

Rename a field and the compiler finds every broken call site instantly.

#### 3. Editor intelligence

Autocomplete for SDKs (OpenAI, Anthropic, LangChain, Vercel AI SDK) is dramatically better with types.

#### 4. Safer JSON

AI is JSON in, JSON out. TypeScript + a validator (Zod) turns untrusted JSON into trusted data.

#### 5. Full-stack unity

One language and one set of types shared between frontend, backend, and edge.

### 1.3 A 30-second example

```
// JavaScript — this bug ships silently
function charge(user, amount) { return user.id + amount; }
charge({ id: "u1" }, "10"); // "u110" — string concatenation, not addition

// TypeScript — the compiler stops both errors
function charge(user: { id: string }, amount: number): string {
  return `${user.id}:${amount.toFixed(2)}`;
}
charge({ id: "u1" }, "10"); // ❌ Error: string is not assignable to number
```

Part 2 — Foundations

## 2. TypeScript foundations, properly

### 2.1 Setup in 2 minutes

```
npm init -y
npm install -D typescript tsx @types/node
npx tsc --init
# Run a file directly during learning:
npx tsx src/index.ts
# Build for production:
npx tsc
```

Key `tsconfig.json` settings to turn on from day one: `"strict": true`, `"noUncheckedIndexedAccess": true`, `"exactOptionalPropertyTypes": true` (when your team can handle it), and `"module": "NodeNext"` for modern Node projects.

### 2.2 Basic types and inference

```
let model: string = "gpt-5.1";
let temperature: number = 0.2;
let streaming: boolean = true;
let tags: string[] = ["rag", "agents"];

// Inference: TypeScript already knows these types — don't annotate everything
const maxTokens = 1024;              // number (literal context matters)
const config = { model, temperature }; // { model: string, temperature: number }

// Avoid `any`. Prefer `unknown` for data you haven't validated yet.
let modelReply: unknown = JSON.parse(rawText);
```

**Rule:** `any` turns the compiler off. `unknown` keeps it on — you must prove what the data is before using it. Almost all AI I/O should start as `unknown`.

### 2.3 Interfaces, type aliases, and unions

```
interface ChatMessage {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  name?: string; // optional
}

type ModelProvider = "openai" | "anthropic" | "google" | "azure-openai";

type Result<T> =
  | { ok: true; value: T }
  | { ok: false; error: string };

const msg: ChatMessage = { role: "user", content: "Explain RAG simply." };
```

**Discriminated unions** (like `Result` above) are one of TypeScript's most valuable patterns for AI: the compiler forces you to handle success and failure separately. No more forgetting the error branch.

### 2.4 Functions, generics, and narrowing

```
function first<T>(items: readonly T[]): T | undefined {
  return items[0];
}
const firstTag = first(tags); // string | undefined — handled honestly

function isChatMessage(value: unknown): value is ChatMessage {
  return typeof value === "object" && value !== null
    && "role" in value && "content" in value;
}
```

### 2.5 Classes, async, and errors

```
class TokenBudget {
  constructor(private readonly limit: number) {}
  private used = 0;
  spend(n: number): void {
    if (this.used + n > this.limit) throw new Error("Token budget exceeded");
    this.used += n;
  }
  get remaining(): number { return this.limit - this.used; }
}

async function withRetry<T>(fn: () => Promise<T>, tries = 3): Promise<T> {
  let last: unknown;
  for (let i = 0; i < tries; i++) {
    try { return await fn(); } catch (e) { last = e; }
  }
  throw last;
}
```

### 2.6 The type tools you will use daily

| Utility | What it does | AI example |
| --- | --- | --- |
| Partial<T> | All fields optional | Patching a prompt template |
| Pick<T, K> | Keep selected fields | Exposing only safe user fields to a model |
| Omit<T, K> | Remove fields | Stripping secrets before logging |
| Record<K, V> | Dictionary type | Model-name → pricing table |
| Awaited<T> | Unwrap a Promise | Typing async tool results |
| z.infer<typeof schema> | Type from a Zod schema | One source of truth for validation + types |

Part 3 — Hands-On Tutorial

## 3. Tutorial: a type-safe LLM call, step by step

**Goal:** call a model, force a structured answer, validate it, and handle every failure mode — with the compiler proving you did.

### Step 1 — Define the contract first

```
import { z } from "zod";

export const SummarySchema = z.object({
  title: z.string().min(3),
  bullets: z.array(z.string()).min(1).max(5),
  sentiment: z.enum(["positive", "neutral", "negative"]),
  confidence: z.number().min(0).max(1),
});
export type Summary = z.infer<typeof SummarySchema>;
```

### Step 2 — Call the model for JSON, then validate (never trust)

```
async function summarise(text: string): Promise<Summary> {
  const raw = await callModel({ // your provider SDK call
    system: "Return ONLY JSON matching the requested schema.",
    user: text,
    responseFormat: "json",
  });
  const parsed: unknown = JSON.parse(raw);
  return SummarySchema.parse(parsed); // throws a precise error if the model drifted
}
```

### Step 3 — Stream to a user interface safely

```
// Vercel AI SDK pattern (illustrative)
import { streamText } from "ai";
import { openai } from "@ai-sdk/openai";

export async function POST(req: Request) {
  const { prompt }: { prompt: string } = await req.json();
  const result = streamText({ model: openai("gpt-5.1"), prompt });
  return result.toTextStreamResponse(); // token-by-token streaming to the browser
}
```

**Lesson:** Notice the order — contract → call → validate → present. Reversing it (trusting raw model output) is the #1 cause of brittle AI apps.

Part 4 — The Core of This Guide

## 4. How TypeScript is used in AI — in depth

### 4.1 LLM application layer (the biggest use)

Chatbots, copilots, support agents, document Q&A, summarisation, extraction, classification, and code assistants are mostly *software around an API*. TypeScript dominates this layer because the official and community SDKs are excellent: OpenAI, Anthropic, Google Gemini, Azure OpenAI, Cohere, Mistral, plus the Vercel AI SDK and LangChain.js. Typed SDKs mean model names, message shapes, tool schemas, and streaming events autocomplete in your editor and break loudly when a provider changes an API.

### 4.2 AI agents and tool calling — where types save you

An agent is a loop: model → chooses a tool → your code runs it → result goes back to the model. The danger point is the tool boundary: a model can hallucinate argument names, types, or values. In TypeScript you define each tool once — schema + implementation + inferred type — and the framework validates every model-proposed call before it executes.

```
import { tool } from "ai";
import { z } from "zod";

export const getWeather = tool({
  description: "Get current weather for a city",
  inputSchema: z.object({
    city: z.string(),
    units: z.enum(["celsius", "fahrenheit"]).default("celsius"),
  }),
  execute: async ({ city, units }) => {
    // `city` and `units` are fully typed here — no guessing, no any
    return { city, units, temp: 21, condition: "sunny" };
  },
});
```

Use this pattern for database lookups, calculators, CRM actions, ticket creation, web search, and code execution wrappers. **Never execute a raw model-generated call without schema validation.**

### 4.3 RAG (Retrieval-Augmented Generation)

A typical TypeScript RAG pipeline: ingest documents (loaders, chunking) → embed (provider SDK) → store (Pinecone, Weaviate, Qdrant, pgvector via Prisma/Drizzle, Turbopuffer) → retrieve with typed filters → assemble a typed prompt context → answer with citations. TypeScript is ideal here because ingestion jobs, the API, and the chat UI are one codebase sharing the same `Chunk`, `Document`, and `Citation` types — a field renamed in the store breaks the UI build immediately, not in production.

### 4.4 Structured outputs and data extraction

Invoice parsing, resume screening, medical-note structuring, lead qualification, evaluation scoring — all reduce to "unstructured in, trustworthy JSON out." The TypeScript pattern is Zod schema → JSON Schema for the model → parse → typed downstream code (database insert, workflow trigger). This is arguably TypeScript's single most valuable AI role.

### 4.5 AI backends, APIs, and streaming infrastructure

Node.js (Fastify, NestJS, Hono, Express) and edge runtimes are natural homes for AI APIs: they stream well (SSE / WebSockets), handle many concurrent long-running model calls with async I/O, deploy cheaply, and share types with the frontend. NestJS + TypeScript is a common enterprise choice; Hono + TypeScript is a common edge choice.

### 4.6 Frontend AI experiences

Streaming chat UIs, token-by-token rendering, optimistic updates, voice interfaces, and in-browser inference all live in TypeScript/React (or React Native). Libraries: Vercel AI SDK UI hooks (`useChat`, `useCompletion`), LangChain callbacks, and assistant-ui. No other language can do this layer at all — the browser speaks JavaScript/TypeScript.

### 4.7 TensorFlow.js and in-browser / on-device ML

TensorFlow.js, ONNX Runtime Web, Transformers.js (Hugging Face), and MediaPipe let you run real models — classification, embeddings, sentiment, image models, small LLMs — directly in the browser or Node, with privacy (data never leaves the device), zero server cost, and offline capability. Teachable examples: a client-side toxicity filter before sending text to a paid API, or on-device embeddings for a private notes app.

### 4.8 MCP servers and AI tooling

The Model Context Protocol's reference SDK is TypeScript-first. Most MCP servers — tools that expose databases, filesystems, APIs, and SaaS apps to Claude, ChatGPT, and other agents — are written in TypeScript and published via npm/npx. If you build tools *for* agents (not just with them), TypeScript is the default.

### 4.9 Evaluation, observability, and guardrails

Type-safe eval harnesses (promptfoo — itself TypeScript, LangSmith JS, Braintrust), structured logging of typed traces, cost accounting per model/feature, and guardrail middleware (input validation, PII redaction, output schema checks) are all commonly TypeScript in product teams, because they sit next to the product code they measure.

### 4.10 Full-stack AI platforms and SaaS

Put it together and you get the modern AI SaaS shape: Next.js / Remix frontend + TypeScript API + Postgres/pgvector + a Python microservice *only where needed* (heavy training, specialised libraries). Companies choose this because one typed codebase is faster for small teams to change safely — and AI products change weekly.

Part 5 — Judgement

## 5. When to use TypeScript — and when not to

| Use TypeScript when… | Prefer Python (or another tool) when… |
| --- | --- |
| Building a user-facing AI product, chat UI, or copilot | Training or fine-tuning models (PyTorch, JAX, HF Trainer) |
| Agent orchestration, tool calling, workflow glue | Heavy data science, notebooks, statistical analysis (pandas, NumPy) |
| RAG product layer, APIs, streaming, edge deployment | Research prototyping where library coverage matters most |
| Structured extraction that feeds databases / workflows | Classical ML pipelines (scikit-learn, XGBoost) and MLOps training jobs |
| MCP servers and tools for agents | GPU-heavy inference you self-host (vLLM ecosystem is Python-centric) |
| Browser / on-device ML (TensorFlow.js, Transformers.js) | One-off analysis where type safety buys nothing |

**The production answer is usually hybrid:** Python for training, data science, and specialised ML services; TypeScript for everything the user touches and everything that orchestrates models. They communicate over HTTP/gRPC with — ideally — schemas generated from a single contract.

### Common mistakes

- Using `any` for model outputs instead of `unknown` + validation.
- Trusting a model's JSON because it "usually works" — validate every time; models drift.
- Putting business logic in prompts that belongs in typed code (pricing, permissions, eligibility).
- No token/cost budget type or guard — a runaway agent loop is a billing incident.
- Ignoring streaming UX: users forgive latency they can watch; they don't forgive a spinner.
- Skipping evals because the demo worked. Type the eval dataset like you type the app.

### Architecture pattern: the typed AI sandwich

1. **Typed input boundary** — validate user/API input with Zod.
2. **Typed context assembly** — retrieval results and memory as defined interfaces, never string soup by accident.
3. **Model call** — typed SDK, explicit model, temperature, and budget parameters.
4. **Typed output boundary** — schema-validate structured output; treat free text as untrusted display data.
5. **Typed actions** — tools and side-effects only through validated, permission-checked functions.
6. **Traces** — log the typed shapes (redacted) so evals and debugging are possible.

Part 6 — Build

## 6. Three capstone projects

#### Project 1 — Type-Safe Document Q&A (RAG)

Ingest PDFs, chunk and embed them, store in pgvector, answer with typed citations. Skills: ingestion pipelines, embeddings, retrieval, citation types shared API↔UI. Stretch: add a confidence field to the answer schema and refuse below a threshold.

#### Project 2 — Tool-Using Support Agent

An agent with three Zod-validated tools (order lookup, refund eligibility — computed in code, never by the model — and ticket creation), a token budget class, and full trace logging. Skills: tool calling, guardrails, agent loops. Stretch: add human approval before the refund tool executes.

#### Project 3 — Structured Extraction Service

An API that turns invoices or resumes into validated JSON, stores them via a typed ORM, and exposes a review UI. Skills: structured outputs, error queues for failed parses, evals on a labelled set. Stretch: measure extraction accuracy before/after a prompt change — with a typed eval harness.

Part 7 — Practice

## 7. Exercises (do these, in order)

1. Convert a JavaScript file you own to TypeScript with `strict: true` and fix every error without using `any`.
2. Model an LLM conversation as a discriminated union so an assistant message *must* have either text or tool calls — never neither.
3. Write a Zod schema for a job-posting extraction (title, company, salary range, remote flag) and validate 10 real model outputs against it. Log every failure mode.
4. Build the `withRetry` + `TokenBudget` utilities from §2.5 into an agent loop and deliberately exhaust the budget.
5. Stream a model response to a web page with the Vercel AI SDK; then add a typed status indicator (connecting / streaming / done / error).
6. Write one MCP server exposing a single read-only tool (e.g., search your own notes) and call it from an MCP client.
7. Run one model in the browser with Transformers.js (sentiment or embeddings) and compare latency/privacy against the API version.

### Further learning

- TypeScript Handbook (typescriptlang.org) — the official, excellent source; do the "Everyday Types" and "Narrowing" chapters twice.
- Total TypeScript (Matt Pocock) — the best advanced-types training.
- Vercel AI SDK docs, LangChain.js docs, and the MCP TypeScript SDK — read them as worked examples of large typed APIs.
- Zod documentation — validation is half of practical TypeScript-for-AI.
- TensorFlow.js and Transformers.js guides for the on-device path.

**Final takeaway:** Learn Python to understand models. Learn TypeScript to ship AI products people can use, trust, and pay for. The strongest AI engineers in 2026 are fluent in the boundary between the two — and TypeScript is how that boundary is made safe.

TypeScript for AI — Comprehensive Learning & Tutorial Guide • Prepared for Ranadhir Ghosh • November 11, 2026

Code examples are illustrative teaching patterns; check your provider SDK's current docs for exact model names and API signatures before production use.
