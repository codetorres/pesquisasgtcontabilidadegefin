param(
  [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
  [string[]]$SurveyFolderHints = @(
    "P1 -",
    "P2 -",
    "P3 -"
  ),
  [string]$OutputJson = "memoria-duplicidades.json",
  [string]$OutputMarkdown = "memoria-duplicidades.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Convert-ToLongPath {
  param([string]$PathText)

  if ([string]::IsNullOrWhiteSpace($PathText)) {
    return $PathText
  }

  if ($PathText.StartsWith("\\?\\")) {
    return $PathText
  }

  if ($PathText.StartsWith("\\")) {
    return "\\?\UNC\" + $PathText.TrimStart("\")
  }

  $absolute = [System.IO.Path]::GetFullPath($PathText)
  return "\\?\" + $absolute
}

function Normalize-State {
  param([string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) {
    return ""
  }
  return $Value.Trim().ToUpper()
}

function Format-Percent {
  param(
    [int]$Part,
    [int]$Total
  )
  if ($Total -le 0) { return "0%" }
  $p = [math]::Round(($Part / $Total) * 100, 1)
  if ($p % 1 -eq 0) {
    return ("{0}%" -f [int]$p)
  }
  return ("{0}%" -f $p.ToString("0.0"))
}

$surveyResults = @()
$rootDirs = @(Get-ChildItem -LiteralPath $ProjectRoot -Directory -ErrorAction SilentlyContinue)
$resolvedFolders = @()
foreach ($hint in $SurveyFolderHints) {
  $found = $rootDirs | Where-Object { $_.Name -like "$hint*" } | Select-Object -First 1
  if ($found) {
    $resolvedFolders += $found.Name
  } else {
    $resolvedFolders += $hint
  }
}

foreach ($folder in $resolvedFolders) {
  $folderPath = Join-Path $ProjectRoot $folder

  if (-not (Test-Path -LiteralPath $folderPath)) {
    $surveyResults += [pscustomobject]@{
      survey_folder = $folder
      status = "folder_not_found"
      files = @()
    }
    continue
  }

  $zipFiles = Get-ChildItem -LiteralPath $folderPath -Filter "*.zip" -File -ErrorAction SilentlyContinue
  $fileResults = @()

  foreach ($zip in $zipFiles) {
    $zipLongPath = Convert-ToLongPath $zip.FullName
    $entryResults = @()

    $archive = $null
    try {
      $archive = [System.IO.Compression.ZipFile]::OpenRead($zipLongPath)
    } catch {
      $fileResults += [pscustomobject]@{
        file_name = $zip.Name
        status = "open_error"
        error = $_.Exception.Message
        entries = @()
      }
      continue
    }

    foreach ($entry in $archive.Entries) {
      if ($entry.FullName -notmatch "\.csv$") { continue }

      $reader = New-Object System.IO.StreamReader($entry.Open(), [System.Text.Encoding]::UTF8)
      $csvRaw = $reader.ReadToEnd()
      $reader.Close()

      $rows = @()
      try {
        $rows = $csvRaw | ConvertFrom-Csv
      } catch {
        $entryResults += [pscustomobject]@{
          entry_name = $entry.FullName
          status = "csv_parse_error"
          error = $_.Exception.Message
          total_rows = 0
          unique_states = 0
          duplicate_states_count = 0
          duplicate_rows_count = 0
          duplicates = @()
        }
        continue
      }

      if (-not $rows -or $rows.Count -eq 0) {
        $entryResults += [pscustomobject]@{
          entry_name = $entry.FullName
          status = "empty_csv"
          total_rows = 0
          unique_states = 0
          duplicate_states_count = 0
          duplicate_rows_count = 0
          duplicates = @()
        }
        continue
      }

      $columns = $rows[0].PSObject.Properties.Name
      $ufCol = $columns | Where-Object { $_ -eq "Informe o Estado" } | Select-Object -First 1
      if (-not $ufCol) {
        $ufCol = $columns | Where-Object { $_ -match "Estado" } | Select-Object -First 1
      }
      $tsCol = $columns | Where-Object { $_ -match "Carimbo de data/hora" } | Select-Object -First 1

      if (-not $ufCol) {
        $entryResults += [pscustomobject]@{
          entry_name = $entry.FullName
          status = "missing_state_column"
          total_rows = $rows.Count
          unique_states = 0
          duplicate_states_count = 0
          duplicate_rows_count = 0
          duplicates = @()
        }
        continue
      }

      $groups = $rows | Group-Object -Property { Normalize-State($_.$ufCol) } | Where-Object { $_.Name }
      $duplicates = @($groups | Where-Object { $_.Count -gt 1 })
      $duplicateRowsCount = 0
      foreach ($dupState in $duplicates) {
        $duplicateRowsCount += [int]$dupState.Count
      }

      $duplicateItems = @()
      foreach ($g in $duplicates) {
        $tsList = @()
        if ($tsCol) {
          $tsList = $g.Group | ForEach-Object { $_.$tsCol } | Where-Object { $_ } | Sort-Object
        }

        $duplicateItems += [pscustomobject]@{
          state = $g.Name
          count = $g.Count
          timestamps = $tsList
        }
      }

      $entryResults += [pscustomobject]@{
        entry_name = $entry.FullName
        status = "ok"
        state_column = $ufCol
        timestamp_column = $tsCol
        total_rows = $rows.Count
        unique_states = $groups.Count
        duplicate_states_count = $duplicates.Count
        duplicate_rows_count = [int]$duplicateRowsCount
        duplicates = $duplicateItems
      }
    }

    $archive.Dispose()

    $fileResults += [pscustomobject]@{
      file_name = $zip.Name
      status = "ok"
      entries = $entryResults
    }
  }

  $surveyResults += [pscustomobject]@{
    survey_folder = $folder
    status = "ok"
    files = $fileResults
  }
}

$flatEntries = @(
  $surveyResults |
    ForEach-Object { $survey = $_; $_.files | ForEach-Object { $file = $_; $_.entries | ForEach-Object { [pscustomobject]@{
      survey_folder = $survey.survey_folder
      file_name = $file.file_name
      entry_name = $_.entry_name
      status = $_.status
      total_rows = $_.total_rows
      unique_states = $_.unique_states
      duplicate_states_count = $_.duplicate_states_count
      duplicate_rows_count = $_.duplicate_rows_count
      duplicates = $_.duplicates
    } } } }
)

$entriesWithDuplicates = @($flatEntries | Where-Object { $_.status -eq "ok" -and $_.duplicate_states_count -gt 0 })

$memory = [pscustomobject]@{
  generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  project_root = $ProjectRoot
  rule = "Sempre verificar duplicidade por estado (UF) antes de consolidar as estatisticas."
  consolidation_rule = "Se houver duplicidade por UF, consolidar pela resposta mais recente e registrar a UF duplicada na pre-analise."
  has_duplicates = ($entriesWithDuplicates.Count -gt 0)
  surveys = $surveyResults
}

$jsonPath = Join-Path $ProjectRoot $OutputJson
$json = $memory | ConvertTo-Json -Depth 10
Set-Content -LiteralPath $jsonPath -Value $json -Encoding UTF8

$mdPath = Join-Path $ProjectRoot $OutputMarkdown
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Memoria de duplicidades por estado")
$lines.Add("")
$lines.Add("- Atualizado em: $($memory.generated_at)")
$lines.Add("- Regra: $($memory.rule)")
$lines.Add("- Consolidacao: $($memory.consolidation_rule)")
$lines.Add("")

foreach ($entry in $flatEntries) {
  if ($entry.status -ne "ok") {
    continue
  }

  $lines.Add("## $($entry.survey_folder)")
  $lines.Add("- Arquivo: $($entry.file_name)")
  $lines.Add("- Linhas: $($entry.total_rows)")
  $lines.Add("- UFs unicas: $($entry.unique_states)")
  $lines.Add("- UFs em duplicidade: $($entry.duplicate_states_count)")

  if ($entry.duplicate_states_count -gt 0) {
    foreach ($dup in $entry.duplicates) {
      $tsText = if ($dup.timestamps.Count -gt 0) { ($dup.timestamps -join " | ") } else { "sem carimbo" }
      $lines.Add("- Duplicidade: $($dup.state) ($($dup.count) respostas) -> $tsText")
    }
  } else {
    $lines.Add("- Duplicidade: nenhuma")
  }
  $lines.Add("")
}

Set-Content -LiteralPath $mdPath -Value ($lines -join [Environment]::NewLine) -Encoding UTF8

Write-Output "Arquivo atualizado: $jsonPath"
Write-Output "Arquivo atualizado: $mdPath"
