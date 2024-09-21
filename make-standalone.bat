mkdir build
mkdir dist
python setup-cxfreeze.py build_exe --build-exe=build\windows
mkdir build\windows\bin
copy TaskbarLib.tlb build\windows
copy bin\win32\save3ds_fuse.exe build\windows\bin
copy bin\README build\windows\bin
copy custom-install-finalize.3dsx build\windows
copy title.db.gz build\windows
copy extras\windows-quickstart.txt build\windows
copy extras\run_with_cmd.bat build\windows
copy LICENSE.md build\windows
python -m zipfile -c dist\windows.zip build\windows
