import pandas as pd

def calcula_rl(v, cv, cf, ef, taxa):
    mb = v - cv
    ro = mb - cf
    rlai = ro - ef
    i = rlai * taxa
    rl = rlai - i
    return rl

def test_rl():
    assert calcula_rl(12500,6500,3000,500,0.40) == 1500