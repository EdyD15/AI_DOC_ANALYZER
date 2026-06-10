@echo off
echo Building DocuMind.exe ...
pip install pyinstaller --quiet
pyinstaller --onefile --noconsole --name DocuMind launcher.py
echo.
echo Done! Executabilul se afla la: dist\DocuMind.exe
echo Copiaza dist\DocuMind.exe pe desktop si porneste aplicatia de acolo.
pause
