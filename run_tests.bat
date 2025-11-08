@echo off
REM Windows batch file for running Aegis tests
REM Usage: run_tests.bat [command]

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="test" goto test
if "%1"=="test-unit" goto test-unit
if "%1"=="test-fast" goto test-fast
if "%1"=="test-cov" goto test-cov
if "%1"=="lint" goto lint
if "%1"=="format" goto format
if "%1"=="clean" goto clean
if "%1"=="setup" goto setup
goto help

:help
echo Aegis Test Commands (Windows)
echo =============================
echo.
echo Setup:
echo   run_tests.bat setup       Set up development environment
echo.
echo Testing:
echo   run_tests.bat test        Run all tests
echo   run_tests.bat test-unit   Run unit tests only
echo   run_tests.bat test-fast   Run fast tests (no API calls)
echo   run_tests.bat test-cov    Run tests with coverage
echo.
echo Code Quality:
echo   run_tests.bat lint        Run linters
echo   run_tests.bat format      Format code
echo.
echo Cleanup:
echo   run_tests.bat clean       Remove generated files
echo.
goto end

:setup
echo Setting up development environment...
if not exist "config\credentials" mkdir config\credentials
if not exist "data\cache\fred" mkdir data\cache\fred
if not exist "data\cache\yahoo" mkdir data\cache\yahoo
if not exist "data\history" mkdir data\history

if not exist "config\credentials\secrets.ini" (
    echo Copying secrets template...
    copy config\credentials\secrets.ini.example config\credentials\secrets.ini
    echo.
    echo WARNING: Please edit config\credentials\secrets.ini and add your API keys
)

pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock black isort flake8 mypy
echo.
echo Development environment ready!
goto end

:test
echo Running all tests...
pytest
goto end

:test-unit
echo Running unit tests...
pytest -m unit -v
goto end

:test-fast
echo Running fast tests (no API, no secrets)...
pytest -m "not api and not requires_secrets and not slow" -v
goto end

:test-cov
echo Running tests with coverage...
pytest --cov=src --cov-report=html --cov-report=term-missing
echo.
echo Coverage report generated in htmlcov\
echo Open htmlcov\index.html in your browser
start htmlcov\index.html
goto end

:lint
echo Running linters...
flake8 src\ tests\ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 src\ tests\ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
echo.
mypy src\ --ignore-missing-imports --no-strict-optional
goto end

:format
echo Formatting code...
black src\ tests\
echo.
isort --profile black src\ tests\
echo Done!
goto end

:clean
echo Cleaning up...
if exist "__pycache__" rmdir /s /q __pycache__
if exist ".pytest_cache" rmdir /s /q .pytest_cache
if exist ".mypy_cache" rmdir /s /q .mypy_cache
if exist "htmlcov" rmdir /s /q htmlcov
if exist ".coverage" del .coverage
if exist "coverage.xml" del coverage.xml
if exist "coverage.json" del coverage.json
echo Clean complete!
goto end

:end
