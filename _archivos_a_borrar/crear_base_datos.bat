@echo off
title Crear Base de Datos - POS
echo ================================
echo CREAR BASE DE DATOS EN BLANCO
echo ================================
echo.

REM Pedir nombre de base de datos
set /p NOMBRE_BD="Ingresa el nombre de la base de datos (ej: schiro): "

if "%NOMBRE_BD%"=="" (
    echo Error: el nombre no puede estar vacio
    pause
    exit /b 1
)

echo.
echo Se va a crear la base de datos: %NOMBRE_BD%
echo Usuario: pos_user
echo Password: pos_password
echo.
pause

REM Crear script SQL
echo CREATE DATABASE IF NOT EXISTS %NOMBRE_BD% CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; > "%TEMP%\setup_bd.sql"
echo CREATE USER IF NOT EXISTS 'pos_user'@'localhost' IDENTIFIED BY 'pos_password'; >> "%TEMP%\setup_bd.sql"
echo GRANT ALL PRIVILEGES ON %NOMBRE_BD%.* TO 'pos_user'@'localhost'; >> "%TEMP%\setup_bd.sql"
echo FLUSH PRIVILEGES; >> "%TEMP%\setup_bd.sql"

echo Creando base de datos...
"C:\Program Files\MariaDB 11.1\bin\mysql.exe" -u root -padmin123 < "%TEMP%\setup_bd.sql"

if %errorlevel% equ 0 (
    echo.
    echo ================================
    echo BASE DE DATOS CREADA OK
    echo ================================
    echo Nombre:   %NOMBRE_BD%
    echo Usuario:  pos_user
    echo Password: pos_password
    echo Host:     localhost
    echo ================================
) else (
    echo.
    echo Error al crear la base de datos.
    echo Verificar que MariaDB este corriendo: net start MariaDB
)

del "%TEMP%\setup_bd.sql" 2>nul
echo.
pause
