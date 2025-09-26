@echo off
echo Instalando dependencias do RPA...
echo.

echo 1. Instalando Playwright...
pip install playwright==1.40.0

echo.
echo 2. Instalando outras dependencias...
pip install pandas==2.1.4
pip install asyncpg==0.29.0
pip install python-dotenv==1.0.0
pip install openpyxl==3.1.2

echo.
echo 3. Instalando navegadores do Playwright...
python -m playwright install chromium

echo.
echo 4. Testando instalacao...
python -c "import playwright; print('Playwright instalado com sucesso!')"

echo.
echo Instalacao concluida!
pause
