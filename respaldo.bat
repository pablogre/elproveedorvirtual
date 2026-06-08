@echo off
setlocal enabledelayedexpansion

:: Configuraci�n
set MYSQL_USER=root
set MYSQL_PASS=admin123
set BACKUP_DIR=C:\backups

:: Bases a backupear (una por l�nea)
set BASES=factufacil siamotre schiro carnave midoctor panel_factufacil

:: Generar fecha YYYYMMDD_HHMM
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set dt=%%I
set FECHA=%dt:~0,8%_%dt:~8,4%

:: Crear carpeta del d�a
if not exist "%BACKUP_DIR%\%FECHA:~0,8%" mkdir "%BACKUP_DIR%\%FECHA:~0,8%"

:: Loop por cada base
for %%B in (%BASES%) do (
    echo Backupeando %%B...
    mysqldump -u %MYSQL_USER% -p%MYSQL_PASS% --single-transaction --routines --triggers %%B > "%BACKUP_DIR%\%FECHA:~0,8%\%%B_%FECHA%.sql"
    if !errorlevel! equ 0 (
        echo OK %%B
    ) else (
        echo ERROR en %%B
    )
)

:: Borrar backups de mas de 14 dias
forfiles /p "%BACKUP_DIR%" /d -14 /c "cmd /c if @isdir==TRUE rd /s /q @path" 2>nul

echo.
echo Backup completo en %BACKUP_DIR%\%FECHA:~0,8%
pause
