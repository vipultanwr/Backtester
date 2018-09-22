import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from StdSuites.Table_Suite import row
from pandas.io.data import _adjust_prices

############    Data reading and formatting   #############

df = pd.read_csv("NIFTY_EOD.csv")
df['Open'] = pd.to_numeric(df['Open'],errors='coerce')
df['High'] = pd.to_numeric(df['High'],errors='coerce')
df['Low'] = pd.to_numeric(df['Low'],errors='coerce')
df['Close'] = pd.to_numeric(df['Close'],errors='coerce')

############################################################


############    Input Parameters,Assumptions   #############

startdate = datetime.datetime.strptime(df['Date'].iloc[0], "%m/%d/%Y").date()
enddate = datetime.datetime.strptime(df['Date'].iloc[-1], "%m/%d/%Y").date()

transactioncost = 0.0002  #Transaction in actual fraction(not bps)
InitialCapital = 10000000 #Initial Portfolio Capital  
Margin = 0.1
LotSize = 75
PositionSize = 100*LotSize       #Order Size 
riskfreeint = 6.85        #Risk free interest rate
ShortInterval = 3
LongInterval = 15
triggerfactor = 0.005
MaxVaR = 0.5
MinVaR = 0.1
DefaultRatio  = 0.6
############################################################


########## Strategy definition and application  ############

def KellyPosition(data):
    #W = Winning probability (count wins/count losses)
    #R = win/loss amount ratio
        
    p = 0
    l = 0

    for val in data:
        #print val
        if val > 0:
            p+=val
        elif val< 0:
            l-=val
                
    if(p==0 and l == 0):
        return MaxVaR
    else:   
        W = float(sum(n>0 for n in data))/float(sum(n!=0 for n in data))
        R = p/(DefaultRatio*p if l == 0 else l )
        #print str(W) + " " + str(R)
        #print W-((1-W)/R)
        return min(MaxVaR,(MinVaR if (W-((1-W)/R)) < 0 else (W-((1-W)/R))))
        
    
    

def MA50(self):
    df['Signal'] = 0
    df['MA50'] = df['Close'].rolling(15).mean()
    df.loc[((df['MA50'] - df['Close'])/df['MA50']) > triggerfactor,'Signal'] = 1
    df.loc[((df['Close'] - df['MA50'])/df['MA50']) > triggerfactor,'Signal'] = -1
    signal2 =[]

    current =0
    for row in df['Signal']:
        if row == current:
            signal2.append(0) 
        else:
            signal2.append(row)
            if(row!= 0):
                current = row
    df['Signal'] = signal2 
    
    
MA50(df)

############################################################

'''

cash = InitialCapital/Margin
position = 0
total = 0

buyprc = 0     
winlose = 0
W= 0
R= 0
df['Total'] = InitialCapital
df['BuyHold'] = InitialCapital
df['Win/Lose'] = 0
empty = []
# To compute the Buy and Hold value, I invest all of my cash in the Close on the first day of the backtest
positionBeginning = round(InitialCapital/float(df.iloc[0]['Open'])/LotSize)*LotSize
increment = cash*KellyPosition(empty)
     
for row in df.iterrows():
    price = float(row[1]['Close'])
    signal = float(row[1]['Signal'])
    increment = round(cash*KellyPosition(df['Win/Lose'].loc[:row[0]])/price/LotSize)*LotSize
    if(signal > 0 and cash - increment * price > 0):
        # Buy
        buyprc = price
        buyqty = increment
        cash = cash - (increment * price*(1 + transactioncost))
        position = position + increment
        
        print("BUY: "+str(row[0])+" "+str(int(position))+"@ "+str(price) + " Cash= "+str(cash)+" // Total = {:,}".format(int(position*price+cash)))
         
    elif(signal < 0  and position != 0):
        # Sell
        df.loc[df.index == row[0], 'Win/Lose'] += buyqty*(price-buyprc)
        cash = cash + (buyqty * price*(1 - transactioncost))
        position = position - buyqty

        print("SELL: "+str(row[0])+" "+str(int(buyqty))+"@ "+str(price) + " Cash= "+str(cash)+" // Total = {:,}".format(int(position*price+cash)))
    df.loc[df.index == row[0], 'Total'] = cash + (price*position)-(InitialCapital*(1-Margin)/Margin)
    df.loc[df.index == row[0], 'BuyHold'] = price*positionBeginning
    
   
######### Buy/Sell Position plotting over price  ###########


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
'''

############################################################


############ Backtesting Framework Definition  #############

