check:
	.venv/bin/python -m mypy rdsline
	.venv/bin/python -m black -l 100 rdsline
	.venv/bin/python -m black -l 100 --check rdsline
	.venv/bin/python -m pylint rdsline
	.venv/bin/coverage run -m pytest
	.venv/bin/coverage report -m
	
setup-dev:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements.txt

test:
	.venv/bin/python -m pytest
