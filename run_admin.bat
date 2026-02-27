@echo off
echo ==============================================
echo A Iniciar Painel de Admin do SmartInvoice
echo ==============================================

:: Activar o ambiente virtual e rodar o license_admin.py a partir da pasta base
call .\venv\Scripts\activate.bat
python license_admin.py

pause
