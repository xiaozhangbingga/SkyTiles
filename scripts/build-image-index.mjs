import { mkdir, readdir, writeFile } from 'node:fs/promises'
import { extname, join, relative, resolve } from 'node:path'
import process from 'node:process'

import exifr from 'exifr'

const IMAGE_EXTENSIONS = new Set([
  '.jpg',
  '.jpeg',
  '.png',
  '.webp',
])

const workspaceRoot = process.cwd()
const imageRootDir = resolve(workspaceRoot, 'public/imgs')
const outputDir = resolve(workspaceRoot, 'public/img-index')
const outputFile = resolve(outputDir, 'index.json')

async function walkFiles(targetDir) {
  const entries = await readdir(targetDir, { withFileTypes: true })
  const results = await Promise.all(
    entries.map(async (entry) => {
      const fullPath = join(targetDir, entry.name)
      if (entry.isDirectory()) return walkFiles(fullPath)
      return [fullPath]
    }),
  )
  return results.flat()
}

function normalizeImageUrl(absolutePath) {
  const rel = relative(resolve(workspaceRoot, 'public'), absolutePath).replaceAll('\\', '/')
  return `/${rel}`
}

function normalizeDate(value) {
  if (!value) return null
  if (value instanceof Date) return value.toISOString()
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return null
  return parsed.toISOString()
}

async function parseImageExif(filePath, id) {
  const exif = await exifr.parse(filePath, { gps: true })
  const latitude = Number(exif?.latitude)
  const longitude = Number(exif?.longitude)

  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    return null
  }

  const imageUrl = normalizeImageUrl(filePath)
  const filename = imageUrl.split('/').pop() ?? imageUrl
  const capturedAt =
    normalizeDate(exif?.DateTimeOriginal)
    ?? normalizeDate(exif?.CreateDate)
    ?? normalizeDate(exif?.ModifyDate)

  return {
    id,
    filename,
    imageUrl,
    latitude,
    longitude,
    capturedAt,
  }
}

async function main() {
  let allFiles = []
  try {
    allFiles = await walkFiles(imageRootDir)
  }
  catch (error) {
    if (error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT') {
      console.error(`目录不存在: ${imageRootDir}`)
      console.error('请先创建 public/imgs 并放入图片后再执行。')
      process.exitCode = 1
      return
    }
    throw error
  }
  const imageFiles = allFiles.filter((filePath) => IMAGE_EXTENSIONS.has(extname(filePath).toLowerCase()))

  const items = []
  let withoutGpsCount = 0
  let errorCount = 0

  for (let index = 0; index < imageFiles.length; index += 1) {
    const filePath = imageFiles[index]
    try {
      const item = await parseImageExif(filePath, index + 1)
      if (item) items.push(item)
      else withoutGpsCount += 1
    }
    catch (error) {
      errorCount += 1
      console.warn(`EXIF 解析失败: ${filePath}`, error)
    }
  }

  const payload = {
    version: 1,
    generatedAt: new Date().toISOString(),
    source: '/imgs',
    stats: {
      totalImageFiles: imageFiles.length,
      withGps: items.length,
      withoutGps: withoutGpsCount,
      parseErrors: errorCount,
    },
    items,
  }

  await mkdir(outputDir, { recursive: true })
  await writeFile(outputFile, JSON.stringify(payload, null, 2), 'utf-8')

  console.log(`图片索引已生成: ${outputFile}`)
  console.log(
    `总数: ${payload.stats.totalImageFiles}, 有GPS: ${payload.stats.withGps}, 无GPS: ${payload.stats.withoutGps}, 失败: ${payload.stats.parseErrors}`,
  )
}

main().catch((error) => {
  console.error('生成图片索引失败', error)
  process.exitCode = 1
})
