// Streaming LLM gateway — Go's AI-layer strength.
//
// Layer: platform & infrastructure (Layer 6 of the guide's map).
// The traffic-cop layer of production AI is a service in front of model
// providers: it accepts many concurrent requests, gives each one a hard
// timeout, streams tokens back as they arrive, and stays cheap while
// doing it — most of the time it is just waiting on a slow model.
// That shape is exactly what Go was built for: one goroutine per
// request, contexts for cancellation, and a single static binary out.
//
// This is a minimal, stdlib-only version: a /generate endpoint that
// streams tokens from a local mock "model" (no API keys, no network),
// with a per-request deadline enforced by context. Point the mock at a
// real provider client and the handler shape does not change.
//
// Run:  go run gateway.go        then:  curl -N localhost:8080/generate
// Or:   go run gateway.go -selftest   (in-process test, no server)
package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"net/http/httptest"
	"strings"
	"time"
)

// mockModel stands in for an upstream LLM provider. It emits tokens on a
// channel until it is done or the caller's context is cancelled — the
// same contract a real streaming client exposes.
func mockModel(ctx context.Context, prompt string) <-chan string {
	out := make(chan string)
	go func() {
		defer close(out)
		tokens := []string{"Go ", "holds ", "the ", "door ", "while ",
			"the ", "model ", "thinks."}
		for _, tok := range tokens {
			select {
			case <-ctx.Done():
				return // client gone or deadline hit: stop spending
			case out <- tok:
				time.Sleep(50 * time.Millisecond)
			}
		}
	}()
	return out
}

// generateHandler streams one response per request. Every request gets
// its own goroutine from the HTTP server and its own deadline context;
// thousands of these can be in flight at once, nearly all of them
// blocked on the model, costing a few KB of stack each.
func generateHandler(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming unsupported", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")

	prompt := r.URL.Query().Get("prompt")
	for tok := range mockModel(ctx, prompt) {
		fmt.Fprint(w, tok)
		flusher.Flush()
	}
	if ctx.Err() == context.DeadlineExceeded {
		log.Printf("request for %q hit its deadline", prompt)
	}
}

// selfTest exercises the handler in-process: it asserts a full streamed
// response arrives, so `go run gateway.go -selftest` is a real check,
// not a demo that merely looks right.
func selfTest() {
	req := httptest.NewRequest(http.MethodGet, "/generate?prompt=hi", nil)
	rec := httptest.NewRecorder()
	generateHandler(rec, req)
	body := rec.Body.String()
	want := "Go holds the door while the model thinks."
	if !strings.Contains(body, want) {
		log.Fatalf("self-test FAIL: got %q, want it to contain %q", body, want)
	}
	fmt.Println("self-test PASS: streamed response complete:", body)
}

func main() {
	self := flag.Bool("selftest", false, "run the in-process self-test and exit")
	flag.Parse()
	if *self {
		selfTest()
		return
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/generate", generateHandler)
	addr := ":8080"
	log.Printf("mock LLM gateway listening on %s (try: curl -N 'localhost%s/generate?prompt=hi')", addr, addr)
	log.Fatal(http.ListenAndServe(addr, mux))
}
