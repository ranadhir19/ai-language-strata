//! Cosine-similarity vector search — Rust's AI-layer strength.
//!
//! Layer: inference & serving internals (Layer 3/6 of the guide's map).
//! Retrieval is arithmetic: embed everything once, then, per query,
//! score every stored vector and return the nearest few. That inner
//! loop decides the latency of every RAG product built on top of it,
//! which is why production vector databases (Qdrant is the Rust one)
//! live in this layer. This file is that idea in miniature — the same
//! cosine scoring Qdrant performs, over a handful of in-memory vectors,
//! with no dependencies, no garbage collector, and errors as values.
//!
//! Compile & run (no cargo needed):
//!     rustc -O vector_search.rs -o vector_search && ./vector_search
//! The program ends with assertions: it is a self-check, not just a demo.

use std::cmp::Ordering;

/// Cosine similarity of two equal-length vectors.
/// Returns None — an explicit, typed absence — for a zero vector or a
/// dimension mismatch, instead of a NaN quietly poisoning the ranking.
fn cosine(a: &[f32], b: &[f32]) -> Option<f32> {
    if a.len() != b.len() {
        return None;
    }
    let mut dot = 0.0f32;
    let mut norm_a = 0.0f32;
    let mut norm_b = 0.0f32;
    for i in 0..a.len() {
        dot += a[i] * b[i];
        norm_a += a[i] * a[i];
        norm_b += b[i] * b[i];
    }
    let denom = norm_a.sqrt() * norm_b.sqrt();
    if denom == 0.0 {
        return None;
    }
    Some(dot / denom)
}

/// A stored document: an id plus its embedding.
struct Doc {
    id: &'static str,
    text: &'static str,
    embedding: Vec<f32>,
}

/// Score every document against the query and return the top `k`
/// (id, score) pairs, best first — brute force, the honest baseline
/// an approximate index (HNSW) is measured against.
fn search<'a>(docs: &'a [Doc], query: &[f32], k: usize) -> Vec<(&'a str, f32)> {
    let mut scored: Vec<(&str, f32)> = docs
        .iter()
        .filter_map(|d| cosine(&d.embedding, query).map(|s| (d.id, s)))
        .collect();
    scored.sort_by(|x, y| y.1.partial_cmp(&x.1).unwrap_or(Ordering::Equal));
    scored.truncate(k);
    scored
}

fn main() {
    // Toy 4-dimensional "embeddings" — in production these come from an
    // embedding model; here they are hand-placed so the expected ranking
    // is knowable and the assertions below mean something.
    let docs = vec![
        Doc {
            id: "python",
            text: "Python makes the models: training and research.",
            embedding: vec![0.95, 0.10, 0.05, 0.00],
        },
        Doc {
            id: "typescript",
            text: "TypeScript products the models: apps, agents, UI.",
            embedding: vec![0.10, 0.95, 0.10, 0.05],
        },
        Doc {
            id: "go",
            text: "Go operates the models: gateways and infrastructure.",
            embedding: vec![0.05, 0.10, 0.95, 0.10],
        },
        Doc {
            id: "rust",
            text: "Rust accelerates the models: fast internals.",
            embedding: vec![0.00, 0.05, 0.10, 0.95],
        },
    ];

    // A query "about building fast vector internals" — closest to rust.
    let query = [0.05, 0.10, 0.25, 0.95];
    let top = search(&docs, &query, 2);
    for (id, score) in &top {
        let doc = docs.iter().find(|d| d.id == *id).unwrap();
        println!("{:.4}  {} — {}", score, doc.id, doc.text);
    }

    // Self-checks: the nearest neighbour must be rust, python must be
    // last for this query, and the degenerate inputs must be None.
    assert_eq!(top[0].0, "rust", "nearest neighbour should be rust");
    let all = search(&docs, &query, 4);
    assert_eq!(all[3].0, "python", "python should rank last for this query");
    assert_eq!(cosine(&[0.0, 0.0], &[1.0, 1.0]), None);
    assert_eq!(cosine(&[1.0], &[1.0, 2.0]), None);
    println!("self-check PASS: ranking and edge cases correct");
}
