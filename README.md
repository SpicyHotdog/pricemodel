# Optimal pricing using Python data analytic
## Model introduction
* **1. Problem statement**: 
  * China "Shenzhen Component Index" is currently belong to the undervalued period for the entire year, and show a trend fluctuations based on the undervalued range in the short term. This study focuses on "Shenzhen Component Index". It aims to issue buy recommendations towards related index fund when the price reaches bottom or low range, based on the analysis of price data over the past year. Additionally, this study aims to earn profits from short-term fluctuations.
  * Product used for this study: Shenzhen Component Index 50 ETF LOF fund - (code: 160424). 
  * Why LOF(listed open-ended fund)? - Lower volatility and non-real-time trading avoids frequent trading actions, ideal for new investors learning the market.
* **2. Modelling**：
  * Step 1: Data acquisition 
    * Use open sourced Python finance data library - Akshare, and retrieve historical price value of the product over entire year of trading days. Akshare: （https://akshare.xyz/data/fund/fund_public.html）
    * Data cleaning, remove missing values, empty values and filter out non-trading days' values if any.
  * Step 2: Analyzing 
    * Based on historical data from the past year, obtain a list of the bottom price throughout the past year by using the least squares method. Find out the minimum 
    * Based on historical data from the past year, obtain the lower quartile, median, and upper quartile prices.
    * Compare current price with the two datasets mentioned above.
  * Step 3: Define strategy:
    * 3.1) - buy at bottom-valued range
      * **Given** there is enough captial to buy _and_ currenct time is more than 20 days since last operation
    <br/> **When** the price absolute value of the difference between the current price and the minimum price of the bottom range is greater than 5% (configurable)
    <br/> **Then** determin the price is at lowest point since last year and purchase a quantity equal to 20% (configurable) of total inventory<br/>
    * 3.2) - buy at undervalued range
      * **Given** there is enough captial to buy _and_ currenct time is more than 20 days since last operation
    <br/> **When** current price is between the lower quartile and median of the past entire year
    <br/> **Then** determin current price is within the undervalued range and purchase a quantity equal to 10% (configurable) of total inventory<br/>
    * 3.2) - sell: absolute value profit taking method
      * **Given** all the buying actions have been recorded with price and quantity
    <br/> **When** the profit of any individual record exceeds 5%(configurable)
    <br/> **Then** sell the share quantity of that individual record
    <br/> Alternatively, sell strategy can be further divided like when profits between (1% ~3%):sell 20% share quantity, (3% ~ 5%): sell 50%, (over 5%): sell-off.

* **3. Key Implementation Details**：
``` python
# ---- Part I: import required libs ----
import numpy as np
import akshare as ak
import datetime as dt
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import find_peaks_cwt

# ---- Part II: Data acquition ----
def getFundCode():
    return '160424'

#Retrieve historical data of the year
def getHistoricalData():
    global data
    fundCode = getFundCode()
    data = ak.fund_open_fund_info_em(fund=fundCode, indicator="单位净值走势")  #Use Akshare to retrieve fund price data
    global historicalDateRange
    today = dt.date.today()
    historicalData = data.loc[(data['净值日期']<=today) & (data['净值日期']>(today - dt.timedelta(days=historicalDateRange)))] #historical date range is configurable and it
    return historicalData

# ---- Part III: Analyzing ----
#Buy at valley price decision
def buyAtValleyPrice(historicalData,currentData):
    #... Omit ...
   
    isValley = False
    valleyPoint = find_peaks_cwt(-historicalDataValue,widths=np.ones(historicalDataValue.shape)*2)-1 #find a list of valley value point
    minValley = np.min(historicalDataValue.iloc[valleyPoint])  #find the minimum valley value from the list
    if(abs((currentDataValue - minValley)/minValley)<=0.05): #Analyze whether it's at valley price range
        isValley = True
        enquiryRecord += f'Current price is within valley price range。Bottom value of the past year：{minValley}，Current price：{currentDataValue}\n'
        print(enquiryRecord)
        amountToBuy = investAmountStep * 2 #to buy 20% of total amount
        if(totalAmount >= amountToBuy):
            if((currentDataDate-invDate).days>20): #buy action must be 20 trading later since last buy action
                # implement buy and update buy records
                # ...Omit...
                invDate = currentDataDate
                totalAmount = totalAmount - amountToBuy
                updateTotalAmount() #update total amount
                updateInvDate()     #update investment date
            else:
                enquiryRecord += 'Less than 20 days since last buy action, wait and avoid frequent buying actions\n'
                print(enquiryRecord)    
        else:
            enquiryRecord += 'Insufficient fund for the buy action！\n'
            print(enquiryRecord)
    else:
        enquiryRecord += 'Not reaching valley price range, please inquiry again later.\n'
        print(enquiryRecord)

def buyAtLowPrice(historicalData,currentData):
    #... Omit ...
    #get lower quartile, upper quartile and median value of historical data
    loweQuartile = np.percentile(historicalData['单位净值'],25)
    loweQuartile = round(loweQuartile,2)
    upperQuartile = np.percentile(historicalData['单位净值'],75)
    upperQuartile = round(upperQuartile,2)
    median = np.median(historicalData['单位净值'])
    median = round(median,2)
    #... Omit ...
    #buy decision
    if(currentDataValue < loweQuartile and (currentDataDate - invDate).days>20):
        amountToBuy = investAmountStep * 2
        if totalAmount >= amountToBuy:
            # price lower than low quartile, buy 20% of total amount
            
    elif(currentDataValue > loweQuartile and currentDataValue < median and (currentDataDate - invDate).days>20):
        amountToBuy = investAmountStep * 0.5
        if totalAmount >= amountToBuy:
            # price between median and low quartile, buy 5% of total amount        
```
Each time of running the program, charts will be drawn to indicate analytic results as below to help decision making:
<img src='https://github.com/SpicyHotdog/pricemodel/blob/main/analytic%20result.png'/><br/><br/>


