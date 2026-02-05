# Script demo nhanh - Tao cau truc thu muc mau voi mot vai file test

$companies = @("SAB", "VNM", "FPT")

foreach ($company in $companies) {
    $companyPath = "BCTC\$company"
    New-Item -ItemType Directory -Force -Path $companyPath | Out-Null
    
    Write-Host "Da tao folder: $companyPath" -ForegroundColor Cyan
    Write-Host "   -> Dat cac file PDF vao day theo format: $company`_2020.pdf, $company`_2021.pdf, ..." -ForegroundColor Gray
}

Write-Host "`nCau truc thu muc da san sang!" -ForegroundColor Green
Write-Host "`nBuoc tiep theo:" -ForegroundColor Yellow
Write-Host "   1. Copy cac file PDF vao cac folder tuong ung" -ForegroundColor White
Write-Host "   2. Chay: python batch_runner.py" -ForegroundColor White
