@echo off
setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"
set CONFIG_FILE=%SCRIPT_DIR%config.json

for /f "usebackq tokens=* delims=" %%i in (`py -c "import json;import pathlib;cfg=json.load(open(r'%CONFIG_FILE%','r'));print(cfg.get('modelsim_home',''))"`) do set "MODELSIM_HOME=%%i"
for /f "usebackq tokens=* delims=" %%i in (`py -c "import json;import pathlib;cfg=json.load(open(r'%CONFIG_FILE%','r'));print(cfg.get('gcc_path',''))"`) do set "GCC_PATH=%%i"
for /f "usebackq tokens=* delims=" %%i in (`py -c "import json;cfg=json.load(open(r'%CONFIG_FILE%','r'));print(cfg.get('license_file',''))"`) do set "LICENSE_FILE=%%i"

if not defined MODELSIM_HOME (
    echo [Error] modelsim_home not set in config.json
    exit /b 1
)

if not defined GCC_PATH (
    echo [Error] gcc_path not set in config.json
    exit /b 1
)

rem If license_file is provided, set both Mentor and LM license variables for consistency during link
if defined LICENSE_FILE (
    set "MGLS_LICENSE_FILE=%LICENSE_FILE%"
    set "LM_LICENSE_FILE=%LICENSE_FILE%"
)

set INCLUDE_PATH=%MODELSIM_HOME%\include
set PATH=%GCC_PATH%;%PATH%

echo Compiling C code for ModelSim PLI...

gcc -c -I"%INCLUDE_PATH%" -o clibrary/cJSON.o clibrary/cJSON.c
gcc -c -I"%INCLUDE_PATH%" -o clibrary/function.o clibrary/function.c
gcc -c -I"%INCLUDE_PATH%" -o clibrary/main.o clibrary/main.c
gcc -c -I"%INCLUDE_PATH%" -o clibrary/modelsim_pli.o clibrary/modelsim_pli.c

echo Linking DLL...
gcc -shared -o clibrary/pli.dll clibrary/cJSON.o clibrary/function.o clibrary/main.o clibrary/modelsim_pli.o -L"%MODELSIM_HOME%\win64" -lmtipli

if %errorlevel% neq 0 (
    echo Build Failed!
    exit /b %errorlevel%
)

echo Build Success! pli.dll created.
del clibrary\*.o
endlocal
