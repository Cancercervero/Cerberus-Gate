@echo off
title Lanzador Maestro - Cerberus Gate
color 0e

echo =======================================================
echo [⚙️] FASE 1/5: LIMPIEZA TACTICA (Purgando La Pecera)
echo =======================================================
echo Buscando instancias fantasmas del Muro Blindado...
taskkill /F /FI "WINDOWTITLE eq Muro Blindado*" /T >nul 2>&1
echo Buscando contenedores "cerebro_naranja" huerfanos...
docker stop cerebro_naranja >nul 2>&1
docker rm cerebro_naranja >nul 2>&1
echo [+] Limpieza completada.

echo.
echo =======================================================
echo [🔨] FASE 2/5: FORJANDO EL ACERO (Compilacion Docker)
echo =======================================================
docker build -t lnm-pecera -f .\brain_core\Dockerfile .
if %ERRORLEVEL% neq 0 (
    echo [!] Error critico compilando la imagen de La Pecera.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =======================================================
echo [🌊] FASE 3/5: INMERSION Y BARRERAS (Levantando Nodos)
echo =======================================================
echo Elevando Muro Blindado [Windows Host/GPU] en Terminal 1...
start "Muro Blindado (Host en localhost:50051)" cmd /k "python host_engine\grpc_server.py"

echo Sumergiendo el Cerebro Aislado [La Pecera] en Terminal 2...
start "La Pecera (Linux Sandbox en puente 50052)" cmd /k "docker run -it --rm --name cerebro_naranja -p 50052:50051 lnm-pecera"

echo.
echo =======================================================
echo [⏱️] FASE 4/5: SINCRONIZACION SECUENCIAL
echo =======================================================
echo Esperando al hipervisor para calentar motores (4 Segundos)...
timeout /t 4 /nobreak >nul

echo.
echo =======================================================
echo [👁️] FASE 5/5: DESPERTAR CENTINELA (Front-End)
echo =======================================================
echo Lanzando HUD Fantasma en este hilo...
python ui_core\hud_fantasma.py

echo.
echo [!] Fin de secuencia. El Orbe ha cerrado su ciclo.
pause
