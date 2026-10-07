param(
    [string]$Python = "python"
)

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dist = Join-Path $Root "dist"
$Build = Join-Path $Root "build"

& $Python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name MathModelingChartGallery `
    --icon (Join-Path $Root "assets\icon.ico") `
    --paths (Join-Path $Root "src") `
    --add-data "$(Join-Path $Root 'src\chart_gallery\style.qss');." `
    --add-data "$(Join-Path $Root 'assets\icon.png');." `
    --exclude-module chart_gallery.ai `
    --distpath $Dist `
    --workpath $Build `
    --specpath $Root `
    (Join-Path $Root "portable_run.py")

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Built: $(Join-Path $Dist 'MathModelingChartGallery.exe')"
