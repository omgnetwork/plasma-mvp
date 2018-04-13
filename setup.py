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
        'web3==3.16.4',
        'werkzeug==0.13',
        'json-rpc==1.10.8',
        'plyvel==1.0.4',
        'py-solc',
        'click==6.7',
        'pytest',
        'eth-abi==0.5.0',
        'eth-hash==0.1.0',
        'eth-keyfile==0.4.1',
        'eth-keys==0.1.0b4',
        'eth-tester==0.1.0b15',
        'eth-utils==0.7.3'
    ],
    entry_points={
        'console_scripts': ["omg=plasma.cli:cli"],
    }
)
