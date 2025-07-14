# ==================================================================
# Tiaozhanbei2.0 项目演示脚本 (PowerShell版本)
# 管道追踪与法兰识别系统 - 完整测试与使用流程
# 
# 功能:
# 1. 系统环境检查
# 2. 各模块单元测试
# 3. 系统集成测试
# 4. 实际使用演示
#
# 作者: cxzandy
# 版本: 2.0.0
# ==================================================================

param(
    [switch]$SkipPause,    # 跳过暂停
    [switch]$AutoMode,     # 自动模式，跳过用户输入
    [switch]$Verbose       # 详细输出
)

# 设置UTF-8编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding

# 设置项目根目录
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# 颜色定义
$Colors = @{
    Red     = "Red"
    Green   = "Green"
    Yellow  = "Yellow"
    Blue    = "Blue"
    Magenta = "Magenta"
    Cyan    = "Cyan"
    White   = "White"
}

# 日志函数
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Color = "White"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp]" -ForegroundColor Gray -NoNewline
    Write-Host " [$Level]" -ForegroundColor $Color -NoNewline
    Write-Host " $Message"
}

function Write-LogInfo { 
    param([string]$Message)
    Write-Log $Message "INFO" $Colors.Blue
}

function Write-LogSuccess { 
    param([string]$Message)
    Write-Log $Message "SUCCESS" $Colors.Green
}

function Write-LogWarning { 
    param([string]$Message)
    Write-Log $Message "WARNING" $Colors.Yellow
}

function Write-LogError { 
    param([string]$Message)
    Write-Log $Message "ERROR" $Colors.Red
}

function Write-LogSection {
    param([string]$Title)
    Write-Host ""
    Write-Host "===================================================" -ForegroundColor $Colors.Magenta
    Write-Host $Title -ForegroundColor $Colors.Magenta
    Write-Host "===================================================" -ForegroundColor $Colors.Magenta
    Write-Host ""
}

# 检查命令是否存在
function Test-Command {
    param([string]$Command)
    
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        Write-LogSuccess "$Command 已安装"
        return $true
    }
    catch {
        Write-LogError "$Command 未找到"
        return $false
    }
}

# 检查Python模块
function Test-PythonModule {
    param([string]$Module)
    
    try {
        $result = python -c "import $Module" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Python模块 $Module 已安装"
            return $true
        }
        else {
            Write-LogError "Python模块 $Module 未找到"
            return $false
        }
    }
    catch {
        Write-LogError "Python模块 $Module 检查失败"
        return $false
    }
}

# 执行命令并检查结果
function Invoke-TestCommand {
    param(
        [string]$Command,
        [string]$Description,
        [int]$TimeoutSeconds = 0
    )
    
    Write-LogInfo "执行: $Description"
    if ($Verbose) {
        Write-Host "命令: $Command" -ForegroundColor Gray
    }
    
    try {
        if ($TimeoutSeconds -gt 0) {
            $job = Start-Job -ScriptBlock { 
                param($cmd) 
                Invoke-Expression $cmd 
            } -ArgumentList $Command
            
            if (Wait-Job $job -Timeout $TimeoutSeconds) {
                $result = Receive-Job $job
                Remove-Job $job
                
                if ($LASTEXITCODE -eq 0) {
                    Write-LogSuccess "$Description - 成功"
                    return $true
                }
                else {
                    Write-LogError "$Description - 失败 (退出码: $LASTEXITCODE)"
                    return $false
                }
            }
            else {
                Stop-Job $job
                Remove-Job $job
                Write-LogWarning "$Description - 超时 ($TimeoutSeconds 秒)"
                return $false
            }
        }
        else {
            Invoke-Expression $Command
            if ($LASTEXITCODE -eq 0) {
                Write-LogSuccess "$Description - 成功"
                return $true
            }
            else {
                Write-LogError "$Description - 失败 (退出码: $LASTEXITCODE)"
                return $false
            }
        }
    }
    catch {
        Write-LogError "$Description - 异常: $($_.Exception.Message)"
        return $false
    }
}

# 暂停等待用户输入
function Wait-UserInput {
    if (-not $SkipPause -and -not $AutoMode) {
        Write-Host ""
        Write-Host "按任意键继续..." -ForegroundColor $Colors.Cyan
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        Write-Host ""
    }
}

