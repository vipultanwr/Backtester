import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from StdSuites.Table_Suite import row
from pandas.io.data import _adjust_prices
from matplotlib.pyplot import draw


############    Data reading and formatting   #############

df = pd.read_csv("btc_raw.csv")

#conveting string values to numeric

df['Open'] = pd.to_numeric(df['Open'],errors='coerce')
df['High'] = pd.to_numeric(df['High'],errors='coerce')
df['Low'] = pd.to_numeric(df['Low'],errors='coerce')
df['Close'] = pd.to_numeric(df['Close'],errors='coerce')

cols = ['Open', 'High','Low','Close']  
df[cols] = df[cols].ffill()         #Forward filling the empty rows

############################################################


############    Input Parameters & Assumptions   #############

transactioncost = 0.0002            #Transaction in actual fraction(not bps)
InitialCapital = 10000000           #Initial Portfolio Capital  
Margin = 0.1                        #Margin Provided
LotSize = 75
InterestRate = 0.0685               #Risk free interest rate
ShortInterval = 15                  #Days to be considered in faster moving average's
LongInterval = 20                   #Days to be considered in slower moving average's
triggerfactor = 0.001               #Band of bps to assume proximity to signal
MaxVaR = 0.5                        #Maximum value that can be put to risk
MinVaR = 0.01                       #Minimum value to add in case of a drawdown even if KellyPosition returns zero or negative
DefaultRatio  = 0.6                 #Default payoff value assumption for taking the very first position
MarginCallPercentage = 0.25         #When the portfolio value reaches this fraction of Init capital, strategy stops

############################################################


########## Strategy definition and application  ############

def KellyPosition(data):
    '''
    We start position taking with some seed value,
    after that the model looks at past performance 
    and computes the position size according to the Kelly criterion
    (Calculates W and R defined below)
    '''
    
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
    
    

def PullBack(self):
    '''
    
    Strategy logic where we create a column "Signal"
    in the dataframe and fill t with 1 and -1 for buy and sell respectively
    in the loop at the end of the function we make sure that 
    one buy signal is followed by one sell signal only for simplicity
    
    '''
    df['Signal'] = 0
    df['SMA'] = df['Close'].rolling(LongInterval).mean()
    df['EMA']=  df['Close'].ewm(span=ShortInterval, adjust=False).mean()

    
    df.loc[(df['SMA'].shift(-6) < df['EMA'].shift(-6)) & (((df['SMA'] - df['EMA'])/df['SMA']) > triggerfactor),'Signal'] = 1
    df.loc[((df['EMA'] - df['SMA'])/df['SMA']) > 0,'Signal'] = -1
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
    
    
PullBack(df) #Applying strategy to the entire OHLC dataframe

############################################################

   
   
######### Buy/Sell Position plotting over price  ###########
''' 
    Showing the buy and sell spots 
    on price chart with green and red color
'''

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


############################################################


############ Backtesting Framework Definition  #############

def backtest(df):
    '''
    This function takes care of book keeping.
    Maitains a P&L for the strategy as well as 
    benchmark buy and hold strategy. 
    It also maitains the values of W and R for 
    KellyPosition function to calculate next position size
    '''
    cash = InitialCapital/Margin
    position = 0
    
    buyprc = 0     
    df['Total'] = InitialCapital
    df['BuyHold'] = InitialCapital
    df['Win/Lose'] = 0
    empty = []
    # To compute the Buy and Hold value, I invest all of my cash in the Close on the first day of the backtest
    positionBeginning = int(InitialCapital/Margin/float(df.iloc[0]['Open'])/LotSize)*LotSize
    increment = cash*KellyPosition(empty)
         
    for row in df.iterrows():
        price = float(row[1]['Close'])
        signal = float(row[1]['Signal'])
        increment = round(cash*KellyPosition(df['Win/Lose'].loc[:row[0]])/price/LotSize)*LotSize
        
        if(row[1]['Total'] < 0):
            print "Margin Call! Stopping strategy..."
            exit()
        
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
        df.loc[df.index == row[0], 'BuyHold'] = price*positionBeginning - (InitialCapital*(1-Margin)/Margin) - ((InterestRate/360)*(1-Margin)*InitialCapital)
    
    return cash + (price*position)-(InitialCapital*(1-Margin)/Margin)

    
############################################################


######### B & H/Performance Calculation & Plotting #########



startdate = datetime.datetime.strptime(df['Date'].iloc[0], "%m/%d/%Y").date()
enddate = datetime.datetime.strptime(df['Date'].iloc[-1], "%m/%d/%Y").date()

#Backtest
backtestResult = int(backtest(df))
print " "
print(("Active Portfolio Value => {:,} INR").format(backtestResult))
perf = (float(backtestResult)/InitialCapital-1)*100
daysDiff = (enddate-startdate).days
perf = (perf/(daysDiff))*360

perf = (((float(backtestResult)/InitialCapital)**(0.125)) -1 )

print("Strategy CAGR => "+str(perf*100)+"%")
print " "

# Buy and Hold
perfBuyAndHold = float(df.tail(1)['BuyHold'])
print(("Buy&Hold Portfolio Value => {:,} INR").format(perfBuyAndHold))
perfBuyAndHold = (perfBuyAndHold - InitialCapital)/InitialCapital
perfBuyAndHold = (perfBuyAndHold/(daysDiff))*360

perfBuyAndHold = (((float(df.tail(1)['BuyHold'])/InitialCapital)**(0.125)) -1 )
print("Buy&Hold CAGR => "+str(perfBuyAndHold*100)+"%")
print " "
df.to_csv('out.csv')

# Various Performance Metrics

df['Returns'] = df['Total'].pct_change()
sharpereturns = df['Returns'] - 0.0685/252
Inforeturns = df['Total'].pct_change() - df['BuyHold'].pct_change()

print " "
sharpe =  np.sqrt(252) * sharpereturns.mean() / sharpereturns.std()
volatility =  np.sqrt(252) * df['Returns'].std()
IR =  np.sqrt(252) * Inforeturns.mean()/Inforeturns.std()


print("Volatility => "+str(volatility*100)+"%")
print("Sharpe Ratio => "+str(sharpe))
print("Information Ratio => "+str(IR))


# Showing P&L chart with respect to benchmark B&H strategy
plt.plot(df.index, df['Total'], label='Total', color='g')
plt.plot(df.index, df['BuyHold'], label='BuyHold', color='r')
plt.xlabel('Date')
plt.legend(loc=0)
plt.show()

###########################################################








