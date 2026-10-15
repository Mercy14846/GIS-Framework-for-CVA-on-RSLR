from functools import lru_cache

from coastal_dss.core.config import get_settings
from coastal_dss.providers.base import DataProvider, Grid


@lru_cache
def get_provider() -> DataProvider:
    mode = get_settings().data_mode
    if mode == "demo":
        from coastal_dss.providers.demo import DemoProvider

        return DemoProvider()
    raise NotImplementedError(f"data_mode '{mode}' is not implemented yet (see docs/roadmap.md)")


__all__ = ["DataProvider", "Grid", "get_provider"]