# ==================================================================
# 第一阶段：系统环境检查
# ==================================================================
function Test-Environment {
    Write-LogSection "第一阶段：系统环境检查"
    
    $allGood = $true
    
    # 检查基础命令
    Write-LogInfo "检查基础环境..."
    $allGood = $allGood -and (Test-Command "python")
    $allGood = $allGood -and (Test-Command "pip")
    
    # 检查Python版本
    try {
        $pythonVersion = python --version 2>&1
        Write-LogInfo "Python版本: $pythonVersion"
    }
    catch {
        Write-LogError "无法获取Python版本"
        $allGood = $false
    }
    
    # 检查关键Python模块
    Write-LogInfo "检查Python依赖模块..."
    $modules = @("numpy", "cv2", "pyrealsense2", "serial")
    foreach ($module in $modules) {
        $allGood = $allGood -and (Test-PythonModule $module)
    }
    
    # 检查项目文件结构
    Write-LogInfo "检查项目文件结构..."
    $requiredFiles = @(
        "src\main.py",
        "src\config.py", 
        "src\camera\calibration.py",
        "src\robot\communication.py",
        "src\perception\obstacle_detection.py",
        "src\perception\pipe_tracking.py",
        "src\utils\logger.py"
    )
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-LogSuccess "文件存在: $file"
        }
        else {
            Write-LogError "文件缺失: $file"
            $allGood = $false
        }
    }
    
    # 检查数据目录
    $requiredDirs = @("data\calib", "output", "tests")
    foreach ($dir in $requiredDirs) {
        if (Test-Path $dir) {
            Write-LogSuccess "目录存在: $dir"
        }
        else {
            Write-LogWarning "目录不存在: $dir (将自动创建)"
            try {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
                Write-LogSuccess "目录已创建: $dir"
            }
            catch {
                Write-LogError "无法创建目录: $dir"
                $allGood = $false
            }
        }
    }
    
    if ($allGood) {
        Write-LogSuccess "环境检查完成 - 所有检查通过！"
        return $true
    }
    else {
        Write-LogError "环境检查失败 - 请安装缺失的依赖"
        Write-Host ""
        Write-Host "安装命令建议:" -ForegroundColor $Colors.Yellow
        Write-Host "pip install pyrealsense2 opencv-python numpy pyserial"
        return $false
    }
}

# ==================================================================
# 第二阶段：配置验证测试
# ==================================================================
function Test-Configuration {
    Write-LogSection "第二阶段：系统配置验证"
    
    $success = Invoke-TestCommand "python src\main.py --config-check" "配置文件验证"
    
    if ($success) {
        Write-LogSuccess "配置验证通过"
    }
    else {
        Write-LogError "配置验证失败"
        return $false
    }
    
    Wait-UserInput
    return $true
}

