# -*- coding: utf-8 -*-

import os
import pytest
import sys


@pytest.fixture(scope='module')
def plonecli_bin():
    bin_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    plonecli_bin = bin_path + '/plonecli'
    print('plonebin path: ' + plonecli_bin)
    yield plonecli_bin
