call py -m ensurepip --upgrade
call python.exe -m pip install --upgrade pip
call python -m venv venv
call venv/Scripts/activate
call pip install -r requirements.txt
call pip-review --local --auto
pause