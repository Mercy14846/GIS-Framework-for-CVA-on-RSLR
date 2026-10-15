# 0001 Data provider seam
**Decision:** all science and API code depends on a `DataProvider` protocol, not on files or a
database. **Why:** real layers (DEM, InSAR, GRID3) are not yet available; the prototype must be
demonstrable now and swap to real data later without rewrites. **Cost:** one extra abstraction.
