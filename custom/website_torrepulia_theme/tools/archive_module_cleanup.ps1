$ErrorActionPreference = 'Stop'
$module = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repo = (Resolve-Path (Join-Path $module '..\..')).Path
$parent = Split-Path $repo -Parent
$separator = [IO.Path]::DirectorySeparatorChar
if (-not $module.StartsWith($repo + $separator, [StringComparison]::OrdinalIgnoreCase) -or (Split-Path $module -Leaf) -ne 'website_torrepulia_theme') {
    throw 'Unexpected module root.'
}
$archive = [IO.Path]::GetFullPath((Join-Path $parent ('torrepulia-theme-cleanup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))))
if (-not $archive.StartsWith($parent + $separator, [StringComparison]::OrdinalIgnoreCase) -or -not (Split-Path $archive -Leaf).StartsWith('torrepulia-theme-cleanup-')) {
    throw 'Archive is outside the intended parent directory.'
}
New-Item -ItemType Directory -Path $archive | Out-Null
Copy-Item -LiteralPath $module -Destination (Join-Path $archive 'module-before-cleanup') -Recurse
$plan = Get-Content -LiteralPath (Join-Path $module 'docs\qa-final\cleanup-plan.json') -Raw | ConvertFrom-Json
$moved = @()
foreach ($entry in @($plan.unused_assets) + @($plan.retired_tools) + @($plan.historical_docs)) {
    $source = [IO.Path]::GetFullPath((Join-Path $module $entry.path))
    $destination = [IO.Path]::GetFullPath((Join-Path (Join-Path $archive 'retired') $entry.path))
    if (-not $source.StartsWith($module + $separator, [StringComparison]::OrdinalIgnoreCase) -or -not $destination.StartsWith($archive + $separator, [StringComparison]::OrdinalIgnoreCase)) {
        throw ('Refusing out-of-scope file operation: ' + $entry.path)
    }
    if (Test-Path -LiteralPath $source -PathType Leaf) {
        New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
        Move-Item -LiteralPath $source -Destination $destination
        $moved += $entry
    }
}
$record = [ordered]@{ archive = $archive; files = $moved.Count; bytes = ($moved | Measure-Object bytes -Sum).Sum; entries = $moved }
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $module 'docs\qa-final\cleanup-results.json') -Encoding UTF8
Write-Output ('Archive: ' + $archive)
Write-Output ('Moved files: ' + $moved.Count)
Write-Output ('Removed from module: ' + $record.bytes + ' bytes')
