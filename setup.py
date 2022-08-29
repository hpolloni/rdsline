from setuptools import setup
import os

VERSION=os.environ['PYPI_VERSION']

setup(
    name='rdsline',
    version=VERSION,
    author='Herman Polloni',
    author_email='hpolloni@gmail.com',
    description='The RDS REPL',
    entry_points = {
        'console_scripts': ['rdsline=rdsline.cli:main']
    },
    packages=['rdsline'],
    license="MIT",
    install_requires=['pyyaml', 'boto3', 'tabulate']
)
