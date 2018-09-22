'''
Created on 01-Aug-2018

@author: vipultanwar
'''
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from StdSuites.Table_Suite import row


#Data reading and formatting
df = pd.read_csv("NIFTY_EOD.csv")
df['Open'] = pd.to_numeric(df['Open'],errors='coerce')
df['High'] = pd.to_numeric(df['High'],errors='coerce')
df['Low'] = pd.to_numeric(df['Low'],errors='coerce')
df['Close'] = pd.to_numeric(df['Close'],errors='coerce')
'''
startdate = datetime.datetime.strptime(df['Date'].iloc[0], "%m/%d/%Y").date()
enddate = datetime.datetime.strptime(df['Date'].iloc[-1], "%m/%d/%Y").date()
'''
df['LastMin'] = df['Low'].rolling(30).min
df['LastMax'] = df['High'].rolling(30).max

#Marking buy and sell signal according to alpha output
df['Signal'] = 0
df.loc[, 'Signal'] = -1
df.loc[(df['LongTermSlope'] < 0) &  (df['ShortTermSlope'] > 0), 'Signal'] = 1 


signal2 =[]

current =0
for row in df['Signal']:
    if row == current:
        signal2.append(0) 
    else:
        signal2.append(row)
        if(row!= 0):
            current = row
#df['Signal2'] = signal2    
df['Signal'] = signal2     
buys = df.ix[df['Signal'] == 1]
sells = df.ix[df['Signal'] == -1]

#Plot the close prices
plt.plot(df.index, df['Close'], label='Close')
# Plot the buy and sell signals on the same plot
plt.plot(sells.index, df.ix[sells.index]['Close'], 'v', markersize=10, color='r')
plt.plot(buys.index, df.ix[buys.index]['Close'], '^', markersize=10, color='g')
plt.ylabel('Price')
plt.xlabel('Date')
plt.legend(loc=0)
# Display everything
plt.show()

print df.head(39)






'''



df['LongTermSlope'] = df['Close'].diff(LongInterval)
df['ShortTermSlope'] = df['Close'].diff(ShortInterval)
df['SlopeRatio'] = df['ShortTermSlope']/df['LongTermSlope'] 

#Marking buy and sell signal according to alpha output
df['Signal'] = 0

df.loc[df['SlopeRatio'] > triggerfactor, 'Signal'] = -1
df.loc[df['SlopeRatio'] < (1/triggerfactor), 'Signal'] = 1

#df.loc[(df['ShortTermSlope']/df['LongTermSlope']), 'Signal'] = -1


############################################################
signal2 =[]

current =0
for row in df['Signal']:
    if row == current:
        signal2.append(0) 
    else:
        signal2.append(row)
        if(row!= 0):
            current = row
#df['Signal2'] = signal2    
df['Signal'] = signal2     
buys = df.ix[df['Signal'] == 1]
sells = df.ix[df['Signal'] == -1]
'''
############################################################
