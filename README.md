# SETUP

Install `requirements.txt`. Tabula-py requires java [development](https://www.oracle.com/java/technologies/downloads/#jdk20-windows) which must be installed **additionally**.
To package you need pyinstaller and pillow.
Packing from virtual environment does not seem to work on windows.
On Windows tabulapy needs to be included explicitly, eg:
```cmd
flet pack .\flet_main.py --name "BikeIdent Database Editor" --icon .\favicon_bikeident.ico --add-data "C:\Users\Julian\anaconda3\Lib\site-packages\tabula\tabula-1.0.5-jar-with-dependencies.jar;tabula"
```
or on linux:
```cmd
flet pack flet_main.py --name "BikeIdent Database Editor" --icon .\favicon_bikeident.ico --add-data "venv/lib/python*/site-packages/tabula/tabula-1.0.5-jar-with-dependencies.jar:tabula"
```
See [stackoverflow](https://stackoverflow.com/questions/56550410/unable-to-execute-my-script-when-converting-it-to-exe)
