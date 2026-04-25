$ErrorActionPreference = 'Stop'

function Get-PythonCommand {
  foreach ($candidate in @('py', 'python', 'python3')) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
      return $candidate
    }
  }

  throw "Python tidak ditemukan. Pastikan Python sudah terpasang dan bisa diakses dari terminal."
}

$tailwindArgs = @(
  'tailwindcss',
  '-i', './static/src/input.css',
  '-o', './static/css/output.css',
  '--watch'
)

$tailwindProcess = Start-Process -FilePath 'npx.cmd' -ArgumentList $tailwindArgs -PassThru -WindowStyle Hidden

try {
  Write-Host 'Tailwind watch berjalan di background.'
  Write-Host 'Menyalakan Django runserver...'

  $python = Get-PythonCommand
  & $python manage.py runserver
}
finally {
  if ($tailwindProcess -and -not $tailwindProcess.HasExited) {
    Stop-Process -Id $tailwindProcess.Id -Force
  }
}
