# -*- coding: utf-8 -*-
from distutils.core import setup
from Cython.Build import cythonize

fileList = ["_CoWbUnit.py", "Errors.py"]

setup(
    ext_modules=cythonize(fileList)
)
