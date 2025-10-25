:: 分步创建多级目录（不依赖/p参数，兼容性更好）
md build1
md build1\bin
md build1\bin\weather
md build1\bin\totp
md build1\bin\pstool

:: 打包各程序（路径统一用反斜杠）
pyinstaller --onefile --noconsole --icon=icon.ico --uac-admin --add-data "main.ui;." --add-data "icon.ico;." --add-data "setting.ui;." main.py
pyinstaller --onefile --noconsole --icon=icon.ico --uac-admin --add-data "icon.ico;." system_tpp.py
pyinstaller --onefile --noconsole --uac-admin --add-data "bin\weather\main.ui;." --add-data "bin\weather\weather\*;weather" --add-data "bin\weather\icon.ico;." --icon "bin\weather\icon.ico" bin\weather\weathers.py
pyinstaller --onefile --noconsole --uac-admin bin\totp\totp.py
pyinstaller --onefile --noconsole --uac-admin uninstall\uninstall.py

:: 修复copy命令（补全扩展名、修正目标路径）
copy dist\weathers.exe build1\bin\weather\weathers.exe
copy dist\totp.exe build1\bin\totp\totp.exe
:: 修正pstool复制目标（复制到目录下，而非重命名为pstool）
copy bin\pstool\*.exe build1\bin\pstool\
:: 补全最后一个不完整的copy命令（复制卸载程序）
copy dist\uninstall.exe build1\uninstall.exe
copy dist\main.exe build1\main.exe