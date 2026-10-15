# 0004 Mapbox GL JS basemap with token fallback
**Decision:** render with Mapbox GL JS and Mapbox styles (satellite-streets, streets, dark, light).
The analysis layer is re-installed on every `style.load`, beneath the first label layer, and
styles are switched with `diff: false` because Mapbox's default style diffing silently removes
custom layers without firing `style.load`. **Fallback:** with no `VITE_MAPBOX_TOKEN` the app uses
an Esri raster basemap so it never shows a blank map. **Note:** Mapbox GL still sends telemetry
requests with a placeholder token in fallback mode; they fail harmlessly. **Cost:** Mapbox
terms and usage limits apply; the token is public and must be URL-restricted.
