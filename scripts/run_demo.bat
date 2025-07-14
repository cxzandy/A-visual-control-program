@echo off
:: ==================================================================
:: Tiaozhanbei2.0 项目演示脚本 (Windows版本)
:: 管道追踪与法兰识别系统 - 完整测试与使用流程
:: 
:: 功能:
:: 1. 系统环境检查
:: 2. 各模块单元测试
:: 3. 系统集成测试
:: 4. 实际使用演示
::
:: 作者: cxzandy
:: 版本: 2.0.0
:: ==================================================================

setlocal enabledelayedexpansion
chcp 65001 > nul

:: 设置项目根目录
set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

:: 颜色代码（Windows Terminal支持）
set "COLOR_RED=[31m"
set "COLOR_GREEN=[32m"
set "COLOR_YELLOW=[33m"
set "COLOR_BLUE=[34m"
set "COLOR_PURPLE=[35m"
set "COLOR_CYAN=[36m"
set "COLOR_RESET=[0m"

:: 日志函数
:log_info
echo %COLOR_BLUE%[INFO]%COLOR_RESET% %~1
exit /b

:log_success
echo %COLOR_GREEN%[SUCCESS]%COLOR_RESET% %~1
exit /b

:log_warning
echo %COLOR_YELLOW%[WARNING]%COLOR_RESET% %~1
exit /b

:log_error
echo %COLOR_RED%[ERROR]%COLOR_RESET% %~1
exit /b

:log_section
echo.
echo %COLOR_PURPLE%===================================================%COLOR_RESET%
echo %COLOR_PURPLE%%~1%COLOR_RESET%
echo %COLOR_PURPLE%===================================================%COLOR_RESET%
echo.
exit /b

:: 检查命令是否存在
:check_command
where %~1 >nul 2>&1
if %errorlevel% == 0 (
    call :log_success "%~1 已安装"
    exit /b 0
) else (
    call :log_error "%~1 未找到"
    exit /b 1
)

:: 检查Python模块
:check_python_module
python -c "import %~1" >nul 2>&1
if %errorlevel% == 0 (
    call :log_success "Python模块 %~1 已安装"
    exit /b 0
) else (
    call :log_error "Python模块 %~1 未找到"
    exit /b 1
)

:: 执行命令并检查结果
:run_command
set "cmd=%~1"
set "description=%~2"

call :log_info "执行: %description%"
echo 命令: %cmd%

%cmd%
if %errorlevel% == 0 (
    call :log_success "%description% - 成功"
    exit /b 0
) else (
    call :log_error "%description% - 失败"
    exit /b 1
)

:: 暂停等待用户输入
:pause_for_user
echo.
echo %COLOR_CYAN%按任意键继续...%COLOR_RESET%
pause >nul
exit /b

:: ==================================================================
:: 第一阶段：系统环境检查
:: ==================================================================
:phase1_environment_check
call :log_section "第一阶段：系统环境检查"

set "all_good=true"

:: 检查基础命令
call :log_info "检查基础环境..."
call :check_command "python" || set "all_good=false"
call :check_command "pip" || set "all_good=false"

:: 检查Python版本
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set "python_version=%%i"
call :log_info "Python版本: !python_version!"

:: 检查关键Python模块
call :log_info "检查Python依赖模块..."
call :check_python_module "numpy" || set "all_good=false"
call :check_python_module "cv2" || set "all_good=false"
call :check_python_module "pyrealsense2" || set "all_good=false"
call :check_python_module "serial" || set "all_good=false"

:: 检查项目文件结构
call :log_info "检查项目文件结构..."
set "required_files=src\main.py src\config.py src\camera\calibration.py src\robot\communication.py src\perception\obstacle_detection.py src\perception\pipe_tracking.py src\utils\logger.py"

for %%f in (%required_files%) do (
    if exist "%%f" (
        call :log_success "文件存在: %%f"
    ) else (
        call :log_error "文件缺失: %%f"
        set "all_good=false"
    )
)

:: 检查数据目录
set "required_dirs=data\calib output tests"
for %%d in (%required_dirs%) do (
    if exist "%%d" (
        call :log_success "目录存在: %%d"
    ) else (
        call :log_warning "目录不存在: %%d (将自动创建)"
        mkdir "%%d" >nul 2>&1
    )
)

if "%all_good%" == "true" (
    call :log_success "环境检查完成 - 所有检查通过！"
    exit /b 0
) else (
    call :log_error "环境检查失败 - 请安装缺失的依赖"
    echo.
    echo %COLOR_YELLOW%安装命令建议:%COLOR_RESET%
    echo pip install pyrealsense2 opencv-python numpy pyserial
    exit /b 1
)

:: ==================================================================
:: 第二阶段：配置验证测试
:: ==================================================================
:phase2_config_test
call :log_section "第二阶段：系统配置验证"

call :run_command "python src\main.py --config-check" "配置文件验证"
if %errorlevel% == 0 (
    call :log_success "配置验证通过"
) else (
    call :log_error "配置验证失败"
    exit /b 1
)

call :pause_for_user
exit /b 0

:: ==================================================================
:: 第三阶段：单元测试
:: ==================================================================
:phase3_unit_tests
call :log_section "第三阶段：各模块单元测试"

set "test_files=tests\test_camera.py tests\test_robot.py tests\test_perception.py"
set "all_tests_passed=true"

