rd /S /Q .\dist\application
rd /S /Q .\build\application
rem pyinstaller --windowed --icon=resources\fish.ico --version-file=version.txt CamtrawlBrowser.pyw
pyinstaller SEBASTES.spec
rem /E copies the subfolders too: resources\icons holds the SVG icons that theme.py draws
md .\dist\application\resources
xcopy /E resources .\dist\application\resources
md .\dist\application\schema
xcopy /E schema .\dist\application\schema
rem md .\dist\SEBASTES\configuration
rem xcopy /E configuration .\dist\SEBASTES\configuration
rem md .\dist\SEBASTES\manual
rem xcopy /E manual .\dist\SEBASTES\manual
rem md .\dist\SEBASTES\examples
rem xcopy /E examples .\dist\SEBASTES\examples
rem md .\dist\SEBASTES\logs

