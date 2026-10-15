"""Shared constants. Conventions are documented in docs/conventions.md."""

# GMSLR projections in IPCC AR6 are relative to the 1995-2014 mean (centred on 2005).
# Subsidence is therefore accumulated from the same baseline year.
BASELINE_YEAR: int = 2005

HORIZONS: tuple[int, ...] = (2030, 2050, 2100)
PATHWAYS: dict[str, str] = {
    "ssp245": "SSP2-4.5 (intermediate emissions)",
    "ssp585": "SSP5-8.5 (high emissions)",
}

CVI_CLASSES: tuple[str, ...] = ("very low", "low", "moderate", "high", "very high")