def backtest(df):
    
    cash = InitialCapital/Margin
    position = 0
    total = 0
    
    buyprc = 0     
    winlose = 0
    W= 0
    R= 0
    df['Total'] = InitialCapital
    df['BuyHold'] = InitialCapital
    df['Win/Lose'] = 0
    empty = []
    # To compute the Buy and Hold value, I invest all of my cash in the Close on the first day of the backtest
    positionBeginning = round(InitialCapital/float(df.iloc[0]['Open'])/LotSize)*LotSize
    increment = cash*KellyPosition(empty)
         
    for row in df.iterrows():
        price = float(row[1]['Close'])
        signal = float(row[1]['Signal'])
        increment = round(cash*KellyPosition(df['Win/Lose'].loc[:row[0]])/price/LotSize)*LotSize

        if(signal > 0 and cash - increment * price > 0):
            # Buy
            buyprc = price
            buyqty = increment
            cash = cash - (increment * price*(1 + transactioncost))
            position = position + increment
            
            print("BUY: "+str(row[0])+" "+str(int(position))+"@ "+str(price) + " Cash= "+str(cash)+" // Total = {:,}".format(int(position*price+cash)))
             
        elif(signal < 0  and position != 0):
            # Sell
            df.loc[df.index == row[0], 'Win/Lose'] += buyqty*(price-buyprc)
            cash = cash + (buyqty * price*(1 - transactioncost))
            position = position - buyqty
    
            print("SELL: "+str(row[0])+" "+str(int(buyqty))+"@ "+str(price) + " Cash= "+str(cash)+" // Total = {:,}".format(int(position*price+cash)))
        df.loc[df.index == row[0], 'Total'] = cash + (price*position)-(InitialCapital*(1-Margin)/Margin)
        df.loc[df.index == row[0], 'BuyHold'] = price*positionBeginning
    
    return cash + (price*position)-(InitialCapital*(1-Margin)/Margin)
    '''
    cash = InitialCapital/Margin
    position = 0
    total = 0
     
    data['Total'] = InitialCapital
    data['BuyHold'] = InitialCapital
    data['Win/Lose'] = 0
    # To compute the Buy and Hold value, I invest all of my cash in the Close on the first day of the backtest
    positionBeginning = int(InitialCapital/float(data.iloc[0]['Open']))
    increment = PositionSize
     
    for row in data.iterrows():
        price = float(row[1]['Close'])
        signal = float(row[1]['Signal'])
        increment = round((cash/price)/LotSize)*LotSize
        
        if(position - increment*price >= InitialCapital):
            print "Margin Call! Capital Vanished, Stopping Strategy!!!"
            exit()
            
         
        if(signal > 0 and cash - increment * price > 0):
            # Buy
            cash = cash - increment * price*(1 + transactioncost)
            position = position + increment
            print(str(row[0])+" Position = "+str(position)+" Cash = "+str(cash)+" // Total = {:,}".format(int(position*price+cash)))
             
        elif(signal < 0 and abs(position*price) < cash  and position != 0):
            # Sell

            data.loc[data.index == row[0], 'Win/Lose'] = (increment*price - position)
            cash = cash + increment * price*(1 - transactioncost)
            position = position - increment
            print(str(row[0])+" Position = "+str(position)+" Cash = "+str(cash)+" // Total = {:,}".format(int(position*price+cash)))
             
        data.loc[data.index == row[0], 'Portfolio Value'] = float(position*price+cash - (InitialCapital/Margin)+InitialCapital)
        data.loc[data.index == row[0], 'BuyHold'] = price*positionBeginning
         
    return position*price+cash




'''
############################################################


######### B & H/Performance Calculation & Plotting #########

#Backtest
backtestResult = int(backtest(df))
print(("Backtest => {:,} INR").format(backtestResult))
perf = (float(backtestResult)/InitialCapital-1)*100
daysDiff = (enddate-startdate).days
perf = (perf/(daysDiff))*360
print("Annual return => "+str(perf)+"%")
print " "
# Buy and Hold
perfBuyAndHold = float(df.tail(1)['Close'])/float(df.head(1)['Close'])-1
print(("Buy and Hold => {:,} INR").format(int((1+perfBuyAndHold)*InitialCapital)))
perfBuyAndHold = (perfBuyAndHold/(daysDiff))*360
print("Annual return => "+str(perfBuyAndHold*100)+"%")
print " "
'''

#print df.head(85)


# Compute Sharpe ratio
df["Return"] = df["Total"]/df["Total"].shift(1)-1
volatility = df["Return"].std()*252
sharpe = (perf-riskfreeint)/volatility
print("Volatility => "+str(volatility)+"%")
print("Sharpe => "+str(sharpe))

df['Total'] = df['Total']/10000
df['BuyHold'] = df['BuyHold']/10000


plt.plot(df.index, df['Total'], label='Total', color='g')
plt.plot(df.index, df['BuyHold'], label='BuyHold', color='r')
plt.xlabel('Date')
plt.legend(loc=0)
plt.show()

############################################################


'''






