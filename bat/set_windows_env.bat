@echo off
title "DavinciResolve Enviroment Variable Setter"
echo .:: DavinciResolve Enviroment Variable Setter ::.
echo.

echo [info] Make sure that you have the correct version of python [3.6.x] which works with Resolve 17. If not please install correct one. Don't choose version diffrent than [3.6.x]
echo.
echo Looking for Python...
echo.
where python > nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Version:
 	FOR /F %%a in ('where python') DO %%a --version & echo %%a & echo.
    echo.
	set /p PYTHONPATH="Choose and enter python path: " 
	echo.
) else (
	echo [!] Python has not been found! Install Python x64 3.6.x and try again.
	echo.
)
echo Setting RESOLVE_SCRIPT_API...
setx RESOLVE_SCRIPT_API "%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\
if %ERRORLEVEL% EQU 0 (echo ----------------------------------------------) else (echo FAILED)
echo.
echo Setting RESOLVE_SCRIPT_LIB...
setx RESOLVE_SCRIPT_LIB "C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
if %ERRORLEVEL% EQU 0 (echo ----------------------------------------------) else (echo FAILED)
echo.
echo Setting PYTHONPATH...
setx PYTHONPATH "%PYTHONPATH%";"%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules\
if %ERRORLEVEL% EQU 0 (echo ----------------------------------------------) else (echo FAILED)

pause