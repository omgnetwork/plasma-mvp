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
        'ethereum==2.1.3',
        'click==6.7',
    ],
    # entry_points="""
    #     [console_scripts]
    #     pm=plasma.cli:main
    # """,
    entry_points={
        'console_scripts': ["pm=plasma.cli:main"],
    }
)