* **4. Regression testing**: 
  * In order to ensure the fairness and usability of the model， use another similar product to test the total profit using the model with the market data during year 2021 ~ 2022.
  <br/> Reveal result: 
  <br/> Total times of analytic: 50. Annual Profile of using the model: **5.12%** compared to market profit of that year: -18.6%, beating the market by 23.6%.   
  <br/> Implementation details from the model:
Order date: 2022-01-04, amount: 250.0, price: 1.7775, buy share: 140.65<br/>
Order date: 2022-01-18, amount: 1000.0, price: 1.7472, buy share: 572.34<br/>
Order date: 2022-02-07, amount: 1000.0, price: 1.6884, buy share: 592.28<br/>
Order date: 2022-02-21, amount: 1000.0, price: 1.6767, buy share: 596.41<br/>
Order date: 2022-03-28, amount: 1000.0, price: 1.5234, buy share: 656.43<br/>
Order date: 2022-04-13, amount: 1000.0, price: 1.5433, buy share: 647.96<br/>
Order date: 2022-04-27, amount: 1000.0, price: 1.4455, buy share: 691.8<br/>
Order date: 2022-05-12, amount: 1000.0, price: 1.471, buy share: 679.81<br/>
Order date: 2022-05-26, amount: 1000.0, price: 1.4773, buy share: 676.91<br/>
Order date: 2022-06-23, amount: 1705.639914, price: 1.623, sell share: 1050.9180000000001<br/>
Order date: 2022-06-30, amount: 6942.7846752000005, price: 1.6516, sell share: 4203.6720000000005<br/>
Order date: 2022-08-04, amount: 1000.0, price: 1.5549, buy share: 643.13<br/>
Order date: 2022-09-08, amount: 1000.0, price: 1.5354, buy share: 651.3<br/>
Order date: 2022-09-22, amount: 1000.0, price: 1.4513, buy share: 689.04<br/>
Order date: 2022-10-10, amount: 1000.0, price: 1.4058, buy share: 711.34<br/>
Order date: 2022-10-24, amount: 1000.0, price: 1.3716, buy share: 729.08<br/>
Order date: 2022-11-07, amount: 1000.0, price: 1.4156, buy share: 706.41<br/>
Order date: 2022-12-05, amount: 1233.7206099999999, price: 1.4935, sell share: 826.06<br/>
Order date: 2022-12-12, amount: 3925.7014592000005, price: 1.4851, sell share: 2643.3920000000003<br/>
Order date: 2022-12-19, amount: 954.5288511999998, price: 1.4444, sell share: 660.848<br/>
