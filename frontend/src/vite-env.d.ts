/// <reference types="vite/client" />
interface ImportMetaEnv {
  /** Public Mapbox access token (pk.…). Restrict it to your site URLs in the Mapbox dashboard. */
  readonly VITE_MAPBOX_TOKEN?: string;
}
