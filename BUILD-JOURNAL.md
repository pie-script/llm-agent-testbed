# Build Journal — LLM Agent Security Testbed

This is the "how it actually went" file — the decisions that changed
mid-build, mistakes caught along the way, and open challenges. The
[README](./README.md) documents the finished architecture; this
documents the process that got there, including the parts that didn't
go smoothly on the first try. Kept separate on purpose — a design
doc shouldn't have to carry the archaeology of how it was built.

---

## Phase 0 — Getting tool-calling working

**What changed mid-build:** the plan originally assumed Anthropic's API
end to end, using the request/response shape (`stop_reason: "tool_use"`,
`input` field) as the reference example. Switched to Google's Gemini
API partway through, once a Gemini API key (free tier) turned out to
already be available. This meant re-deriving the equivalent concepts
under different names:

| Concept | Anthropic | Gemini |
|---|---|---|
| Signal that a tool was requested | `stop_reason: "tool_use"` | presence of `part.function_call` |
| Tool arguments | `input` | `function_call.args` |
| Tool schema wrapper | plain dict w/ `input_schema` | `types.FunctionDeclaration` |

**A real gotcha:** the model name used in the first working script
(`gemini-2.5-flash`) was already stale by the time of actually building
— the live rate-limit dashboard showed `gemini-3.6-flash` as the current
model. Model names in this space move fast enough that hardcoding one
from memory/older docs is a real risk — always worth checking the
live dashboard or docs immediately before, not assuming a name from a
few months back is still current.

**Free tier limits, checked directly rather than trusted from search
results:** blog posts guessing at Gemini's free-tier RPM/RPD numbers
were unreliable — actual numbers (checked live in AI Studio) came out
to roughly 5 RPM / 20 RPD for `gemini-3.6-flash`, tighter than several
third-party estimates suggested. This directly shaped later phases —
Phase 6's batch testing had to be planned around a ~20/day ceiling
rather than assumed to be effectively unlimited.

---

## Phase 1 — Planning

**One real design correction:** the original instinct for the grading
approach was to build all three grading methods (keyword-matching,
LLM-as-judge, tool-argument inspection) simultaneously in v1, each as
"one view" of the same result. Corrected to: build ONE method
completely first (tool-argument inspection, per the project's own
notes calling it the most reliable), prove the whole pipeline works
end to end, and only then fork into separate copies for the other two
methods. Same lesson as the header scanner's `RULES` table — one rule
working correctly before writing the other five, not five in parallel
and debugging none of them cleanly.

---

## Phase 2 — Data model

**A genuine confusion worth being honest about:** partway through this
phase, the header-scanner-era distinction between "rule" (static
definition) and "finding" (per-run outcome) turned out to be blurrier
in memory than expected — a review pass showed real uncertainty about
*why* `HeaderRule` and `HeaderFinding` were two separate classes rather
than one. Rather than push through a memory-test on the old project,
the correct call was pausing to confirm the *current* project's
equivalent distinction (`AttackAttempt` vs `AttackResult`) was actually
understood fresh, rather than assuming the old pattern had fully
transferred. Worth naming honestly: syntax and design reasoning can
blur together when a lot of new material lands at once, and that's a
normal part of learning, not a sign of failure.

**The `target_secret` field** wasn't part of the original three-shape
sketch — it got added specifically because grading needs a
ground-truth value to compare against per-attack, and without it,
grading would have needed to awkwardly infer "what is this attack even
after" from the prompt text itself at grading time, rather than having
it declared up front.

---

## Phase 3 — Tool design

**A real design mistake caught before coding:** the first attempt at
`hardened_get_user`'s logic had a redundant, effectively-unreachable
branch —

```python
if user.restricted and user.role != "admin":
    return {"error": ...}
elif user.restricted and user.role == "admin":
    return {"error": ...}
```

