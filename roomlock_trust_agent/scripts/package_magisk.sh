#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APK_PATH="${ROOT_DIR}/app/build/outputs/apk/release/app-release.apk"
OUT_DIR="${ROOT_DIR}/build/magisk-module"
ZIP_PATH="${ROOT_DIR}/build/roomlock_trust_agent_magisk.zip"

if [[ ! -f "${APK_PATH}" ]]; then
  echo "Missing APK: ${APK_PATH}" >&2
  echo "Run ./gradlew :app:assembleRelease first, or adjust APK_PATH in this script." >&2
  exit 1
fi

rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}/system/priv-app/RoomLock"
cp -R "${ROOT_DIR}/magisk/common/." "${OUT_DIR}/"
cp "${ROOT_DIR}/magisk/module.prop" "${OUT_DIR}/module.prop"
cp "${ROOT_DIR}/magisk/post-fs-data.sh" "${OUT_DIR}/post-fs-data.sh"
cp "${ROOT_DIR}/magisk/service.sh" "${OUT_DIR}/service.sh"
cp "${APK_PATH}" "${OUT_DIR}/system/priv-app/RoomLock/RoomLock.apk"
chmod 0644 "${OUT_DIR}/system/priv-app/RoomLock/RoomLock.apk"
chmod 0644 "${OUT_DIR}/system/etc/permissions/privapp-permissions-roomlock.xml"
chmod 0644 "${OUT_DIR}/system/etc/sysconfig/roomlock-hiddenapi-whitelist.xml"
chmod 0644 "${OUT_DIR}/module.prop"
chmod 0755 "${OUT_DIR}/post-fs-data.sh" "${OUT_DIR}/service.sh"

rm -f "${ZIP_PATH}"
(
  cd "${OUT_DIR}"
  zip -qr "${ZIP_PATH}" .
)

echo "Created ${ZIP_PATH}"
