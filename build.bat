@echo off
setlocal enabledelayedexpansion

echo Running tests with coverage...
pytest --cov=drawer --cov=app --cov=controllers --cov=routes --cov-report term --cov-report html > coverage_output.txt

if %ERRORLEVEL% neq 0 (
    echo Tests failed, docker build will not be executed
    exit /b 1
)

echo Extracting coverage percentage...
for /f "tokens=4 delims= " %%a in ('type coverage_output.txt ^| find "TOTAL"') do (
    set coverage=%%a
    set coverage=!coverage:~0,-1!
)

echo Total coverage: !coverage!%%

if !coverage! gtr 55 (
    echo Total coverage is >= 55%%
    echo STARTING DOCKER BUILD
    docker build -t flask-report:test .
) else (
    echo Total coverage is insufficient docker build CANCELED
    exit /b 1
)

del coverage_output.txt
del 70%%
del 68%%
del 55%%


cd C:\Users\Aleksandr\Documents\Work\ServerPTZ

docker compose -f docker-compose.yml up -d --build