@echo off
echo ==============================================
echo  Compilador do SmartInvoice
echo ==============================================

echo A limpar builds anteriores...
rmdir /s /q build dist 2>nul
del /q SmartInvoice.spec 2>nul

echo A compilar a aplicacao principal...
:: --noconfirm forca override se existir a build
:: --windowed esconde a janela da consola em segundo plano
:: --name altera o nome do exe gerado

call .\venv\Scripts\pyinstaller --noconfirm --windowed --name "SmartInvoice" main.py

echo.
echo ==============================================
echo Compilacao terminada. O executavel encontra-se na pasta "dist\SmartInvoice".
echo Nota: Nao te esquecas de entregar o executavel COM a instrucaçao para instalar o Tesseract-OCR no cliente.
echo ==============================================
pause
