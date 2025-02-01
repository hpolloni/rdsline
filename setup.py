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
    install_requires=['pyyaml', 'boto3', 'tabulate'],
    python_requires='>=3.8',
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
)
