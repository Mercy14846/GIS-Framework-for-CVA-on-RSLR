from fastapi import APIRouter

from coastal_dss import __version__
from coastal_dss.core.config import get_settings
from coastal_dss.ingestion.catalogue import CATALOGUE
from coastal_dss.providers import get_provider
from coastal_dss.scenarios.registry import available
from coastal_dss.services.assessment import default_weights

router = APIRouter()


@router.get("/health")
def health() -> dict:
    s = get_settings()
    return {"status": "ok", "version": __version__, "data_mode": s.data_mode}


@router.get("/scenarios")
def scenarios() -> dict:
    weights, cr = default_weights()
    return {
        **available(),
        "data_mode": get_settings().data_mode,
        "ahp": {"weights": weights, "consistency_ratio": round(cr, 3)},
    }


@router.get("/layers")
def layers() -> list[dict]:
    return [r.to_dict() for r in CATALOGUE]


@router.get("/sources")
def sources() -> dict:
    """Where each analysis layer comes from: observed, derived or a synthetic placeholder."""
    p = get_provider()
    return {"data_mode": p.mode, "layers": p.sources()}