for %%t in (%test_files%) do (
    if exist "%%t" (
        call :log_info "运行测试: %%t"
        python "%%t"
        if !errorlevel! == 0 (
            call :log_success "测试通过: %%t"
        ) else (
            call :log_error "测试失败: %%t"
            set "all_tests_passed=false"
        )
        echo ----------------------------------------
    ) else (
        call :log_warning "测试文件不存在: %%t"
    )
)

if "%all_tests_passed%" == "true" (
    call :log_success "所有单元测试通过！"
) else (
    call :log_error "部分单元测试失败"
    call :log_warning "这可能是由于硬件未连接导致的，可以继续进行系统测试"
)

call :pause_for_user
exit /b 0

:: ==================================================================
:: 第四阶段：系统集成测试
:: ==================================================================
:phase4_integration_test
call :log_section "第四阶段：系统集成测试"

:: 演示模式测试
call :log_info "测试1: 演示模式（不显示图像）"
call :run_command "timeout /t 30 /nobreak >nul & python src\main.py --mode demo --verbose" "演示模式测试"

echo.

:: 演示模式 + 图像显示
call :log_info "测试2: 演示模式（显示图像）"
call :log_warning "即将显示图像窗口，请按'q'键或等待自动结束"
call :run_command "python src\main.py --mode demo --display --verbose" "演示模式图像显示测试"

echo.

:: 相机标定测试（如果有标定图片）
dir /b data\calib\*.jpg >nul 2>&1
if %errorlevel% == 0 (
    call :log_info "测试3: 相机标定测试"
    call :log_info "发现标定图片，运行相机标定..."
    call :run_command "python src\main.py --mode calib --verbose" "相机标定测试"
) else (
    call :log_warning "测试3: 跳过相机标定（未找到标定图片）"
    call :log_info "如需运行标定，请将棋盘格图片放置在 data\calib\ 目录下"
)

call :pause_for_user
exit /b 0

:: ==================================================================
:: 第五阶段：实际使用演示
:: ==================================================================
:phase5_practical_demo
call :log_section "第五阶段：实际使用演示"

echo %COLOR_CYAN%选择演示模式:%COLOR_RESET%
echo 1^) 短时间追踪演示 (30秒^)
echo 2^) 交互式追踪演示 (手动停止^)
echo 3^) 仅显示状态，不运行追踪
echo 4^) 跳过此阶段
echo.
set /p "choice=请选择 (1-4): "

if "%choice%" == "1" (
    call :log_info "运行短时间追踪演示..."
    call :log_warning "即将开始30秒的实时追踪，请确保相机已连接"
    call :log_warning "按'q'键可提前退出，或等待自动结束"
    call :run_command "python src\main.py --mode track --display --save --verbose" "短时间追踪演示"
) else if "%choice%" == "2" (
    call :log_info "运行交互式追踪演示..."
    call :log_warning "即将开始实时追踪，按Ctrl+C或'q'键退出"
    call :run_command "python src\main.py --mode track --display --save --verbose" "交互式追踪演示"
) else if "%choice%" == "3" (
    call :log_info "显示系统状态..."
    call :run_command "python src\main.py --mode demo --verbose" "系统状态显示"
) else if "%choice%" == "4" (
    call :log_info "跳过实际使用演示"
) else (
    call :log_warning "无效选择，跳过此阶段"
)

exit /b 0

:: ==================================================================
:: 第六阶段：结果总结
:: ==================================================================
:phase6_summary
call :log_section "第六阶段：演示总结与使用说明"

call :log_info "演示脚本执行完成！"
echo.

echo %COLOR_CYAN%系统使用方法总结:%COLOR_RESET%
echo 1. 配置检查:    python src\main.py --config-check
echo 2. 快速演示:    python src\main.py --mode demo --display
echo 3. 相机标定:    python src\main.py --mode calib
echo 4. 实时追踪:    python src\main.py --mode track --display --save
echo 5. 系统测试:    python src\main.py --mode test --verbose
echo.

echo %COLOR_CYAN%生成的文件位置:%COLOR_RESET%
echo - 日志文件:    output\logs\
echo - 追踪结果:    output\images\
echo - 标定数据:    data\calib\config\
echo.

echo %COLOR_CYAN%故障排除:%COLOR_RESET%
echo - 相机问题:    检查RealSense驱动和pyrealsense2安装
echo - 机器人问题:  检查串口连接和权限（可忽略继续使用）
echo - 图像问题:    确保显示器支持OpenCV窗口显示
echo.

call :log_success "感谢使用 Tiaozhanbei2.0 系统！"
exit /b 0

:: ==================================================================
:: 主函数
:: ==================================================================
:main
call :log_section "Tiaozhanbei2.0 系统演示脚本启动"

echo %COLOR_CYAN%本脚本将依次执行以下阶段:%COLOR_RESET%
echo 1. 系统环境检查
echo 2. 配置验证测试
echo 3. 各模块单元测试
echo 4. 系统集成测试
echo 5. 实际使用演示
echo 6. 结果总结
echo.

set /p "confirm=是否继续？(y/N): "
if /i not "%confirm%" == "y" (
    call :log_info "用户取消执行"
    exit /b 0
)

:: 执行各个阶段
call :phase1_environment_check
if %errorlevel% neq 0 (
    call :log_error "环境检查失败，演示终止"
    pause
    exit /b 1
)

call :phase2_config_test
if %errorlevel% neq 0 (
    call :log_error "配置测试失败，演示终止"
    pause
    exit /b 1
)

call :phase3_unit_tests

call :phase4_integration_test

call :phase5_practical_demo

call :phase6_summary

call :log_success "演示脚本执行完成！"
pause
exit /b 0

:: 脚本入口点
call :main %*