— both branches tested `restricted` and returned identical errors; the
`role` check added nothing. Worse, the actual `else` branch still
returned `password` in the clear, directly contradicting the whole
point of the hardening (password should never be returned, regardless
of restriction status). Caught and corrected to two independent checks:
refuse entirely if `restricted`, and separately, never include
`password` in the field list at all for the success path — not "return
everything then try to delete a key," but "build the response by hand
without ever mentioning password."

**Why this bug mattered beyond just being wrong:** it's the exact shape
of bug a real security review needs to catch — a check that *looks*
sufficient (block restricted users) but silently leaves a second,
independent risk (ordinary users' passwords) completely open.

---

## Phase 4 — Wiring to Gemini

**First real end-to-end result, unprompted:** the naive tool, wired to
Gemini and asked an entirely benign question ("what role does alice
have?"), returned Alice's full record including her plaintext password
— with zero adversarial prompting involved. This was a useful, concrete
demonstration that "naive" doesn't require an attacker at all; it fails
by default the moment it's asked *anything* that touches the record.

**A conceptual gap surfaced and corrected:** when asked what would
happen if the follow-up API call sent only the tool's result with no
prior conversation context, the first answer given was "an API error" —
corrected to the more accurate (and more instructive) answer: the call
would likely still *succeed*, just produce a confused or generically
unhelpful response, since the model would have no context for what
question it was even answering. Silent-wrong is a sneakier failure mode
than a loud error, and it's the reason Phase 7 (manual spot-checking)
exists rather than trusting automated grading blindly.

---

## Phase 5 — Attack prompts

**A design gap found while writing the indirect-injection attack:** the
original `FakeUser` shape (from Phase 2) had no free-text field at all
— meaning there was nowhere for a planted injection payload to live.
This required going back and adding a `bio` field, then deciding
whether both tools should return it. Landed on: yes, both should —
`bio` isn't sensitive, and if the hardened tool stripped it too, the
indirect-injection attack would be untestable by construction, which
would hide a real finding rather than reveal one.

**An honest, still-open limitation:** the `chained_request` attack was
written assuming a multi-turn conversation (a "step 1, then step 2"
structure), but the actual test harness built in Phase 6 is single-shot
— one prompt in, one graded response out. The attack prompt exists in
`attacks.py`, but it won't be meaningfully tested until (or unless) the
harness is extended to support multi-message runs. Documented rather
than quietly ignored.

---

## Phase 6 — Testing (in progress)

**Quota-driven planning:** the free-tier ~20 requests/day limit on
`gemini-3.6-flash` directly shaped how testing is being sequenced —
rather than running the full 6-attack × 2-tool-version batch (12+ API
calls) in one go, the plan is: smoke-test the `run_attack()` function
against a single attack/tool pair first (cheap, ~2 calls), confirm the
harness's mechanics work correctly, and save the full batch run for a
day with fresh quota — rather than burning quota on iterative debugging
of the harness itself.

**A considered-and-rejected idea:** briefly considered dual-wiring the
harness to also run against the local Qwen2.5-Coder model (free,
unlimited) for cheap debugging. Decided against it for now — Qwen and
Gemini have different SDK shapes (OpenAI-compatible vs. `google-genai`),
so supporting both would mean building and maintaining two parallel
code paths just to save API quota during debugging, which wasn't worth
the added complexity at this stage. Local models also tend to be
easier to manipulate than frontier models, so results from Qwen
wouldn't have meant the same thing as results against the actual
target model anyway — worth keeping the target model consistent so the
eventual report measures one thing clearly, not two different things
under one label.

---

## Open questions / things to revisit later

- Does `chained_request` need real multi-turn harness support, or is a
  single well-crafted prompt an acceptable stand-in for v1?
- Once tool-argument inspection is fully proven out, is it worth
  actually forking keyword-matching and LLM-as-judge as comparison
  methods, or is one grading approach sufficient for the project's
  scope?
- Worth adding a second target model (a second frontier model, not a
  smaller local one) later, to see whether findings are Gemini-specific
  or hold more generally?
