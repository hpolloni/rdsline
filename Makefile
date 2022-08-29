
check:
	.venv/bin/python -m pytest 
	.venv/bin/python -m mypy rdsline
	.venv/bin/python -m black -l 100 rdsline
	.venv/bin/python -m black -l 100 --check rdsline
	.venv/bin/python -m pylint rdsline
	
setup-dev:
	python -m venv .venv
	.venv/bin/python -m pip install -r requirements.txt
