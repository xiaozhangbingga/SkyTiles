#!/usr/bin/env python3
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ExifTags, ImageOps
except ImportError:
    print("缺少依赖 Pillow，请先安装：pip install Pillow")
    sys.exit(1)

# 本项目处理的是本地可信图片，关闭 Pillow 的解压炸弹像素限制，
# 避免超大分辨率图片触发 DecompressionBombError。
Image.MAX_IMAGE_PIXELS = None
warnings.simplefilter("ignore", Image.DecompressionBombWarning)


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
WORKSPACE_ROOT = Path.cwd()
IMAGE_ROOT_DIR = WORKSPACE_ROOT / "public" / "imgs"
OUTPUT_DIR = WORKSPACE_ROOT / "public" / "img-index"
OUTPUT_FILE = OUTPUT_DIR / "index.json"
THUMB_ROOT_DIR = WORKSPACE_ROOT / "public" / "thumbs"
THUMB_MAX_EDGE = 320

GPS_INFO_TAG = None
for tag_id, tag_name in ExifTags.TAGS.items():
    if tag_name == "GPSInfo":
        GPS_INFO_TAG = tag_id
        break

GPS_TAGS = ExifTags.GPSTAGS
GPS_IFD_TAG = getattr(getattr(ExifTags, "IFD", object), "GPSInfo", 0x8825)


def to_float(value):
    try:
        return float(value)
    except Exception:
        return None


def to_int(value, default_value=0):
    try:
        return int(value)
    except Exception:
        return default_value


def print_progress(prefix, current, total):
    if total <= 0:
        return
    bar_width = 30
    ratio = current / total
    filled = int(bar_width * ratio)
    bar = "#" * filled + "-" * (bar_width - filled)
    sys.stdout.write(f"\r{prefix} [{bar}] {current}/{total}")
    sys.stdout.flush()
    if current == total:
        sys.stdout.write("\n")


def normalize_relative_path(path_value):
    if not path_value:
        return None
    return str(path_value).replace("\\", "/").lstrip("/")


def derive_relative_path_from_item(item):
    relative_path = normalize_relative_path(item.get("relativePath"))
    if relative_path:
        return relative_path

    image_url = item.get("imageUrl")
    if isinstance(image_url, str) and image_url.startswith("/imgs/"):
        return image_url[len("/imgs/") :]
    return None


def dms_to_decimal(dms_tuple, ref):
    if not dms_tuple or len(dms_tuple) < 3:
        return None
    d = to_float(dms_tuple[0])
    m = to_float(dms_tuple[1])
    s = to_float(dms_tuple[2])
    if d is None or m is None or s is None:
        return None

    decimal = d + (m / 60.0) + (s / 3600.0)
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal


def parse_altitude(gps):
    altitude_value = gps.get("GPSAltitude")
    if altitude_value is None:
        return None

    altitude = to_float(altitude_value)
    if altitude is None:
        return None

    altitude_ref = gps.get("GPSAltitudeRef", 0)
    if isinstance(altitude_ref, bytes) and len(altitude_ref) > 0:
        altitude_ref = altitude_ref[0]

    # EXIF 规范: 0=海平面以上, 1=海平面以下
    if altitude_ref == 1:
        altitude = -abs(altitude)

    return altitude


def normalize_date(value):
    if not value:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    value = str(value).strip()

    # EXIF 常见格式: "YYYY:MM:DD HH:MM:SS"
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.isoformat() + "Z"
        except ValueError:
            pass
    return None


def ensure_rgb_image(image):
    if image.mode in ("RGB", "L"):
        return image.convert("RGB")
    return image.convert("RGB")


def build_thumbnail(file_path):
    rel_path = file_path.relative_to(IMAGE_ROOT_DIR)
    # 统一转为 jpg 缩略图时，保留原扩展名到文件名中，避免同目录同名不同扩展互相覆盖：
    # 例如 a.jpg -> a__jpg.jpg, a.png -> a__png.jpg
    src_ext = rel_path.suffix.lower().lstrip(".")
    thumb_rel_path = rel_path.with_name(f"{rel_path.stem}__{src_ext}.jpg")
    thumb_path = THUMB_ROOT_DIR / thumb_rel_path
    thumb_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(file_path) as image:
        image = ImageOps.exif_transpose(image)
        image = ensure_rgb_image(image)
        image.thumbnail((THUMB_MAX_EDGE, THUMB_MAX_EDGE))
        thumb_path = thumb_path.with_suffix(".jpg")
        image.save(thumb_path, format="JPEG", quality=82, optimize=True)

    thumb_url = "/" + str(thumb_path.relative_to(WORKSPACE_ROOT / "public")).replace("\\", "/")
    return thumb_url


