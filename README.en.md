# SkyTiles

<div align="center">

### A lightweight 3D map viewer for UAV photogrammetry images

[![Vue](https://img.shields.io/badge/Vue-3-42b883?style=for-the-badge&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Vite-7-646cff?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Cesium](https://img.shields.io/badge/Cesium-3D%20Map-6cadde?style=for-the-badge)](https://cesium.com/platform/cesiumjs/)
[![License](https://img.shields.io/badge/License-MIT-2ea043?style=for-the-badge)](./LICENSE)

English | [简体中文](./README.md)

</div>

---

## Overview

`SkyTiles` is a lightweight web platform that maps EXIF/GPS data from UAV images into a Cesium 3D scene, so you can browse photos by their real capture locations.

Good for:
- Spatial verification of photogrammetry image sets
- Site image review and visual inspection
- Lightweight 3D geospatial photo presentation

## Key Features

| Feature | Description |
| --- | --- |
| Auto indexing | Scans `public/imgs` and generates `public/img-index/index.json` |
| EXIF parsing | Extracts latitude, longitude, altitude, and capture time |
| 3D marker rendering | Renders all photo points in Cesium |
| Hover preview | Shows thumbnail preview when hovering markers |
| Click-to-open | Opens full image in a modal overlay |
| Incremental build | Python script supports incremental indexing for large datasets |

## Screenshots

> Add your screenshots here for a cooler GitHub landing page.

```text
assets/
├─ cover.png
├─ map-view.png
└─ preview-modal.png
```

Example markdown:

```md
![SkyTiles Cover](./assets/cover.png)
![Map View](./assets/map-view.png)
![Photo Preview](./assets/preview-modal.png)
```

## Tech Stack

- Frontend: `Vue 3` + `TypeScript` + `Vite`
- 3D Engine: `Cesium`
- Indexing scripts:
  - Python: `Pillow`
  - Node.js: `exifr`

## Quick Start

### 1. Install dependencies

```bash
npm install
```

### 2. Prepare image data

Put your photos under:

```text
public/imgs/
```

> Images should contain GPS EXIF metadata, otherwise they cannot be placed on the map.

### 3. Build image index

Recommended Python version (thumbnail + incremental indexing):

```bash
pip install -r requirements.txt
npm run build:image-index
```

Optional Node version:

```bash
npm run build:image-index:node
```

### 4. Run locally

```bash
npm run dev
```

Default local URL is usually `http://localhost:5173`.

## Commands

```bash
# Development
npm run dev

# Production build (with type check)
npm run build

# Frontend-only build
npm run build-only

# Build image index (Python)
npm run build:image-index

# Build image index (Node)
npm run build:image-index:node

# Lint and format
npm run lint
npm run format
```

## Project Structure

```text
SkyTiles/
├─ public/
│  ├─ imgs/               # Source UAV images
│  ├─ thumbs/             # Generated thumbnails
│  └─ img-index/
│     └─ index.json       # Generated index
├─ scripts/
│  ├─ build_image_index.py
│  └─ build-image-index.mjs
├─ src/
│  ├─ Map.vue             # Map rendering and interactions
│  └─ ...
└─ README.en.md
```

## Roadmap

- [ ] Add layer filtering and time-based controls
- [ ] Support route-based grouping
- [ ] Provide an online demo deployment
- [ ] Move Cesium token to environment variables

## Contributing

Contributions are welcome via issues and pull requests.

1. Fork the repository
2. Create a branch: `git checkout -b feat/your-feature`
3. Commit changes: `git commit -m "feat: add your feature"`
4. Push and open a PR

## Notes

- Cesium token is currently in `src/Map.vue`; consider moving it to env vars.
- Images without GPS metadata will not appear on the map.
- Use the Python indexer for large datasets.

## License

This project is licensed under the [MIT License](./LICENSE).
