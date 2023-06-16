#!/usr/bin/env python

from setuptools import setup, find_packages

requirements = [x.strip() for x in open("requirements.txt", "r").readlines()]

setup(name='Conanmail',
      version='1.0.19',
      description='Helping you delete your old accounts',
      author='Gobutsu',
      packages=find_packages(),
      url='https://github.com/Gobutsu/Conan',
      install_requires=requirements,
      package_data={'conan': ['IMAP.json', 'web/*']},
      entry_points={
            'console_scripts': [
                    'conan = conan.main:main'
            ]
        },
      python_requires='>=3.6'
)