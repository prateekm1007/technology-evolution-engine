# Matcher Specification (MATCHER_SPEC.md)

## Current production matcher: `_bridge_matches(expected_bridge, candidate)`

### Step 1: Canonicalization
- Lowercase
- Replace whitespace and hyphens with underscores
- Remove non-alphanumeric characters (except underscores)
- Collapse multiple underscores
- Strip leading/trailing underscores

### Step 2: Exact match
If canonicalized expected == canonicalized candidate → MATCH

### Step 3: Substring match
If canonicalized expected is a substring of canonicalized candidate, or vice versa → MATCH

### Step 4: Token overlap
- Split both canonicalized strings by underscores
- Remove stopwords: {the, a, an, of, in, and, for, to, with, by}
- If any shared token of length >= 4 exists → MATCH

### Step 5: Synonym map
- Look up canonicalized expected in BRIDGE_SYNONYMS
- If candidate's canonical form is in the synonym set → MATCH
- If any synonym is a substring of candidate or vice versa → MATCH

### Current state
BRIDGE_SYNONYMS is empty (cycle 270). Step 5 is a no-op.
The matcher effectively does: exact → substring → token overlap.
