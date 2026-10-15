from functools import lru_cache

from coastal_dss.core.config import get_settings
from coastal_dss.providers.base import DataProvider, Grid


@lru_cache
def get_provider() -> DataProvider:
    s = get_settings()
    if s.data_mode == "demo":
        from coastal_dss.providers.demo import DemoProvider

        return DemoProvider()
    if s.data_mode == "raster":
        from coastal_dss.providers.raster import RasterProvider

        return RasterProvider(s.data_dir / "processed")
    raise NotImplementedError(f"data_mode '{s.data_mode}' is not implemented (demo | raster)")


__all__ = ["DataProvider", "Grid", "get_provider"]
