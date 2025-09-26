@echo off
echo Instalando dependencias do RPA...
echo.

echo 1. Instalando Playwright...
pip install playwright

echo.
echo 2. Instalando outras dependencias...
pip install pandas
pip install asyncpg
pip install python-dotenv
pip install openpyxl

echo.
echo 3. Instalando navegadores...
python -m playwright install chromium

echo.
echo 4. Testando...
python -c "import playwright; print('Playwright OK!')"

echo.
echo Instalacao concluida!
pause
