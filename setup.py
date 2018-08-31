# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

setup(
    name='plasma',
    description='Plasma MVP',
    long_description=readme,
    author='David Knott',
    author_email='',
    license=license,
    packages=find_packages(exclude=('tests')),
    include_package_data=True,
    install_requires=[
        'ethereum==2.3.0',
        'web3==4.5.0',
        'werkzeug==0.14.1',
        'json-rpc==1.10.8',
        'py-solc',
        'click==6.7',
        'pytest',
        'flake8==3.5.0',
        'rlp==0.6.0'
    ],
    entry_points={
        'console_scripts': ["omg=plasma.cli:cli"],
    }
)
