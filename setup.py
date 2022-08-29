from setuptools import setup

setup(
    name='rdsline',
    version='0.4.2',
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
