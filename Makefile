all:run

run:
	python main.py

exe:
	pyinstaller --onefile --noconsole --uac-admin main.py
	pyinstaller --onefile --noconsole --uac-admin --dat bin/weather/main.py

clean:
	rm -rf *.pyc