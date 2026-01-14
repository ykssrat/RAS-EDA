@echo off
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

set CONFIG_FILE=%SCRIPT_DIR%config.json
for /f "usebackq tokens=* delims=" %%i in (`py -c "import json;cfg=json.load(open(r'%CONFIG_FILE%','r'));print(cfg.get('modelsim_home',''))"`) do set "MODELSIM_HOME=%%i"
for /f "usebackq tokens=* delims=" %%i in (`py -c "import json;cfg=json.load(open(r'%CONFIG_FILE%','r'));print(cfg.get('license_file',''))"`) do set "LICENSE_FILE=%%i"

if not defined MODELSIM_HOME (
    echo Error: modelsim_home not set in config.json
    exit /b 1
)

rem If license_file is provided, set both Mentor and LM license variables
if defined LICENSE_FILE (
    set "MGLS_LICENSE_FILE=%LICENSE_FILE%"
    set "LM_LICENSE_FILE=%LICENSE_FILE%"
)

rem 接受参数：第一个参数是 testbench 模块名
set TB_MODULE=%1
if "%TB_MODULE%"=="" (
    echo Error: No testbench module specified.
    echo Usage: run_modelsim.bat ^<testbench_module^>
    exit /b 1
)

rem Configure Questasim installation paths
set VSIM_BIN=%MODELSIM_HOME%\win64
set PATH=%VSIM_BIN%;%PATH%

rem Avoid non-ASCII temp paths causing "stdout stream" reopen errors
set TEMP=%SCRIPT_DIR%tmp
set TMP=%TEMP%
if not exist "%TEMP%" mkdir "%TEMP%"

rem 1. Compile Verilog
if not exist "work" (
    vlib work
)

echo Compiling Verilog...
vlog -f circuit/verilog_file.f

rem 2. Run Simulation
echo Running Simulation...
rem -c: Command line mode
rem -do: Execute TCL script
rem -pli: Load PLI DLL
vsim -c -pli clibrary/pli.dll -do run.tcl %TB_MODULE%

