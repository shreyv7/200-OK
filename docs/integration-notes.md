# M0 Integration Notes (post-merge)

**Status:** M0 from Backend, AIA, and AIS is integrated on `dev` and `main`.

## Source of truth (PRD-aligned)

| Contract | Owner | Import from |
|---|---|---|
| `EvidenceEvent`, `DeclaredSelf`, `GapBreakdown`, `DecisionPacket`, `IdentityStack`, `LedgerEntry` | **Backend** | `from app.schemas import ...` |
| Gap formula constants + scoring | **AIA** | `app.services.identity.scoring` |
| LangGraph coordinator + stack assembly | **AIS** | `app.agents`, `app.services.recommendation` |

## Known M0 seams (fix in M1)

1. **AIS `app/agents/_contracts.py`** is a TEMP mirror — M1 AIS work must migrate to `app.schemas` (Backend-owned).
2. **Field naming:** Backend schemas use PRD camelCase (`userId`, `whyThis`). AIS mirror uses snake_case — align during M1.
3. **Providers:** Backend has `app/providers/llm.py`; AIS has `app/providers/llm/` stubs — consolidate behind Backend facades in M1+.
4. **AIA `pyproject.toml`** is supplementary; CI uses `requirements.txt` + `requirements-dev.txt`.

## Merge order (every milestone)

**Backend → AIA → AIS → `dev` → `main`**

## Run tests locally

```bash
cd services/api
pip install -r requirements.txt -r requirements-dev.txt
AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q
```