def parse_image_exif(file_path, item_id):
    with Image.open(file_path) as image:
        exif_raw = image.getexif()
        if not exif_raw:
            return None

        # Pillow 的 GPS 数据通常在独立 IFD 中，直接 get(GPSInfo) 往往只拿到偏移整数。
        gps_raw = None
        try:
            gps_raw = exif_raw.get_ifd(GPS_IFD_TAG)
        except Exception:
            gps_raw = None

        if not gps_raw and GPS_INFO_TAG is not None:
            fallback = exif_raw.get(GPS_INFO_TAG)
            if isinstance(fallback, dict):
                gps_raw = fallback

        if not gps_raw:
            return None

        gps = {}
        for key, val in gps_raw.items():
            gps[GPS_TAGS.get(key, key)] = val

        lat_ref = gps.get("GPSLatitudeRef")
        lon_ref = gps.get("GPSLongitudeRef")
        if isinstance(lat_ref, bytes):
            lat_ref = lat_ref.decode("utf-8", errors="ignore")
        if isinstance(lon_ref, bytes):
            lon_ref = lon_ref.decode("utf-8", errors="ignore")

        latitude = dms_to_decimal(gps.get("GPSLatitude"), lat_ref)
        longitude = dms_to_decimal(gps.get("GPSLongitude"), lon_ref)
        altitude = parse_altitude(gps)

        if latitude is None or longitude is None:
            return None

        image_url = "/" + str(file_path.relative_to(WORKSPACE_ROOT / "public")).replace("\\", "/")
        relative_path = str(file_path.relative_to(IMAGE_ROOT_DIR)).replace("\\", "/")
        filename = file_path.name
        thumb_url = build_thumbnail(file_path)
        captured_at = (
            normalize_date(exif_raw.get(36867))  # DateTimeOriginal
            or normalize_date(exif_raw.get(36868))  # DateTimeDigitized
            or normalize_date(exif_raw.get(306))  # DateTime
        )

        return {
            "id": item_id,
            "filename": filename,
            "relativePath": relative_path,
            "imageUrl": image_url,
            "thumbUrl": thumb_url,
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "capturedAt": captured_at,
        }


def main():
    if not IMAGE_ROOT_DIR.exists():
        print(f"目录不存在: {IMAGE_ROOT_DIR}")
        print("请先创建 public/imgs 并放入图片后再执行。")
        sys.exit(1)

    image_files = sorted([
        p
        for p in IMAGE_ROOT_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ], key=lambda p: str(p.relative_to(IMAGE_ROOT_DIR)).lower())

    existing_payload = {}
    existing_items = []
    if OUTPUT_FILE.exists():
        try:
            existing_payload = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
            raw_items = existing_payload.get("items", [])
            if isinstance(raw_items, list):
                existing_items = raw_items
        except Exception as exc:
            print(f"读取旧索引失败，将按空索引处理: {exc}")
            existing_payload = {}
            existing_items = []

    existing_by_relative_path = {}
    max_id = 0
    for item in existing_items:
        if isinstance(item, dict):
            rel_path = derive_relative_path_from_item(item)
            if rel_path:
                existing_by_relative_path[rel_path] = item
            max_id = max(max_id, to_int(item.get("id"), 0))

    new_image_files = []
    total_files = len(image_files)
    for idx, file_path in enumerate(image_files, start=1):
        rel_path = normalize_relative_path(file_path.relative_to(IMAGE_ROOT_DIR))
        if rel_path not in existing_by_relative_path:
            new_image_files.append(file_path)
        print_progress("扫描文件", idx, total_files)

    new_items = []
    without_gps_count = 0
    error_count = 0

    total_new_files = len(new_image_files)
    for idx, file_path in enumerate(new_image_files, start=1):
        try:
            max_id += 1
            item = parse_image_exif(file_path, max_id)
            if item:
                new_items.append(item)
            else:
                without_gps_count += 1
        except Exception as exc:
            error_count += 1
            print(f"EXIF 解析失败: {file_path} -> {exc}")
        print_progress("处理新增", idx, total_new_files)

    items = existing_items + new_items
    old_stats = existing_payload.get("stats", {}) if isinstance(existing_payload, dict) else {}
    old_without_gps = to_int(old_stats.get("withoutGps"), 0)
    old_parse_errors = to_int(old_stats.get("parseErrors"), 0)

    payload = {
        "version": 1,
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "source": "/imgs",
        "mode": "incremental",
        "stats": {
            "totalImageFiles": len(image_files),
            "withGps": len(items),
            "withoutGps": old_without_gps + without_gps_count,
            "parseErrors": old_parse_errors + error_count,
            "newFilesProcessed": total_new_files,
        },
        "items": items,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"图片索引已生成: {OUTPUT_FILE}")
    print(
        f"总数: {payload['stats']['totalImageFiles']}, "
        f"有GPS: {payload['stats']['withGps']}, "
        f"无GPS: {payload['stats']['withoutGps']}, "
        f"失败: {payload['stats']['parseErrors']}, "
        f"本次新增处理: {payload['stats']['newFilesProcessed']}"
    )


if __name__ == "__main__":
    main()
