<div align="center">

# SkyTiles · 司图

### 无人机航测影像的三维可视化浏览平台

[![Vue](https://img.shields.io/badge/Vue-3-42b883?style=for-the-badge&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Vite-7-646cff?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Cesium](https://img.shields.io/badge/Cesium-3D%20Map-6cadde?style=for-the-badge)](https://cesium.com/platform/cesiumjs/)
[![License](https://img.shields.io/badge/License-Apache%202.0-d22128?style=for-the-badge)](./LICENSE)

[English](./README.en.md) | 简体中文

</div>

---

## 项目简介

`SkyTiles（司图）` 用于将无人机影像中的 EXIF/GPS 信息映射到 Cesium 三维场景，实现“按拍摄位置回看照片”的交互式浏览体验。

适用于：

- 航测影像空间位置核查
- 项目现场影像回溯与可视化巡检
- 轻量级三维地图照片展示

## 功能亮点

| 能力        | 说明                                                    |
| ----------- | ------------------------------------------------------- |
| 自动索引    | 扫描 `public/imgs` 并生成 `public/img-index/index.json` |
| EXIF 解析   | 提取经纬度、高程、拍摄时间等信息                        |
| 3D 点位渲染 | 将照片批量渲染到 Cesium 三维地图                        |
| 悬停预览    | 鼠标移动到点位时显示缩略图                              |
| 点击大图    | 点击点位打开原图查看                                    |
| 增量构建    | Python 脚本支持增量索引，适配大批量数据                 |

<!--
## 界面预览

> 你可以在这里放项目截图，发布到 GitHub 时观感会更好。

```text
assets/
├─ cover.png
├─ map-view.png
└─ preview-modal.png
```

示例（请替换为你自己的截图路径）：

```md
![SkyTiles Cover](./assets/cover.png)
![Map View](./assets/map-view.png)
![Photo Preview](./assets/preview-modal.png)
```
-->

## 技术栈

- 前端：`Vue 3` + `TypeScript` + `Vite`
- 地图引擎：`Cesium`
- 索引脚本：
  - Python：`Pillow`
  - Node.js：`exifr`

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 准备影像数据

将图片放入：

```text
public/imgs/
```

> 建议使用包含 GPS EXIF 信息的照片，否则无法在地图中定位。

### 3. 生成图片索引

推荐 Python 版（支持缩略图与增量构建）：

```bash
pip install -r requirements.txt
npm run build:image-index
```

可选 Node 版：

```bash
npm run build:image-index:node
```

### 4. 启动开发环境

```bash
npm run dev
```

默认访问地址通常为 `http://localhost:5173`。

## 命令速查

```bash
# 开发
npm run dev

# 构建（含类型检查）
npm run build

# 仅前端构建
npm run build-only

# 索引构建（Python）
npm run build:image-index

# 索引构建（Node）
npm run build:image-index:node

# 代码检查与格式化
npm run lint
npm run format
```

## 项目结构

```text
SkyTiles/
├─ public/
│  ├─ imgs/               # 原始航测图片
│  ├─ thumbs/             # 缩略图（脚本生成）
│  └─ img-index/
│     └─ index.json       # 索引文件（脚本生成）
├─ scripts/
│  ├─ build_image_index.py
│  └─ build-image-index.mjs
├─ src/
│  ├─ Map.vue             # 三维地图与照片交互
│  └─ ...
└─ README.md
```

## Roadmap

- [ ] 增加图层筛选与时间轴过滤
- [ ] 支持按航线分组浏览
- [ ] 支持在线部署示例（Demo）
- [ ] 引入环境变量管理 Cesium Token

## 贡献

欢迎提交 Issue 与 PR，一起完善 `SkyTiles / 司图`。

1. Fork 仓库
2. 新建分支：`git checkout -b feat/your-feature`
3. 提交修改：`git commit -m "feat: add your feature"`
4. 推送分支并发起 PR

## 注意事项

- 当前 Cesium Token 在 `src/Map.vue` 中，建议迁移到环境变量。
- 无 GPS 的图片不会出现在地图点位上。
- 大批量影像建议使用 Python 索引脚本。

## 许可证

本项目基于 [Apache License 2.0](./LICENSE) 开源。
