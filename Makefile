
check:
	.venv/bin/python -m pytest 
	.venv/bin/python -m mypy rdsline
	.venv/bin/python -m black -l 100 rdsline
	.venv/bin/python -m black -l 100 --check rdsline
	.venv/bin/python -m pylint rdsline
	
setup-dev:
	python -m venv .venv
	.venv/bin/python -m pip install -r requirements.txt

dist: check
	.venv/bin/python setup.py sdist

pypi: dist
	twine upload dist/rdsline-${PYPI_VERSION}.tar.gz
