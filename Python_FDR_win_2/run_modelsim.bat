@echo off
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

rem 接受参数：第一个参数是 testbench 模块名
set TB_MODULE=%1
if "%TB_MODULE%"=="" (
    echo Error: No testbench module specified.
    echo Usage: run_modelsim.bat ^<testbench_module^>
    exit /b 1
)

rem Configure Questasim installation paths
set MODELSIM_HOME=D:\questasim
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

