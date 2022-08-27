from setuptools import setup

setup(
    name='rdsline',
    version='0.2',
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