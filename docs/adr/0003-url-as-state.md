# 0003 URL as application state
**Decision:** view state (tab, pathway, horizon, subsidence, map position) is encoded in the URL.
**Why:** shareable, citable views, matching the NOAA viewer. **Cost:** state changes must go
through `useUrlState`.
