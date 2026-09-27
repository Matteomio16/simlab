# Model recipes: how to use GLM and Jev, and what Kev needs

From the test bench, 27–28 Sep 2026 (details and numbers in `docs/CHANGELOG.md`, `docs/scorecard.md`,
`docs/fidelity2.md`). Each rule says what was measured. Total OpenRouter spend for all tests so far: about $1.5.

## GLM-5.3 Flash: the controlled recipe

| Rule | Why (measured) |
| --- | --- |
| Use GLM for the **direction** of a news reaction, not its size | On real events it gets the direction right for 92% of events that moved opinion ≥1 point, but its size barely tracks reality (rank correlation 0.26; fitted points-per-unit 3.4 on everyday events vs 12.6 on famous ones). Sizes come from real data: the filter, per state. |
| Ask every scale **both ways** (as written and reversed) and average | Asked one way GLM leans −44% (toward Republicans, as a share of its typical reaction); both ways −2%. A fixed correction only removes about two-thirds of the lean. |
| **Bundle** all of a persona's questions in one prompt per order | About 2.5–3× cheaper, no parse errors; put the shared question block first and the persona last for prompt caching. |
| Never bundle **vote-choice questions with turnout**; ask turnout on its own | "How did this person vote" implies they voted and pushed turnout answers up (+51 points in one test); even bundled with opinion items turnout bias rose from +9 to +13. |
| **Strip outlet names** before asking which side a story helps | The same headline credited to MSNBC instead of Fox News moves GLM's "helps Democrats" by 30 points; its top answer flips on 41% of stories. |
| Don't take **party-specific opinions** from GLM | It flattens partisan gaps on evaluative items (Democrats approving of Biden: real 83%, GLM 44%). Vote and hot-button issues are close. |
| Keep the **direct question** wording | The Field Guide's "exposure × how it landed" wording was slightly worse on every measure for GLM. |
| Don't expect averaging GLM with Jev (or another hosted model) to cancel errors | Their errors on real events correlate 0.88–0.97; averaging never beat GLM alone. |
| Host: InferenceNet (fp4) with DeepInfra (fp4) as overflow; reasoning `effort: minimal` | InferenceNet rate-limits upstream (429s); reasoning can't be switched off, "minimal" uses 0 tokens. |

Cost at these settings: about $0.03 per 1,000 decisions asked both ways (single questions); bundling lowers it further.

## Jev 1.13

| Use it for | Evidence |
| --- | --- |
| "Does this story change anything?" gate | Irrelevant news: 99–100% "no change" (best of all models). |
| Cheap yes/no and labelling questions | Bundling all questions in one request is ~3× cheaper and gives identical answers; ~$0.02 per 480 stories labelled. |

| Don't use it for | Evidence |
| --- | --- |
| Group percentages on multi-option questions | Its probabilities are label confidence (approval and economy TVD 0.6–0.8). |
| Size of a news reaction | Size-tracking −0.03: it predicts the same size for no-effect and clear-effect events. |
| Anything where the outlet name is visible | Source name moves its "helps" answer by 15 points (top label flips on 15%). |

Scales don't need to be asked both ways for Jev (its order effect is negligible).

## Levels (vote and turnout by group)

Statistics win everywhere: the regression baseline beats every model on all 14 fidelity items (average TVD 0.05–0.07 vs
GLM 0.14–0.16, Jev 0.25–0.36). Turnout targets come from the Census CPS; CES validated turnout tracks voter-file matching
and must not be used for group turnout.

## What Kev needs (the reasons a fine-tuned Kev is worth having)

1. **Real sizes, not model sizes.** Hosted models share the same blind spots (under-react to big shocks, over-react to
   media spectacles) and barely track size. Kev's reaction training uses measured shifts from `simlab/events2.json` (11
   directional + 15 no-change events) and design rules, never GLM answers, so it can be an independent second opinion.
   Headline test on the 19 held-out events: size-tracking vs GLM's 0.26, error correlation with GLM, and whether the
   average of Kev and GLM beats GLM alone.
2. **Partisan structure.** Kev trained on CES party strata with the 14 opinion items should beat GLM where GLM flattens
   partisan gaps.
3. **Invariances built in.** No-change examples on irrelevant news; party-swapped mirror pairs; source-swap pairs if an
   outlet name ever appears; option orders shuffled.
4. **One task at a time until proven otherwise.** ces-v2 (more cell types in one model) did worse on vote than ces-v1; the
   v3a/v3b comparison (CPS turnout vs vote only) tells whether tasks interfere.
5. **Always beat simple baselines** on states it never saw: the regression and the same cell pooled over other states.
