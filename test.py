# -*- coding: utf-8 -*-
"""
Created on Thu Nov 03 22:37:04 2016

@author: rsharp
"""

from lib.util import sample_gamma
from lib.test_pyconfig import test_conf

def main():
    print sample_gamma(1.0, 2.0, size=10)
    print test_conf

if __name__ == '__main__':
    main()