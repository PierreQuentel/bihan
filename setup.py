# Always prefer setuptools over distutils
from setuptools import setup, find_packages

import os

with open('README.rst', encoding='utf-8') as fobj:
    LONG_DESCRIPTION = fobj.read()

setup(
    name='bihan',

    version='0.0.5',

    description='Minimalist Python web framework',
    
    long_description = LONG_DESCRIPTION,

    # The project's main homepage.
    url='https://github.com/PierreQuentel/bihan',

    # Author details
    author='Pierre Quentel',
    author_email='quentel.pierre@orange.fr',
    
    # Choose your license
    license='BSD',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Interpreters',
        
        'Operating System :: OS Independent',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
    ],

    # What does your project relate to?
    keywords='Python web',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    # packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    py_modules=["bihan"]

)