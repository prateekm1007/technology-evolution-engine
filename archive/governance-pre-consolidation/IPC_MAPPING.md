# IPC_MAPPING — Phase 7B

**Status:** IPC classification mapping (definition, not yet populated).
**Phase:** 7B.

This document defines how IPC (International Patent Classification)
codes map to the CAPABILITY_MODEL. IPC is the predecessor to CPC and
is still used by many patent offices. For patents filed before 2013
(or in jurisdictions that haven't adopted CPC), IPC is the only
classification available.

---

## 1. The IPC hierarchy for electrochemical energy storage

The primary IPC code is:

```text
H01M — PROCESSES OR MEANS, e.g. BATTERIES, FOR THE DIRECT
       CONVERSION OF CHEMICAL ENERGY INTO ELECTRICAL ENERGY
```

(Same top-level as CPC — CPC was built on the IPC foundation.)

### Key IPC subgroups for this vertical

| IPC code | Description | Maps to capabilities |
|---|---|---|
| H01M 4/00 | Electrodes | INTERCALATION, ELECTRON_COLLECTION |
| H01M 10/00 | Secondary cells | ELECTROCHEMICAL_ENERGY_STORAGE |
| H01M 10/0525 | Rocking-chair (Li-ion) | ION_TRANSPORT |
| H01M 10/40 | Assembling | CELL_ASSEMBLY |
| H01M 10/48 | Monitoring | STATE_OF_CHARGE_MONITORING, SAFETY_PROTECTION |

---

## 2. IPC vs CPC coverage

| Feature | IPC | CPC |
|---|---|---|
| Introduced | 1968 | 2013 |
| Granularity | ~70,000 subgroups | ~250,000 subgroups |
| Maintained by | WIPO | EPO + USPTO + others |
| Used for | Pre-2013 patents; non-CPC jurisdictions | Post-2013 patents in CPC jurisdictions |

For the Phase 7 corpus (1990-2026):
- Patents 1990-2012: IPC only (may have CPC retrospectively applied)
- Patents 2013-2026: CPC (may also have IPC)

**Both should be ingested.** A patent's IPC code is evidence; its
CPC code is evidence. They are complementary, not competing.

---

## 3. What this document does NOT do

- Same as CPC_MAPPING.md Section 4.
- IPC is treated as secondary evidence when CPC is available.
  When only IPC is available (pre-2013 patents), IPC is primary.
