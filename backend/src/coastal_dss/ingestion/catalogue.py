"""Dataset catalogue: every layer carries provenance metadata (proposal section 3.4).

Records mirror the proposal's data acquisition table. `status` moves planned -> ingested ->
validated as real data are brought in.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class DatasetRecord:
    id: str
    name: str
    source: str
    resolution: str
    crs: str
    coverage: str
    purpose: str
    objectives: tuple[str, ...]
    status: str = "planned"  # planned | ingested | validated
    uncertainty_note: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return asdict(self)


CATALOGUE: tuple[DatasetRecord, ...] = (
    DatasetRecord(
        "dem",
        "Digital Elevation Model",
        "USGS SRTM 1 Arc-Second Global, via the M2M API",
        "30 m",
        "EPSG:4326",
        "static",
        "Elevation, slope, inundation susceptibility",
        ("ii", "iii"),
    ),
    DatasetRecord(
        "gmslr",
        "Global mean sea level rise",
        "IPCC AR6",
        "scenario table",
        "n/a",
        "2030, 2050, 2100; SSP2-4.5, SSP5-8.5",
        "Future sea-level scenarios",
        ("i",),
    ),
    DatasetRecord(
        "subsidence",
        "Land subsidence rates",
        "Published InSAR / GNSS studies",
        "points (mm/yr)",
        "EPSG:4326",
        "annual rates",
        "Local vertical land motion",
        ("i",),
        uncertainty_note="Sparse in-situ GNSS coverage; interpolated",
    ),
    DatasetRecord(
        "rslr",
        "Relative sea level rise (derived)",
        "Computed",
        "raster",
        "EPSG:32631",
        "scenario surfaces",
        "Core hazard layer",
        ("i", "ii", "iii"),
    ),
    DatasetRecord(
        "imagery",
        "Satellite imagery",
        "USGS Landsat 4-5 TM and 8-9 OLI Collection 2 Level-2, via the M2M API",
        "10-30 m",
        "EPSG:32631",
        "multi-date",
        "Land cover and shoreline mapping",
        ("ii",),
    ),
    DatasetRecord(
        "shoreline",
        "Shoreline position",
        "Extracted from imagery",
        "vector",
        "EPSG:32631",
        "multi-temporal",
        "Shoreline change rate",
        ("ii",),
    ),
    DatasetRecord(
        "geomorphology",
        "Coastal geomorphology",
        "Imagery and existing maps",
        "1:50,000-1:100,000",
        "EPSG:32631",
        "static",
        "Vulnerability characterisation",
        ("ii",),
    ),
    DatasetRecord(
        "population",
        "Population",
        "GRID3 Nigeria",
        "100 m - 1 km",
        "EPSG:4326",
        "latest",
        "Socio-economic vulnerability and exposure",
        ("ii", "iii"),
    ),
    DatasetRecord(
        "lulc",
        "Land use / land cover",
        "Classified from imagery",
        "10-30 m",
        "EPSG:32631",
        "latest",
        "Exposure and sensitivity",
        ("ii", "iii"),
    ),
    DatasetRecord(
        "infrastructure",
        "Infrastructure",
        "OpenStreetMap; Lagos State GIS",
        "vector",
        "EPSG:4326",
        "latest",
        "Impact on roads, ports, buildings, utilities",
        ("iii",),
    ),
    DatasetRecord(
        "assets",
        "Economic assets",
        "Lagos State planning documents",
        "administrative",
        "n/a",
        "latest",
        "Economic sector exposure",
        ("iii",),
    ),
    DatasetRecord(
        "floods",
        "Flood records",
        "LASEMA; published studies",
        "event-based",
        "n/a",
        "historical",
        "Validation of hazard outputs",
        ("iv",),
    ),
    DatasetRecord(
        "admin",
        "Administrative boundaries",
        "GRID3 Nigeria",
        "vector",
        "EPSG:4326",
        "latest",
        "Spatial referencing and reporting",
        ("iv",),
    ),
)


def by_id(dataset_id: str) -> DatasetRecord:
    for rec in CATALOGUE:
        if rec.id == dataset_id:
            return rec
    raise KeyError(dataset_id)
