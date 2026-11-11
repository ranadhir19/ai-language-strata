/**
 * Validated tool calling — TypeScript's AI-layer strength.
 *
 * Layer: agent & application logic (Layer 4 of the guide's map).
 * An agent is a loop in which a model proposes tool calls. The danger
 * point is the tool boundary: a model can hallucinate argument names,
 * types, or values. This example defines one tool the way production
 * TypeScript does — a Zod schema as the single source of truth, the
 * argument type inferred from it, and a dispatcher that validates
 * every model-proposed call before anything executes.
 *
 * It is dependency-free by design: the `Schema` mini-validator below
 * plays the exact role Zod plays in a real project (parse unknown
 * input, return typed data or a precise error), so the file runs with
 * no npm install. In production you would swap it for zod and keep
 * every other line — see docs/typescript-for-ai.md, section 4.2.
 *
 * Run with tsx:   npx tsx tool_call.ts
 * Or type-check:  npx tsc --noEmit --strict tool_call.ts
 */

// ---------------------------------------------------------------------------
// A minimal schema validator with the same contract as z.object(...).parse()
// ---------------------------------------------------------------------------

type ParseResult<T> =
  | { ok: true; value: T }
  | { ok: false; error: string };

interface Schema<T> {
  parse(input: unknown): ParseResult<T>;
}

const stringMatching = (pattern: RegExp, label: string): Schema<string> => ({
  parse(input) {
    if (typeof input !== "string")
      return { ok: false, error: `${label}: expected a string` };
    if (!pattern.test(input))
      return { ok: false, error: `${label}: "${input}" does not match ${pattern}` };
    return { ok: true, value: input };
  },
});

function objectSchema<S extends Record<string, Schema<unknown>>>(
  shape: S,
): Schema<{ [K in keyof S]: S[K] extends Schema<infer T> ? T : never }> {
  type Out = { [K in keyof S]: S[K] extends Schema<infer T> ? T : never };
  return {
    parse(input) {
      if (typeof input !== "object" || input === null)
        return { ok: false, error: "tool arguments must be an object" };
      const record = input as Record<string, unknown>;
      const value = {} as Record<string, unknown>;
      for (const key of Object.keys(shape)) {
        const r = shape[key].parse(record[key]);
        if (!r.ok) return { ok: false, error: r.error };
        value[key] = r.value;
      }
      return { ok: true, value: value as Out };
    },
  };
}

// ---------------------------------------------------------------------------
// One tool, defined once: description + input schema + implementation.
// The Args type is *inferred* from the schema — it can never drift from it.
// ---------------------------------------------------------------------------

const orderLookupSchema = objectSchema({
  orderId: stringMatching(/^ORD-\d+$/, "orderId"),
});

type OrderLookupArgs = typeof orderLookupSchema extends Schema<infer T>
  ? T
  : never;

interface ToolDef<A> {
  name: string;
  description: string;
  schema: Schema<A>;
  execute: (args: A) => Promise<unknown>;
}

const lookupOrder: ToolDef<OrderLookupArgs> = {
  name: "lookup_order",
  description: "Look up an order by its id (ORD-<digits>)",
  schema: orderLookupSchema,
  execute: async ({ orderId }) => {
    // A local stand-in for a database call. `orderId` here is proven
    // typed and pattern-checked — no defensive re-validation needed.
    const orders: Record<string, { status: string; total: number }> = {
      "ORD-1042": { status: "shipped", total: 184.5 },
    };
    return orders[orderId] ?? { status: "not_found", total: 0 };
  },
};

// ---------------------------------------------------------------------------
// The dispatcher: the only path from a model proposal to execution.
// ---------------------------------------------------------------------------

async function dispatchToolCall(
  tools: ToolDef<never>[],
  call: { name: string; arguments: unknown },
): Promise<ParseResult<unknown>> {
  const tool = tools.find((t) => t.name === call.name);
  if (!tool) return { ok: false, error: `unknown tool: ${call.name}` };
  const parsed = tool.schema.parse(call.arguments);
  if (!parsed.ok)
    return { ok: false, error: `invalid arguments for ${call.name}: ${parsed.error}` };
  const value = await tool.execute(parsed.value as never);
  return { ok: true, value };
}

// ---------------------------------------------------------------------------
// Demo: one good call, and the two classic model mistakes — both refused
// before execution, with errors a model (or a log) can act on.
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const tools = [lookupOrder] as unknown as ToolDef<never>[];

  const good = await dispatchToolCall(tools, {
    name: "lookup_order",
    arguments: { orderId: "ORD-1042" },
  });
  console.log("good call  ->", JSON.stringify(good));

  const badShape = await dispatchToolCall(tools, {
    name: "lookup_order",
    arguments: { order_id: 1042 }, // hallucinated name + wrong type
  });
  console.log("bad shape  ->", JSON.stringify(badShape));

  const badValue = await dispatchToolCall(tools, {
    name: "lookup_order",
    arguments: { orderId: "DROP TABLE orders" }, // not an order id at all
  });
  console.log("bad value  ->", JSON.stringify(badValue));

  if (!good.ok || badShape.ok || badValue.ok) {
    throw new Error("self-check failed: dispatcher contract broken");
  }
  console.log("self-check PASS: valid call executed, both invalid calls refused");
}

void main();
