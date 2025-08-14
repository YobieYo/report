@echo off
setlocal enabledelayedexpansion

echo Running tests with coverage...
pytest > coverage_output.txt 2>&1

if %ERRORLEVEL% neq 0 (
    echo Tests failed, docker build will not be executed
    type coverage_output.txt
    exit /b 1
)

echo Extracting coverage percentage...
for /f "tokens=*" %%a in ('findstr /C:"TOTAL" coverage_output.txt') do (
    for /f "tokens=4" %%b in ("%%a") do (
        set coverage=%%b
        set coverage=!coverage:~0,-1!
    )
)

if not defined coverage (
    echo Could not determine coverage from output:
    type coverage_output.txt
    exit /b 1
)

echo Total coverage: !coverage!%%

if !coverage! geq 55 (
    echo Coverage is sufficient (^>=55%%^). Building Docker...
    docker build -t flask-report:test .
    cd C:\Users\Aleksandr\Documents\Work\ServerPTZ
    docker compose -f docker-compose.yml up -d --build
) else (
    echo Coverage is too low (^<55%%^). Docker build canceled.
    exit /b 1
)



del coverage_output.txt