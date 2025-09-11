Param (
    [Parameter(ValueFromRemainingArguments, Position = 1)]
    [string[]]$TrailingArgs
)

$VirtualEnvPath = ".venv"
$Python = "$VirtualEnvPath\Scripts\python.exe"

Write-Host "Running CLI..."
if (-Not (Test-Path "$VirtualEnvPath")) {
    Write-Error """$VirtualEnvPath"" doesn't exist. Exiting..."
    return
}

$env:PYTHONPATH = ".\src"
& "$Python" -c "import sys; from i2cs_graph.cli import main; sys.exit(main())" @TrailingArgs
Remove-Item Env:\PYTHONPATH
