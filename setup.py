from setuptools import setup
import subprocess

VERSION='0.4dev1'

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
    install_requires=['pyyaml', 'boto3']
)
