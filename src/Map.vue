<!-- eslint-disable vue/multi-word-component-names -->
<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import {
  Cartesian2,
  Cartesian3,
  Color,
  HeadingPitchRange,
  defined,
  Entity,
  Ion,
  Math as CesiumMath,
  ScreenSpaceEventType,
  Terrain,
  Viewer,
} from 'cesium'

const cesiumContainer = ref<HTMLElement | null>(null)
const previewImageUrl = ref('')
const previewImageName = ref('')
const hoverImageUrl = ref('')
const hoverImageName = ref('')
const hoverX = ref(0)
const hoverY = ref(0)
let viewer: Viewer | null = null

type PhotoItem = {
  id: number
  filename: string
  relativePath?: string
  imageUrl: string
  thumbUrl?: string
  latitude: number
  longitude: number
  altitude?: number | null
  capturedAt: string | null
}

type PhotoIndexResponse = {
  version: number
  generatedAt: string
  source: string
  stats: {
    totalImageFiles: number
    withGps: number
    withoutGps: number
    parseErrors: number
  }
  items: PhotoItem[]
}

async function loadPhotoIndex(): Promise<PhotoItem[]> {
  const response = await fetch('/img-index/index.json', { cache: 'no-store' })
  if (!response.ok) throw new Error(`读取索引失败: HTTP ${response.status}`)
  const indexData = (await response.json()) as PhotoIndexResponse
  return indexData.items
}

function addAllMarkers(photos: PhotoItem[]): void {
  if (!viewer) return

  viewer.entities.removeAll()

  for (const photo of photos) {
    viewer.entities.add({
      id: String(photo.id),
      name: photo.filename,
      position: Cartesian3.fromDegrees(photo.longitude, photo.latitude, Number(photo.altitude ?? 0)),
      properties: {
        imageUrl: photo.imageUrl,
        thumbUrl: photo.thumbUrl ?? photo.imageUrl,
        relativePath: photo.relativePath ?? photo.filename,
      },
      point: {
        pixelSize: 8,
        color: Color.RED,
        outlineColor: Color.WHITE,
        outlineWidth: 1,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    })
  }

  if (photos.length > 0) {
    void viewer.flyTo(viewer.entities, {
      offset: new HeadingPitchRange(0, CesiumMath.toRadians(-90), 0),
    })
  }
}

function closePreview(): void {
  previewImageUrl.value = ''
  previewImageName.value = ''
}

function closeHoverPreview(): void {
  hoverImageUrl.value = ''
  hoverImageName.value = ''
}

function bindHoverPreview(): void {
  if (!viewer) return

  viewer.screenSpaceEventHandler.setInputAction((movement: { endPosition: Cartesian2 }) => {
    if (!viewer) return

    const picked = viewer.scene.pick(movement.endPosition)
    if (!defined(picked) || !(picked.id instanceof Entity)) {
      closeHoverPreview()
      return
    }

    const thumbUrl = picked.id.properties?.thumbUrl?.getValue(viewer.clock.currentTime)
    if (typeof thumbUrl !== 'string' || thumbUrl.length === 0) {
      closeHoverPreview()
      return
    }

    hoverImageUrl.value = thumbUrl
    const relativePath = picked.id.properties?.relativePath?.getValue(viewer.clock.currentTime)
    hoverImageName.value = typeof relativePath === 'string' && relativePath.length > 0
      ? relativePath
      : (picked.id.name ?? 'photo')
    hoverX.value = movement.endPosition.x + 16
    hoverY.value = movement.endPosition.y + 16
  }, ScreenSpaceEventType.MOUSE_MOVE)
}

function bindPhotoClickPreview(): void {
  if (!viewer) return

  viewer.screenSpaceEventHandler.setInputAction((movement: { position: Cartesian2 }) => {
    if (!viewer) return

    const picked = viewer.scene.pick(movement.position)
    if (!defined(picked) || !(picked.id instanceof Entity)) return

    const imageUrl = picked.id.properties?.imageUrl?.getValue(viewer.clock.currentTime)
    if (typeof imageUrl !== 'string' || imageUrl.length === 0) return

    previewImageUrl.value = imageUrl
    const relativePath = picked.id.properties?.relativePath?.getValue(viewer.clock.currentTime)
    previewImageName.value = typeof relativePath === 'string' && relativePath.length > 0
      ? relativePath
      : (picked.id.name ?? 'photo')
  }, ScreenSpaceEventType.LEFT_CLICK)
}

onMounted(async () => {
  Ion.defaultAccessToken =
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIxZDZmMTY3Ny1jMzI0LTQ1NjgtODQwMi1jZjVmMjMxM2MzNDciLCJpZCI6Mzg4MTg3LCJpYXQiOjE3NzA0ODIzOTl9.WvJLINaASwIWRqwd_h_bGoUaKuHWyTnxc0Jgbgi3imY'

  if (!cesiumContainer.value) return

  viewer = new Viewer(cesiumContainer.value, {
    terrain: await Terrain.fromWorldTerrain(),
    infoBox: false,
  })

  try {
    const photos = await loadPhotoIndex()
    addAllMarkers(photos)
    bindHoverPreview()
    bindPhotoClickPreview()
  }
  catch (error) {
    console.error('加载图片索引失败', error)
  }
})

onUnmounted(() => {
  if (viewer) {
    viewer.screenSpaceEventHandler.removeInputAction(ScreenSpaceEventType.LEFT_CLICK)
    viewer.screenSpaceEventHandler.removeInputAction(ScreenSpaceEventType.MOUSE_MOVE)
  }

  closeHoverPreview()
  viewer?.destroy()
  viewer = null
})
</script>

<template>
  <div ref="cesiumContainer" class="map-container" />

  <div
    v-if="hoverImageUrl && !previewImageUrl"
    class="hover-preview"
    :style="{ left: `${hoverX}px`, top: `${hoverY}px` }"
  >
    <img :src="hoverImageUrl" :alt="hoverImageName" class="hover-preview-image">
    <div class="hover-preview-name">{{ hoverImageName }}</div>
  </div>

  <div v-if="previewImageUrl" class="preview-overlay" @click="closePreview">
    <button class="preview-close" type="button" @click.stop="closePreview">
      x
    </button>
    <img
      :src="previewImageUrl"
      :alt="previewImageName"
      class="preview-image"
      @click.stop
    >
    <div class="preview-name" @click.stop>{{ previewImageName }}</div>
  </div>
</template>

<style scoped>
.map-container {
  width: 100%;
  height: 100vh;
}

.hover-preview {
  position: fixed;
  z-index: 10000;
  width: 220px;
  padding: 6px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.8);
  pointer-events: none;
}

.hover-preview-image {
  display: block;
  width: 100%;
  height: auto;
  max-height: 140px;
  object-fit: contain;
  border-radius: 4px;
}

.hover-preview-name {
  margin-top: 6px;
  color: #fff;
  font-size: 11px;
  line-height: 1.3;
  word-break: break-all;
}

.preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.85);
}

.preview-image {
  max-width: 96vw;
  max-height: 96vh;
  width: auto;
  height: auto;
  object-fit: contain;
}

.preview-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  color: #fff;
  font-size: 20px;
  line-height: 36px;
  background: rgba(255, 255, 255, 0.2);
  cursor: pointer;
}

.preview-name {
  position: absolute;
  left: 20px;
  bottom: 20px;
  max-width: min(90vw, 1200px);
  padding: 8px 10px;
  color: #fff;
  font-size: 12px;
  line-height: 1.4;
  background: rgba(0, 0, 0, 0.45);
  border-radius: 6px;
  word-break: break-all;
}
</style>
