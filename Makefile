
dist:
	python setup.py sdist

testpypi: dist
	twine upload --repository testpypi dist/rdsline*.tar.gz

pypi: dist
	twine upload dist/rdsline*.tar.gz
