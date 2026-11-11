# IP & Legal Compliance Note — ai-language-strata

Recorded 2026-11-11, before first publication.

## Name
- Chosen name: **ai-language-strata**.
- Collision check (2026-11-11): GitHub repository search `ai-language-strata in:name` returned **0 repositories** (zero exact-name matches). Candidates were checked in order; `ai-language-strata` was the first candidate and passed, so later candidates were not needed.
- Web/product check (2026-11-11): web search for the exact hyphenated name `"ai-language-strata"` returned **no product, company, or project using that exact name**. Unrelated products use the single generic word "Strata" (a local model runner, an enterprise platform, network tooling); none uses this repo's full name, and this repo does not use their branding, copy, or assets.
- The name is descriptive of the repo's own original framing (AI systems as language strata/layers) and is distinctive within the owner's portfolio.

## Originality
- Both guides were written as original tutorial content for the owner (first published to the owner as standalone HTML documents on 2026-11-11); the Markdown files are faithful conversions of those originals, and the HTML originals are included unchanged.
- All four example programs are original teaching code written for this repository. They implement well-known, generic patterns (schema validation, tool dispatch, an HTTP streaming handler, cosine similarity) from first principles; no third-party code was copied.
- No reference product was cloned in name, copy, structure, or code. Where real systems are named (e.g. Qdrant, Ollama, Polars, Candle), they are cited as facts about the ecosystem, with no assets, logos, or text reproduced.

## Licence
- This repository: MIT, © 2026 Ranadhir Ghosh (see LICENSE).
- Third-party dependencies: **none by design**. Every example uses only its language's standard library (the Python example optionally uses pydantic if already installed, and works without it). Nothing to attribute.

## Secrets / internal references
- No secrets, keys, tokens, or credentials exist anywhere in this repository; examples use mock/local data only and need no API keys.
- The full tree was scanned before publication with the owner's reference scanner as part of `validate.py` (stage 6): **no employer references anywhere in the content**. The scanner's only candidate hits in the tree are the harness's own references to the scanning mechanism inside `validate.py` itself (the stage name and the scanner's file path) — judged benign in context, since a harness cannot run the mandated scan without naming it; the harness encodes that judgement explicitly and still fails on any candidate in any content file.
- The content contains no employer references and no personal data beyond the author's own name in the licence and byline.