# ==================================================================
# 第三阶段：单元测试
# ==================================================================
function Test-UnitTests {
    Write-LogSection "第三阶段：各模块单元测试"
    
    $testFiles = @("tests\test_camera.py", "tests\test_robot.py", "tests\test_perception.py")
    $allTestsPassed = $true
    
    foreach ($testFile in $testFiles) {
        if (Test-Path $testFile) {
            Write-LogInfo "运行测试: $testFile"
            $success = Invoke-TestCommand "python `"$testFile`"" "单元测试: $testFile"
            
            if ($success) {
                Write-LogSuccess "测试通过: $testFile"
            }
            else {
                Write-LogError "测试失败: $testFile"
                $allTestsPassed = $false
            }
            Write-Host "----------------------------------------"
        }
        else {
            Write-LogWarning "测试文件不存在: $testFile"
        }
    }
    
    if ($allTestsPassed) {
        Write-LogSuccess "所有单元测试通过！"
    }
    else {
        Write-LogError "部分单元测试失败"
        Write-LogWarning "这可能是由于硬件未连接导致的，可以继续进行系统测试"
    }
    
    Wait-UserInput
    return $true
}

# ==================================================================
# 第四阶段：系统集成测试
# ==================================================================
function Test-SystemIntegration {
    Write-LogSection "第四阶段：系统集成测试"
    
    # 演示模式测试
    Write-LogInfo "测试1: 演示模式（不显示图像）"
    Invoke-TestCommand "python src\main.py --mode demo --verbose" "演示模式测试" 30
    
    Write-Host ""
    
    # 演示模式 + 图像显示
    Write-LogInfo "测试2: 演示模式（显示图像）"
    Write-LogWarning "即将显示图像窗口，请按'q'键或等待自动结束"
    Invoke-TestCommand "python src\main.py --mode demo --display --verbose" "演示模式图像显示测试"
    
    Write-Host ""
    
    # 相机标定测试（如果有标定图片）
    $calibImages = Get-ChildItem "data\calib\*.jpg" -ErrorAction SilentlyContinue
    if ($calibImages) {
        Write-LogInfo "测试3: 相机标定测试"
        Write-LogInfo "发现标定图片，运行相机标定..."
        Invoke-TestCommand "python src\main.py --mode calib --verbose" "相机标定测试"
    }
    else {
        Write-LogWarning "测试3: 跳过相机标定（未找到标定图片）"
        Write-LogInfo "如需运行标定，请将棋盘格图片放置在 data\calib\ 目录下"
    }
    
    Wait-UserInput
    return $true
}

# ==================================================================
# 第五阶段：实际使用演示
# ==================================================================
function Start-PracticalDemo {
    Write-LogSection "第五阶段：实际使用演示"
    
    if ($AutoMode) {
        Write-LogInfo "自动模式：运行短时间追踪演示..."
        $choice = "1"
    }
    else {
        Write-Host "选择演示模式:" -ForegroundColor $Colors.Cyan
        Write-Host "1) 短时间追踪演示 (30秒)"
        Write-Host "2) 交互式追踪演示 (手动停止)"
        Write-Host "3) 仅显示状态，不运行追踪"
        Write-Host "4) 跳过此阶段"
        Write-Host ""
        $choice = Read-Host "请选择 (1-4)"
    }
    
    switch ($choice) {
        "1" {
            Write-LogInfo "运行短时间追踪演示..."
            Write-LogWarning "即将开始30秒的实时追踪，请确保相机已连接"
            Write-LogWarning "按'q'键可提前退出，或等待自动结束"
            Invoke-TestCommand "python src\main.py --mode track --display --save --verbose" "短时间追踪演示" 35
        }
        "2" {
            Write-LogInfo "运行交互式追踪演示..."
            Write-LogWarning "即将开始实时追踪，按Ctrl+C或'q'键退出"
            Invoke-TestCommand "python src\main.py --mode track --display --save --verbose" "交互式追踪演示"
        }
        "3" {
            Write-LogInfo "显示系统状态..."
            Invoke-TestCommand "python src\main.py --mode demo --verbose" "系统状态显示"
        }
        "4" {
            Write-LogInfo "跳过实际使用演示"
        }
        default {
            Write-LogWarning "无效选择，跳过此阶段"
        }
    }
    
    return $true
}

# ==================================================================
# 第六阶段：结果总结
# ==================================================================
function Show-Summary {
    Write-LogSection "第六阶段：演示总结与使用说明"
    
    Write-LogInfo "演示脚本执行完成！"
    Write-Host ""
    
    Write-Host "系统使用方法总结:" -ForegroundColor $Colors.Cyan
    Write-Host "1. 配置检查:    python src\main.py --config-check"
    Write-Host "2. 快速演示:    python src\main.py --mode demo --display"
    Write-Host "3. 相机标定:    python src\main.py --mode calib"
    Write-Host "4. 实时追踪:    python src\main.py --mode track --display --save"
    Write-Host "5. 系统测试:    python src\main.py --mode test --verbose"
    Write-Host ""
    
    Write-Host "生成的文件位置:" -ForegroundColor $Colors.Cyan
    Write-Host "- 日志文件:    output\logs\"
    Write-Host "- 追踪结果:    output\images\"
    Write-Host "- 标定数据:    data\calib\config\"
    Write-Host ""
    
    Write-Host "故障排除:" -ForegroundColor $Colors.Cyan
    Write-Host "- 相机问题:    检查RealSense驱动和pyrealsense2安装"
    Write-Host "- 机器人问题:  检查串口连接和权限（可忽略继续使用）"
    Write-Host "- 图像问题:    确保显示器支持OpenCV窗口显示"
    Write-Host ""
    
    Write-LogSuccess "感谢使用 Tiaozhanbei2.0 系统！"
    return $true
}

# ==================================================================
# 主函数
# ==================================================================
function Main {
    Write-LogSection "Tiaozhanbei2.0 系统演示脚本启动"
    
    Write-Host "本脚本将依次执行以下阶段:" -ForegroundColor $Colors.Cyan
    Write-Host "1. 系统环境检查"
    Write-Host "2. 配置验证测试"
    Write-Host "3. 各模块单元测试"
    Write-Host "4. 系统集成测试"
    Write-Host "5. 实际使用演示"
    Write-Host "6. 结果总结"
    Write-Host ""
    
    if (-not $AutoMode) {
        $confirm = Read-Host "是否继续？(y/N)"
        if ($confirm -ne "y" -and $confirm -ne "Y") {
            Write-LogInfo "用户取消执行"
            return
        }
    }
    
    # 执行各个阶段
    try {
        if (-not (Test-Environment)) {
            Write-LogError "环境检查失败，演示终止"
            return
        }
        
        if (-not (Test-Configuration)) {
            Write-LogError "配置测试失败，演示终止"
            return
        }
        
        Test-UnitTests
        Test-SystemIntegration
        Start-PracticalDemo
        Show-Summary
        
        Write-LogSuccess "演示脚本执行完成！"
    }
    catch {
        Write-LogError "脚本执行异常: $($_.Exception.Message)"
        Write-Host $_.ScriptStackTrace
    }
    finally {
        if (-not $SkipPause) {
            Read-Host "按回车键退出"
        }
    }
}

# 脚本入口点
Main
