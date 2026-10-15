"""Shared constants: scenario axes, datums and the study area."""

# GMSLR projections in IPCC AR6 are relative to the 1995-2014 mean (centred on 2005).
# Subsidence is therefore accumulated from the same baseline year.
BASELINE_YEAR: int = 2005

HORIZONS: tuple[int, ...] = (2030, 2050, 2100)
PATHWAYS: dict[str, str] = {
    "ssp245": "SSP2-4.5 (intermediate emissions)",
    "ssp585": "SSP5-8.5 (high emissions)",
}

CVI_CLASSES: tuple[str, ...] = ("very low", "low", "moderate", "high", "very high")

# Water level action (as in NOAA's SLR viewer, but in metres): an extra, uniform water height
# above today's high tide (MHHW) for tides and storm surge, added on top of the projected RSLR.
WATER_LEVEL_MAX_M: float = 3.0
WATER_LEVEL_STEP_M: float = 0.25

# PLACEHOLDER: height of Lagos MHHW above the elevation datum (MSL), from the ~1 m
# semi-diurnal tidal range. Replace with the Lagos tide-gauge datum before using results.
LAGOS_MHHW_M: float = 0.5

# Study area (lon0, lat0, lon1, lat1): central Lagos, Ojo to Lekki, with the Atlantic to the south.
STUDY_AREA: tuple[float, float, float, float] = (3.20, 6.35, 3.75, 6.65)
