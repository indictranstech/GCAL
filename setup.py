# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

version = '0.0.1'

setup(
    name='gcal',
    version=version,
    description='Sync Google Calender',
    author='New Indictrans Technologies Pvt Ltd',
    author_email='makarand.b@indictranstech.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=("frappe",),
)
