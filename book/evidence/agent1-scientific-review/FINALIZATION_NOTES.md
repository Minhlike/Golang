# Continuous finalization — retained failures and boundaries

The first final tests run is retained in validation.json/finalization/tests:
edition-contracts failed because this reviewer wrote the A04 oracle as
`x declared and not used`. The real Go1.27.1 compiler emitted
`declared and not used: x`; the original Atlas heading was already correct.
The reviewer restored the heading and fixed the test. tests_2 is a fresh run,
not a relabel of the failed run; A04 is not an Agent 2 defect.

The first candidate build stopped at code-width preflight: Ch25 line442,
448.5pt versus 448.2pt allowed. The new jitter expression was split into a
fraction and conversion without reducing font size. No candidate was promoted.

The first whole-manuscript PDF fidelity attempt raised
`RuntimeError: PDF code mismatch 27 block1` before writing a result. Actual
PDF span inspection found SourceSerif4 at14pt for the first C example, while
the later corrected C example used JetBrainsMono at11.5pt. The remaining
quoted fence in Ch27 rendered literally in separate callout boxes. This is
a real inherited source/layout defect, not an oracle issue: remove quotation
prefixes from the fence and rebuild. These notes describe observed failures,
not a fabricated raw stdout transcript.

Library source retrieval attempt1 saved 110 requests, including three AWS
HTTP429 failures. Attempt2 preserves those failures and verifies the three
fallback files independently from content-addressed Git commit/blob objects,
with origin, object hashes and content SHA256; the other files are retrieved
from pinned official raw URLs. File retrieval is not semantic-claim PASS.

The MCP printed handlers omit rate limiting and authenticated caller keys.
Their excerpt test subset checks the boundaries actually printed; the full
unchanged lab test suite separately checks the limiter. Neither is a test of
production authentication, DNS safety, external egress policy or durable audit.

The first actual-PDF excerpt run compiled all five harnesses; its MCP subset
failed three repeated assertions on the error-message contract. The shortened
printed message `target ... blocked by policy` differed from the full lab's
`unapproved target_id ...: blocked by SSRF allowlist policy`. Restore the lab
message in the book, not relax the lab test; rebuild and test the final PDF.
The first PDF content audit also had an oracle normalization mistake: it
uppercased the Error Atlas introductory subtitle as if it were an A–J group.
Only actual group headings render uppercase. Keep both failed results; no
PASS is transferred from a different PDF SHA256.

Actual a6509bcc candidate pages443/444 exposed Git-label overlap and cropped
HMAC. Review of all source PNG dimensions found five images exactly4096px;
each was opened individually and clipping was visible. Old candidate review
is retained:25 pages actually opened,22 pass and3 issues (P3 raw math labels,
P2 overlap, P2 HMAC crop). It is not transferred to the rebuilt candidate.
Five additional diagram models were compared directly against B/C: C added
unsupported reflog/GraphQL parity, unconditional AWS priority/refresh,
eBPF zero-copy and attach conflation, MCP in an unrelated mailbox section,
and invented CVE/runtime-activation claims. Native source repairs are R108–114.

PlantUML1.2026.8 produced a yellow Padding deprecation banner; those generated
images were rejected before final PDF build. Rerender uses the repository's
PlantUML1.2024.7 with UTF-8 and a20000px limit, preserving shared style bytes.
No generated warning banners or PDF pixel patches are accepted.

visual_final prepare was attempted before pdf_3 fidelity had finished;
the SHA guard refused stale evidence. No review state was reset or filled.
