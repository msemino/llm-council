@echo off
title LLM Council
echo =========================================
echo   LLM Council - Starting...
echo =========================================
echo.

:: Start backend
echo Starting backend on http://localhost:8001...
start "LLM Council Backend" cmd /k "cd /d D:\llm-council && uv run python -m backend.main"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend
echo Starting frontend on http://localhost:5173...
start "LLM Council Frontend" cmd /k "cd /d D:\llm-council\frontend && npm run dev"

echo.
echo =========================================
echo   LLM Council is running!
echo   Backend:  http://localhost:8001
echo   Frontend: http://localhost:5173
echo =========================================
echo.
echo Open http://localhost:5173 in your browser
echo Close the backend and frontend windows to stop
pause
