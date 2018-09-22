'''
Created on 11-Aug-2018

@author: vipultanwar
'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from StdSuites.Table_Suite import row
from pandas.io.data import _adjust_prices
from matplotlib.pyplot import draw


############    Data reading and formatting   #############


df = pd.read_csv("BitOHLC.csv")
#conveting string values to numeric
#df = pd.read_csv("NIFTY_EOD.csv")
df['Open'] = pd.to_numeric(df['Open'])
df['High'] = pd.to_numeric(df['High'])
df['Low'] = pd.to_numeric(df['Low'])
df['Close'] = pd.to_numeric(df['Close'])

cols = ['Open', 'High','Low','Close']  

print df.head()
