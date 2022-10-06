# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import re, ast

# get version from __version__ variable in fimax/__init__.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('fimax/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

with open("requirements.txt") as f:
	requirements = f.read().strip().split("\n")

setup(
	name='fimax',
	version=version,
	description='Manage your finances with the best manager',
	author='Yefri Tavarez',
	author_email='yefritavarez@gmail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=[str(ir) for ir in requirements],
)
