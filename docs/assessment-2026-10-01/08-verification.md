# Verification and limitations

Completed October 2, 2026. These checks validate the assessment documents and selected examples. They do not certify that proposed schemas, endpoints, workflows, UI components, or models are integrated into the application.

## Inspection actually performed

- Read application source, both query layers, schema/seed code, scraper adapters, model classes, calculators, frontend routing/components/styles, workflow files, and existing planning documents.
- Opened the running React preview and exercised navigation across Home, Players, Tournaments, Matches, Odds, and Tools. Clicked detail tabs and inspected both desktop (1280 × 900) and mobile (390 × 844) layouts. Restored the preview viewport afterward.
- Checked the running API health response and used a read-only SQLite connection for counts, missing values, format coverage, date ranges, odds age, quick_check, and foreign_key_check.
- Read public product pages, GitHub repository documentation, official framework guidance, and primary papers listed in [report 06](06-research-and-inspiration.md).
- Inspected the legacy Streamlit source. The legacy port responded, but this assessment did not perform a fresh full legacy UI walkthrough.

This establishes observed behavior in the local running preview and saved database, not the behavior of an independently identified public production domain.

## Document checks

| Check | Result |
|---|---|
| Numbered feature proposals | 16, F01–F16 |
| Numbered design proposals | 16, D01–D16 |
| Numbered backend proposals | 16, B01–B16 |
| Numbered model proposals | 16, M01–M16 |
| Code, priority, effort, completion criterion for every proposal | Present for all 64 |
| Python snippet syntax | 40 blocks parsed successfully with Python's AST parser |
| TypeScript/TSX snippet syntax | 20 blocks transpiled without syntax diagnostics |
| Proposal code blocks | 72 across the four category reports; extra blocks are supporting SQL/CSS/configuration |
| Local report/source links | 35 relative links resolve; line anchors are navigation hints rather than a fresh line-range validation |
| Roadmap coverage | All 64 IDs appear in the consolidated backlog |

Syntax parsing/transpilation does not type-check imported API contracts or prove runtime behavior. In particular, React components need their indicated data-loader/route integration; hypothetical schema-v2 code cannot be applied directly to the current schema.

## Numerical examples exercised

Fifteen grouped assertions passed using the documented pure functions:

1. M04 empty forecast population returns unavailable metrics.
2. M04 perfect outcomes give zero Brier score.
3. M04 a 50% forecast gives a 0.25 Brier score for a binary result.
4. M04 −150 with a $100 winning stake yields $66.67 net profit.
5. M04 +150 with a $100 winning stake yields $150 net profit.
6. M04 a losing $100 stake yields −$100.
7. M04 a void-only population has unavailable ROI.
8. M08/F07: twenty combinations of target length and constant leg probability produce normalized score distributions and matching independent-race win probabilities; expected duration remains within the race's legal bounds.
9. M08 the one-leg starter-conditioned case returns its specified probability.
10. M14: four beta-binomial distributions, including zero attempts, normalize and have the expected mean.
11. M10 zero observations returns the stated prior mean.
12. M12 symmetric −110/−110 prices de-vig to 50%/50%, with positive margin.
13. M16 a 72-hour-old snapshot is withheld under the illustrative 36-hour policy.
14. B04 a completed match with an unknown winner remains pending.
15. F11 calendar export preserves a UTC instant and escapes a comma in the title.

These are sanity checks, not empirical validations of a sports model. No model was trained and no new backtest was run. The negative-binomial SciPy example was syntax-checked but not executed because the required scientific dependencies were unavailable in the inspection interpreter.

Three additional D03 TypeScript runtime checks passed: 0.4 displays as 40%, a null probability displays as unavailable, and a symmetric two-sided decorative bar has 50% width per side.

## Existing calculator fixture failure

The normal TypeScript test launcher encountered a native environment lookup error before executing assertions. To distinguish that launcher problem from application behavior, the calculator and its existing test were transpiled to CommonJS with TypeScript and evaluated together using Node's standard assertions.

The fixture reaches calculateEdge(0.6, −120) and fails on object field names:

~~~text
Expected: modelProb, dkImplied, edgePct, expectedValue, grade
Actual:   model_prob, dk_implied, edge_pct, expected_value, grade
Values:   0.6, 0.5455, 5.45, 10, "A"
~~~

The numeric output in this example agrees; the response contract does not. The parlay test also expects camelCase fields while the function returns snake_case fields, as confirmed by source inspection and direct output. The test stops at its first failed assertion, so subsequent assertions were not reported as passing.

This supports B10's recommendation for a single declared calculator contract and meaningful cross-language fixtures. Fixing only the expectation names would not validate push semantics, independence assumptions, or the format heuristic.

## Reproduce the document-level structural check

This standard-library check is read-only. Run it from the repository root; it does not execute the snippets:

~~~python
import ast
import re
from pathlib import Path

root = Path("docs/assessment-2026-10-01")
identifiers = []
python_blocks = 0
for file in sorted(root.glob("*.md")):
    source = file.read_text(encoding="utf-8")
    parts = re.split(r"^## ([FDBM]\d{2})[^\n]*\n", source, flags=re.M)
    for i in range(1, len(parts), 2):
        identifier, body = parts[i:i + 2]
        identifiers.append(identifier)
        assert "Priority" in body and "Effort" in body, identifier
        assert "Done when" in body, identifier
        assert re.search(r"^~~~", body, re.M), identifier
    for language, code in re.findall(
        r"^~~~([^\n]*)\n(.*?)^~~~\s*$", source, re.M | re.S
    ):
        if language.strip() == "python":
            ast.parse(code)
            python_blocks += 1
assert len(identifiers) == len(set(identifiers)) == 64
for prefix in "FDBM":
    assert {i for i in identifiers if i.startswith(prefix)} == {
        prefix + str(n).zfill(2) for n in range(1, 17)
    }
print("64 complete briefs; Python blocks parsed:", python_blocks)
~~~

The 40-block count in the table refers to proposal reports. This reproduction block adds one further Python block to the full document set.

## Environment and scope limits

- The bundled interpreter had standard-library SQLite and NumPy, but not the application's full Streamlit/SQLAlchemy/scikit-learn/SciPy/pytest environment. No dependencies were installed for this assessment.
- The developing-with-streamlit skill's discovery process could not locate a project-specific Python interpreter. Source inspection continued; a full legacy runtime audit is not claimed.
- The TypeScript transpilation check does not resolve React imports or perform semantic type checking.
- SQL migrations, YAML workflow fragments, immutable publication, rollback, model registry, and hypothetical endpoints were not executed or deployed.
- External site/repository observations do not verify their algorithms, subscription-only features, code licenses, or data-access rights.
- Full production accessibility, cross-browser behavior, load, reliability, security, and forecast skill require implementation-specific verification.

## Workspace preservation

Existing uncommitted modifications and untracked application files were present before this task. Assessment work is confined to docs/assessment-2026-10-01. No intentional application-source, database, workflow, dependency, or existing-plan edits were made.

No scraping, odds-provider calls, startup refreshes, continuous workers, model training, deployment, commit, push, or messages to outside parties occurred. The original cached-odds/Actions-only constraints are retained throughout the proposed architecture.
