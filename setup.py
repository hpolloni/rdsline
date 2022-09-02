from setuptools import setup
from rdsline.version import VERSION

setup(
    name='rdsline',
    version=VERSION,
    author='Herman Polloni',
    author_email='hpolloni@gmail.com',
    description='The RDS REPL',
    entry_points = {
        'console_scripts': ['rdsline=rdsline.cli:main']
    },
    packages=['rdsline', 'rdsline.connections'],
    license="MIT",
    url='https://github.com/hpolloni/rdsline',
    long_description='RDS REPL',
    install_requires=['pyyaml', 'boto3', 'tabulate']
)
