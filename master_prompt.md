I'm building a prototype for a federal job take-home assignment: an AI-powered
alcohol label verification tool. Here are the locked-in decisions:

ARCHITECTURE
- A single Python + FastAPI app. No separate frontend framework or build
  step -- the frontend is a plain static/index.html and static/app.js,
  served directly by FastAPI's StaticFiles at the root path, with /api/*
  routes handled separately. Single origin, no CORS needed.
- No Docker/containerization for this version -- it deploys directly to
  Render's native Python runtime (pip install -r requirements.txt, then
  uvicorn main:app --host 0.0.0.0 --port $PORT, reading the port from the
  PORT environment variable, not hardcoded).

CORE FEATURE
One endpoint, POST /api/verify, accepts a list of one or more items. Each
item pairs one label image with its own submitted application data (brand
name, class/type designation, alcohol content, net contents, bottler
name/address, country of origin if applicable) -- a single verification is
just a list containing one item, so there is no separate single-item vs
batch endpoint. For each item in the list:
1. Sends the image to the Claude API (model: claude-sonnet-5) using Claude's
   tool-use feature (a forced tool call with a JSON schema matching a
   Pydantic LabelFields model) to extract these same fields from the label
   as structured, validated data -- brand name, class/type, alcohol content,
   net contents, bottler name/address, country of origin if present,
   government warning text, and whether "GOVERNMENT WARNING:" appears in
   bold and all caps.
2. Compares extracted fields to that item's submitted fields using
   different rules per field:
   - Brand name, class/type: normalize (trim, case-fold, collapse
     whitespace) then fuzzy-compare using rapidfuzz. Above a similarity
     threshold = pass, below = fail, borderline = "needs review."
   - Alcohol content: parse the numeric value regardless of formatting
     ("45%", "45% Alc./Vol.", "90 proof") and compare numerically with small
     tolerance.
   - Government warning statement: exact, case-sensitive match against the
     required statutory text, plus a check that "GOVERNMENT WARNING:"
     specifically appears in all caps and bold. No fuzziness here at all.
   - Country of origin: only checked when the application indicates an
     import.
3. Returns per-field pass/fail/needs-review results with a plain-language
   reason for any failure.

When the list has more than one item, process them with limited concurrency
(asyncio, not fully serial), streaming/returning results as each completes
rather than blocking on the whole list.

FRONTEND PAIRING
The user adds one or more label images (drag-and-drop or file picker). For
each image added, the page shows a small inline form (thumbnail plus its
own application-data fields) directly with that image -- this is how the
user associates each image with its data: visually and positionally, not
by filename or ID. Submitting sends the full ordered list of image+data
pairs together in one request.

DESIGN PRINCIPLES
- Low-confidence extractions or borderline fuzzy matches should be flagged
  "needs review," never silently guessed or auto-rejected -- a human stays
  in the loop on judgment calls.
- Fall back to "needs review" on a failed, slow, or malformed API response
  rather than crashing or guessing.
- Reject non-image uploads and cap file size before processing.
- Log each request's timing and outcome using Python's logging module: which
  endpoint was hit (single or batch), how many labels were involved, how
  long it took in seconds, and a summary of the outcome (counts of
  pass/fail/needs-review). Never log the uploaded image or the submitted
  application data itself -- only timing and outcome counts.
- No hardcoded secrets anywhere -- API key only via environment variable.
- UI must be extremely simple: one page, drag-and-drop upload, a form for
  the application data fields, clear color-coded results (pass/fail/needs
  review), no navigation menus or settings screens.

Please start by proposing the file/folder structure for the whole project
(just the layout with a one-line comment on what each file is for -- don't
write full implementations yet). Show me the plan before writing any code.