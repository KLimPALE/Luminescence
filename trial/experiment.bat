@echo off
chcp 65001 >nul
title Building Experiment

echo [1/3] Сборка исполняемого файла...

pyinstaller experiment.spec --noconfirm >nul 2>&1

if errorlevel 1 (
    echo Сборка не удалась!
    exit /b 1
)

echo [OK] Сборка завершена!

echo [2/3] Копирование в корень...

copy /y "dist\Experiment.exe" "..\build\Experiment.exe" >nul 2>&1

echo [OK] Файл скопирован!

echo [3/3] Удаление временных папок...

:delete

rmdir /s /q build >nul 2>&1
rmdir /s /q dist >nul 2>&1

if exist build (
    timeout /t 1 /nobreak >nul
    goto delete
)

echo [OK] Очистка завершена!
