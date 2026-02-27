@echo off
echo ==============================================
echo A Iniciar a Aplicacao SmartInvoice
echo ==============================================

:: Activar o ambiente virtual e rodar o main.py a partir da pasta base
call .\venv\Scripts\activate.bat
python main.py

pause
