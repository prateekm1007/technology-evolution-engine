# TEE Web Layer
Production API + frontend over the frozen core engine.
## Run
    pip install -r web/requirements.txt && ./web/run.sh
## Verification
    python scripts/verify_stack.py && python scripts/calibrate.py
## Verification contract
Every API response carries a verification field: implemented | integrated | benchmarked | verified.
The UI cannot present speculation as fact.
## Rule 8 compliance
This layer READS engine/, ontology/, data/. It never writes to them.
