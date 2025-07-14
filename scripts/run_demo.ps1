# ===============================================================
# Tiaozhanbei2.0 PowerShell Demo Script
# Pipe Tracking and Flange Recognition System
# Author: cxzandy
# Version: 2.0.0
# ===============================================================

param(
    [switch]$SkipPause,
    [switch]$AutoMode,
    [switch]$Verbose
)

# Set console encoding for Chinese characters
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Set project root directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "===============================================" -ForegroundColor Magenta
Write-Host "Tiaozhanbei2.0 System Demo Script" -ForegroundColor Magenta  
Write-Host "Pipe Tracking and Flange Recognition System" -ForegroundColor Magenta
Write-Host "===============================================" -ForegroundColor Magenta
Write-Host ""

# Function to write colored log messages
function Write-ColorLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Color = "White"
    )
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $Color
}

# Check if command exists
function Test-CommandExists {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Environment checks
Write-ColorLog "Starting environment checks..." "INFO" "Blue"

# Check Python
if (Test-CommandExists "python") {
    try {
        $pythonVersion = python --version 2>&1
        Write-ColorLog "Python found: $pythonVersion" "SUCCESS" "Green"
    }
    catch {
        Write-ColorLog "Python version check failed" "ERROR" "Red"
        exit 1
    }
} else {
    Write-ColorLog "Python not found in PATH" "ERROR" "Red"
    exit 1
}

# Check pip
if (Test-CommandExists "pip") {
    Write-ColorLog "pip is available" "SUCCESS" "Green"
} else {
    Write-ColorLog "pip not found in PATH" "ERROR" "Red"
    exit 1
}

# Check Python modules
$modules = @("numpy", "cv2", "pyrealsense2", "serial")
foreach ($module in $modules) {
    try {
        python -c "import $module" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorLog "Python module $module is available" "SUCCESS" "Green"
        } else {
            Write-ColorLog "Python module $module not found" "WARNING" "Yellow"
        }
    }
    catch {
        Write-ColorLog "Failed to check module $module" "WARNING" "Yellow"
    }
}

# Check project structure
$requiredFiles = @(
    "src\main.py",
    "src\config.py",
    "src\camera\calibration.py",
    "src\robot\communication.py",
    "src\perception\obstacle_detection.py",
    "src\perception\pipe_tracking.py",
    "src\utils\logger.py"
)

Write-ColorLog "Checking project file structure..." "INFO" "Blue"
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-ColorLog "File exists: $file" "SUCCESS" "Green"
    } else {
        Write-ColorLog "File missing: $file" "ERROR" "Red"
    }
}

# Check and create required directories
$requiredDirs = @("data\calib", "output", "tests")
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-ColorLog "Directory exists: $dir" "SUCCESS" "Green"
    } else {
        Write-ColorLog "Creating directory: $dir" "INFO" "Yellow"
        try {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-ColorLog "Directory created: $dir" "SUCCESS" "Green"
        }
        catch {
            Write-ColorLog "Failed to create directory: $dir" "ERROR" "Red"
        }
    }
}

Write-Host ""
Write-ColorLog "Environment check completed!" "SUCCESS" "Green"
Write-Host ""

# Ask user confirmation unless in auto mode
if (-not $AutoMode) {
    $confirm = Read-Host "Continue with basic system test? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-ColorLog "Demo cancelled by user" "INFO" "Blue"
        exit 0
    }
}

# Run basic system check (simplified)
Write-ColorLog "Running basic system check..." "INFO" "Blue"
try {
    # Test basic Python import without problematic modules
    $testResult = python -c "import sys; print('Python import test successful')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-ColorLog "Basic Python functionality verified" "SUCCESS" "Green"
    } else {
        Write-ColorLog "Python functionality test failed" "WARNING" "Yellow"
    }
} catch {
    Write-ColorLog "Could not run Python test: $($_.Exception.Message)" "WARNING" "Yellow"
}
Write-ColorLog "Note: For full system test, run: python src\main.py --mode demo" "INFO" "Cyan"

Write-Host ""
Write-ColorLog "Demo script completed successfully!" "SUCCESS" "Green"
Write-Host ""

# Show usage examples
Write-Host "System Usage Examples:" -ForegroundColor Cyan
Write-Host "  Basic demo:         python src\main.py --mode demo --display" -ForegroundColor White
Write-Host "  Camera calibration: python src\main.py --mode calib" -ForegroundColor White
Write-Host "  Real-time tracking: python src\main.py --mode track --display --save" -ForegroundColor White
Write-Host "  System test:        python src\main.py --mode test --verbose" -ForegroundColor White
Write-Host ""

Write-Host "Output Locations:" -ForegroundColor Cyan
Write-Host "  Log files:          output\logs\" -ForegroundColor White
Write-Host "  Tracking results:   output\images\" -ForegroundColor White
Write-Host "  Calibration data:   data\calib\config\" -ForegroundColor White
Write-Host ""

Write-Host "Troubleshooting:" -ForegroundColor Cyan
Write-Host "  Camera issues:      Check RealSense drivers and pyrealsense2 installation" -ForegroundColor White
Write-Host "  Robot issues:       Check serial port connection and permissions" -ForegroundColor White
Write-Host "  Display issues:     Ensure display supports OpenCV windows" -ForegroundColor White
Write-Host ""

if (-not $SkipPause) {
    Read-Host "Press Enter to exit"
}
