#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
project_root=$(pwd)
cargo_bin="${CARGO:-$HOME/.cargo/bin/cargo}"
# A stable certificate keeps the app's designated requirement consistent across
# rebuilds. Ad-hoc signing ties it to the executable hash and breaks TCC grants.
signing_identity="${WRITING_FTM_SIGNING_IDENTITY:-}"
if [ -z "$signing_identity" ]; then
    signing_identity=$(security find-identity -v -p codesigning | awk '/"Apple Development:|"Developer ID Application:/ { print $2; exit }')
fi
if [ -z "$signing_identity" ]; then
    printf '%s\n' 'No development signing certificate found. Set WRITING_FTM_SIGNING_IDENTITY to a code-signing identity.' >&2
    printf '%s\n' 'For a temporary build only, set WRITING_FTM_SIGNING_IDENTITY=- (capture permission may reset after rebuilding).' >&2
    exit 1
fi
"$cargo_bin" build --manifest-path widget/Cargo.toml --locked -j 4
bundle="$project_root/runs/widget/Writing FTM.app"
mkdir -p "$bundle/Contents/MacOS" "$bundle/Contents/Resources"
cp widget/target/debug/writing-ftm-widget "$bundle/Contents/MacOS/writing-ftm-widget"
printf '%s\n' "$project_root" > "$bundle/Contents/Resources/project-root.txt"
cat > "$bundle/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>dev.yash.writing-ftm.widget</string>
<key>CFBundleName</key><string>Writing FTM</string>
<key>CFBundleDisplayName</key><string>Writing FTM</string>
<key>CFBundleExecutable</key><string>writing-ftm-widget</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>0.1.0</string>
<key>CFBundleVersion</key><string>1</string>
<key>LSUIElement</key><true/>
<key>NSHighResolutionCapable</key><true/>
<key>LSMinimumSystemVersion</key><string>13.0</string>
<key>NSScreenCaptureUsageDescription</key><string>Capture a work area you select to extract text for local feedback.</string>
</dict></plist>
PLIST
codesign --force --sign "$signing_identity" --timestamp=none --identifier dev.yash.writing-ftm.widget "$bundle"
codesign --verify --strict "$bundle"
printf 'Built: %s\n' "$bundle"
