@echo off
set MODELSIM_HOME=D:\questasim
set INCLUDE_PATH=%MODELSIM_HOME%\include
set GCC_PATH=%~dp0gcc_toolchain\gcc-4.5.0-mingw64vc12\bin
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
