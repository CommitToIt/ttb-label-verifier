# TTB Label Verifier

An AI-powered prototype that verifies alcohol label images against submitted application data, built for a federal compliance take-home assignment.

---

## For Reviewers: Try It in 30 Seconds

**Live URL:** https://ttb-label-verifier-afbl.onrender.com

No setup needed — the page loads with 8 example labels already added and filled in, each demonstrating a different part of the matching logic: exact matches, tolerated formatting differences (case, units, proof vs. percent), a deliberate brand mismatch, a missing required field, and two real photographed products (not synthetic renders).

1. Open the URL above
2. Click **Verify labels**
3. Review the color-coded pass/fail/needs-review results, each with a plain-language reason

Processing calls a live AI model for each image, so a batch of 8 takes roughly 10-15 seconds — the button shows "Verifying labels..." while it works.

**To test your own label instead:** click **Clear** to remove all pre-loaded examples, then drag in your own image(s) and fill in the application data. You can also remove a single example individually with that card's **Remove image** button, keeping the rest.

---

## Setup and Run Instructions (Local)

**Requirements:** Python 3.11+

```bash
git clone https://github.com/CommitToIt/ttb-label-verifier.git
cd ttb-label-verifier

python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the project root with your own Anthropic API key:
```
ANTHROPIC_API_KEY=your-key-here
```

Run it:
```bash
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/` in a browser.

Run the automated test suite:
```bash
pytest -q
```
(58 tests, all passing as of submission.)

---

## Approach and Tools Used

**Backend:** Python + FastAPI, a single service that serves both the API and the frontend — no separate frontend build step, no Docker. Deployed to Render's native Python runtime.

**Frontend:** Plain HTML, CSS, and JavaScript — no framework. This was a deliberate choice: the UI requirement was "extremely simple, no hunting for buttons," which a plain page satisfies fully, and it keeps the whole build free of a build step, making every visual iteration a simple file-edit-and-refresh rather than a rebuild.

**AI extraction:** The Claude API (`claude-sonnet-5`), using forced tool-use with a JSON schema derived from a Pydantic model — extraction comes back as structured, validated data rather than parsed freeform text.

**Matching logic**, field by field:
- **Brand name, class/type:** normalized (case-fold, whitespace collapse), auto-pass only on an exact match after normalization; otherwise routed to a fuzzy similarity score (needs-review ≥75%, fail below).
- **Bottler name/address, country of origin:** the same normalization plus a containment check — a submitted value that's a genuine substring of the label's (or vice versa) still passes, since real labels commonly include regulatory boilerplate ("Distilled, Aged & Bottled by...") the applicant wouldn't necessarily retype. Bottler addresses also get their trailing US state normalized between full name and abbreviation before comparing.
- **Alcohol content, net contents:** parsed as numbers with their unit (%, proof, mL, L, fl oz) and compared numerically with a small tolerance, rather than as text — this correctly treats "45% Alc./Vol. (90 Proof)" and "45%" as identical, and "750ML" and "750 mL" as identical.
- **Government warning text:** compared against a fixed statutory constant (not user-submitted data, since the warning is a legal requirement, not a claim) after case/whitespace normalization — this tolerates labels that print the entire statement in all caps, while still catching genuinely incorrect wording.
- **Government warning formatting:** a separate check confirming the "GOVERNMENT WARNING:" heading is rendered bold and in all caps, only evaluated once the text itself matches.

**Human-in-the-loop by design:** low-confidence extractions and borderline matches are flagged `needs-review`, never silently auto-passed or auto-rejected — a compliance officer makes the final call on ambiguous cases.

**Batch processing:** a single endpoint accepts a list of one or more image+data pairs (a single verification is just a list of one) and processes them with bounded concurrency (a shared API client, a semaphore limiting concurrent calls) rather than serially or unboundedly.

**Build process:** built incrementally with GitHub Copilot in Agent mode, staged into small, individually-tested pieces, with real local and live testing after every stage rather than trusting generated code on its summary alone.

---

## Testing

**58 automated tests** (`pytest`) covering matching rules for every field, upload validation, batch-size limits, concurrency and error isolation, and structured logging — run on every change.

**8 pre-loaded scenarios** on the live page, each demonstrating a specific, distinct behavior: a full pass, tolerated case differences, a warning-formatting violation, tolerated ABV formatting differences, a missing required field, a genuine brand mismatch, and two real photographed products.

**Real-world testing surfaced genuine gaps synthetic images couldn't.** Testing with actual photographed products — a bottle of Buffalo Trace bourbon and a can of Devils Backbone IPA — found and led to fixing several real formatting variations no controlled test image had exposed:
- Net contents expressed in different units (mL, L, fl oz) rather than one consistent format
- Bottler addresses including regulatory boilerplate phrasing before the actual business name
- US state names given as either full names or abbreviations, including a phone number immediately following the state with no separating comma
- Government warning text legally printed entirely in all caps, not just the heading

Each was fixed and covered with dedicated tests, then re-confirmed against the actual product photo that found it.

---

## Assumptions Made

- This is a standalone prototype, not integrated with TTB's actual COLA system, per the assignment's own scope.
- No user accounts or login — a single-session tool, consistent with the assignment's emphasis on simplicity.
- Application data is entered manually alongside each image rather than imported from an external system.
- Test images are either precisely controlled synthetic renders (generated via a script for exact, deliberate text control) or real photographed consumer products — not AI-generated photos, since image generators can't reliably guarantee exact text.
- The required Government Warning statement is a fixed constant in the code, not a submitted or user-editable value, since it's a legal requirement rather than an applicant's claim.

---

## Trade-offs and Limitations

- **No React/TypeScript frontend or Docker containerization.** A deliberate scope decision to focus available time on extraction accuracy and matching correctness — the actual core of the evaluation — rather than infrastructure not required by the assignment itself.
- **Doesn't handle low-quality, angled, or blurry photos.** Flagged for human review instead, matching how compliance agents already work today per the discovery interviews.
- **Batch mode pairs each image with its own on-page form**, rather than a bulk CSV/spreadsheet import. Appropriate for demo-scale testing; a true 200-300-at-once production workflow would accept a structured file matched to image filenames instead.
- **Fuzzy matching on short, numeric-like fields** measures character similarity, not numeric magnitude — a small edit can occasionally still score high even when the actual value differs substantially (e.g., "50 mL" vs. "750 mL" landed in needs-review rather than a hard fail during testing). `needs-review` exists specifically as the safety net for this case.
- **Class/type is compared as the specific designation, not a broader category** — a submission of "Beer" will not match a label reading "India Pale Ale," consistent with TTB's own class/type designation requirements.
- **A near-miss is not auto-passed, even at a high similarity score.** Only an exact match after normalization auto-passes; anything else — including a genuine one-character misspelling — routes to `needs-review` or `fail`, so a human confirms ambiguous cases rather than the system guessing.
- **Upload size is validated at the application layer only.** Production hardening would add a server/proxy-level request size limit as defense in depth.
- **`extraction_confidence` is self-reported by the model**, with no independent verification signal behind it.
- **Wine was not tested live**, due to product availability at the time of testing. The same shared comparison logic has been proven correct across both distilled spirits and beer.
- **No CI pipeline was set up.** Considered, but deprioritized in favor of extensive manual and live testing (documented above), which surfaced more real issues than a lint/test-on-push workflow would have on its own for a project this size.

---

## Path to Production

This prototype intentionally uses the simplest tools that satisfy the assignment. A real production deployment inside TTB's environment would differ in several specific ways:

- **Azure AI Vision / Azure OpenAI Service** instead of the public Claude API, running inside TTB's own Azure tenant with private networking — this directly addresses the firewall/outbound-connectivity failure mode described in discovery interviews (the prior vendor pilot broke because of exactly this), and aligns with TTB's existing Azure/FedRAMP environment.
- **Azure Key Vault** for secrets instead of platform environment variables.
- **React/TypeScript frontend and Docker-based containerization**, matching the engineering team's actual production stack.
- **A queue-based batch pipeline** for true 200-300-at-once scale, replacing the current in-process concurrency.
- **Structured file import** (CSV/spreadsheet) for bulk application data matched to image filenames, replacing per-image manual entry at real import-scale volume.
- **A full production security review** (PII handling, data retention policy, audit logging) and progression through TTB's existing ATO process — a real rollout measured in months, not an overnight deployment.

---

## Security Notes

- Uploaded files are validated by their actual binary signature, not filename extension or client-declared content type, before any processing occurs.
- No uploaded image content or submitted/extracted label data is ever logged — only timing, counts, and per-field pass/fail/needs-review status with similarity scores.
- The `/api/config` endpoint exposes only two explicitly named, non-sensitive settings via allowlist construction — it cannot leak the API key or other settings even if the configuration object grows new fields later.
- The API key is never included in any log line, error message, or API response.
