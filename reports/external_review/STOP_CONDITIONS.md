# Stop Conditions

External evaluators must stop claiming discovery capability if ANY of the following is true:

1. **The answer is explicitly present in input material.**
   If the bridge concept appears verbatim in either source snippet, the engine is recognizing, not discovering.

2. **The engine merely retrieves the answer.**
   If the bridge concept is in the extracted entities of either source but not proposed as a cross-domain connection, the engine is retrieving, not discovering.

3. **The benchmark leaks the answer.**
   If the gold answer influences the system's behavior (e.g., through synonym maps, training data, or prompt construction), the result is contaminated.

4. **The relationship is produced only by entity extraction.**
   If the bridge concept is an extracted entity from one source that happens to match the gold bridge via lexical overlap, this is entity extraction, not discovery.

5. **The matcher creates the apparent discovery.**
   If the match depends on token overlap, substring matching, or synonym expansion — rather than genuine semantic understanding — the matcher is creating the discovery, not the engine.

6. **Prior literature already establishes the relationship.**
   If an independent literature search finds the connection was published before the benchmark was constructed, the engine is retrieving known knowledge, not discovering new knowledge.

7. **The mechanism is unsupported.**
   If the engine proposes a bridge but cannot provide a plausible causal mechanism — or the mechanism it provides is scientifically incoherent — the discovery is unsupported.

8. **The evaluator cannot distinguish discovery from recognition.**
   If the evaluator cannot determine whether the engine found something genuinely novel versus recognizing something already present, the discovery claim fails for lack of evidence.

## What "stop" means

If any stop condition is met for a given case, that case must be classified as:
- PREVIOUSLY_KNOWN (if prior literature exists)
- UNSUPPORTED (if no mechanism or evidence)
- AMBIGUOUS (if the evaluator cannot tell)

It must NOT be classified as NOVEL.

## Aggregate stop condition

If stop conditions are met for a majority of cases, the evaluator should conclude that the engine has NOT demonstrated independent discovery capability under the tested conditions.
