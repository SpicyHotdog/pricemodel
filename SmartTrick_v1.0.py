# -*- coding: utf-8 -*-
import numpy as np
import akshare as ak
import datetime as dt
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import find_peaks_cwt

''' -------------------------'''
''' Part I: global varialble '''
''' -------------------------'''
data = [[]] #store historical marketing data
historicalDateRange = 252 # historical data range, 252 represent 1 year range
totalAmount = 0
investAmountStep = 250  # % of buying from total amount each time
invDate = dt.date(2000,1,1) #last investment date
enquiryRecord = ''

''' ------------------------------------------'''
''' Part II: retrieve local file configuration'''
''' ------------------------------------------'''
def getDateCursor():
    global enquiryRecord
    #read date cursor record from local file
    with open('/Users/yuki/Desktop/python/database/dateCursor.txt','r') as f:
        content = f.read()
    cursorDate,lastUpdate = content.split(',')
    
    #transfer string to datetime.date
    cursorDate = dt.datetime.strptime(cursorDate,'%Y-%m-%d').date()
    lastUpdate = dt.datetime.strptime(lastUpdate,'%Y-%m-%d').date()
    enquiryRecord += f'获取 cursor date:{cursorDate},上次更新时间：{lastUpdate}\n'
    print(f'获取 cursor date:{cursorDate},上次更新时间：{lastUpdate}')
    
    return cursorDate,lastUpdate

def getTotalAmount():
    content = ''
    with open('/Users/yuki/Desktop/python/database/totalAmount.txt','r') as f:
        content = f.read()
    totalAmount = float(content)
    return totalAmount

def getInvdate():
    with open('/Users/yuki/Desktop/python/database/invdate.txt','r') as f:
        content = f.read()
    invDate = dt.datetime.strptime(content,'%Y-%m-%d').date()
    return invDate

def updateInvDate():
    global invDate
    with open('/Users/yuki/Desktop/python/database/invdate.txt','w') as f:
        f.write(invDate.strftime('%Y-%m-%d'))
        f.close()

def updateTotalAmount():
    global totalAmount
    with open('/Users/yuki/Desktop/python/database/totalAmount.txt','w') as f:
        f.write(str(totalAmount))
        f.close()
def updateCursorDate(cursorDate):
    with open('/Users/yuki/Desktop/python/database/dateCursor.txt','w') as f:
        f.write(cursorDate.strftime('%Y-%m-%d')+','+dt.date.today().strftime('%Y-%m-%d'))
        f.close()

def updateEnquiryRecord():
    global enquiryRecord
    with open('/Users/yuki/Desktop/python/database/EnquiryHistory.txt','a') as f:
        f.write(enquiryRecord)
        f.close()    

''' --------------------------------'''
''' Part III: retrieve marketing data'''
''' --------------------------------'''
#Return target fund code
def getFundCode():
    return '110020'

#Return marketing data
def getData():
    fundCode = getFundCode()
    observeEndDate = dt.date.today() #observation end date is today
    obverveStartDate = observeEndDate - dt.timedelta(days=504)  #observation start date is 2 years in advance to today
    rawData = ak.fund_open_fund_info_em(fund=fundCode, indicator="单位净值走势")
    rawData = rawData.loc[(rawData['净值日期']>=obverveStartDate) & (rawData['净值日期']<=observeEndDate)]
    return rawData

#Return historical data, end by cursor date
def getHistoricalData():
    global data
    global historicalDateRange
    today = dt.date.today()
    historicalData = data.loc[(data['净值日期']<=today) & (data['净值日期']>(today - dt.timedelta(days=historicalDateRange)))]
    return historicalData

#Return historical data including today date, for MA calculation
def getHistoricalDataIncludeToday():
    global data
    global historicalDateRange
    today = dt.date.today()
    historicalData = data.loc[(data['净值日期']<=today) & (data['净值日期']>(today - dt.timedelta(days=historicalDateRange)))]
    return historicalData 

def getCurrentData():
    global data
    today = dt.date.today()
    currentData = data.loc[(data['净值日期']<=today)]
    currentData = currentData.iloc[-1]
    return currentData

#Return nearest transaction date 
def findClosestTxnDate(date):
    global data
    tmp = data.loc[(data['净值日期']>=date)]['净值日期']
    if(len(tmp)>0):
        return tmp.iloc[0]
    
''' ------------------------'''
''' Part IV: decision making'''
''' ------------------------'''
#Buy at valley price decision
def buyAtValley(historicalData,currentData):
    global totalAmount
    global investAmountStep
    global invDate
    global enquiryRecord

    currentDataValue = currentData['单位净值']
    currentDataDate = currentData['净值日期']
    historicalDataValue = historicalData['单位净值']
    
    #Analyze whether it's valley price
    isValley = False
    #find a list of valley value points
    valleyPoint = find_peaks_cwt(-historicalDataValue,widths=np.ones(historicalDataValue.shape)*2)-1
    #find the minimum valley value from the list
    minValley = np.min(historicalDataValue.iloc[valleyPoint])
    enquiryRecord += f'近一年的谷底最低价：{minValley}\n'
    print(f'近一年的谷底最低价：{minValley}')
    if(abs((currentDataValue - minValley)/minValley)<=0.05):
        isValley = True
        enquiryRecord += f'当前价格接近近一年历史价格的谷底区间。最低谷底价格：{minValley}，当前价格：{currentDataValue}\n'
        print(f'当前价格接近近一年历史价格的谷底区间。最低谷底价格：{minValley}，当前价格：{currentDataValue}')
        amountToBuy = investAmountStep * 2
        ''' to continue '''
        if(totalAmount >= amountToBuy):
            if((currentDataDate-invDate).days>10):
                enquiryRecord += f'距离上次买入日期超过10天，建议执行谷底买入操作。买入金额：{amountToBuy}，买入价格为下一个交易日价格，需手动记录。\n'
                print(f'距离上次买入日期超过10天，建议执行谷底买入操作。买入金额：{amountToBuy}，买入价格为下一个交易日价格，需手动记录。')
                invDate = currentDataDate
                totalAmount = totalAmount - amountToBuy
                updateTotalAmount() #update total amount
                updateInvDate()     #update investment date
            else:
                enquiryRecord += '距离上次买入日期未超过10天，请等待。\n'
                print('距离上次买入日期未超过10天，请等待。')    
        else:
            enquiryRecord += '没有足够的资金进行谷底买入操作！\n'
            print('没有足够的资金进行谷底买入操作！')
    else:
        enquiryRecord += '当前没有谷底价格买入的条件\n'
        print('当前没有谷底价格买入的条件')

def buyAtLowPrice(historicalData,currentData):
    global totalAmount
    global invDate
    global investAmountStep
    global enquiryRecord

    currentDataValue = currentData['单位净值']
    currentDataDate = currentData['净值日期']
    #get lower quartile, upper quartile and median value of historical data
    loweQuartile = np.percentile(historicalData['单位净值'],25)
    loweQuartile = round(loweQuartile,2)

    upperQuartile = np.percentile(historicalData['单位净值'],75)
    upperQuartile = round(upperQuartile,2)

    median = np.median(historicalData['单位净值'])
    median = round(median,2)
    enquiryRecord += f'当前日期：{currentDataDate}，下四分位:{loweQuartile}，上四分位:{upperQuartile}，中位数:{median}。| 当前价格：{currentDataValue}\n'
    print(f'当前日期：{currentDataDate}，下四分位:{loweQuartile}，上四分位:{upperQuartile}，中位数:{median}。| 当前价格：{currentDataValue}')

    #check MA20 and MA60 level
    historicalDataIncludeToday = getHistoricalDataIncludeToday()
    MAFlag = False
    df = pd.DataFrame()
    df['M20'] = historicalDataIncludeToday['单位净值'].rolling(window=20).mean()
    df['M60'] = historicalDataIncludeToday['单位净值'].rolling(window=60).mean()    
    enquiryRecord += f'当前MA20:{df["M20"].iloc[-1]}，当前MA60:{df["M60"].iloc[-1]}\n'
    print(f'当前MA20:{df["M20"].iloc[-1]}，当前MA60:{df["M60"].iloc[-1]}')
    div = (df['M20'].iloc[-1]-df['M60'].iloc[-1])/df['M60'].iloc[-1]
    if(df['M20'].iloc[-1] > df['M60'].iloc[-1] and div>0.03):
        MAFlag = True
        enquiryRecord += 'MA20 > MA60，当前为中长期上身趋势\n'
        print('MA20 > MA60，当前为中长期上身趋势')    

    #buy decision
    if(currentDataValue < loweQuartile and (currentDataDate - invDate).days>20):
        amountToBuy = investAmountStep * 2
        if totalAmount >= amountToBuy:
            enquiryRecord += f'下四分位买入指示，买入基本不长的2倍。买入金额：{amountToBuy}\n'
            print(f'下四分位买入指示，买入基本不长的2倍。买入金额：{amountToBuy}')
            invDate = currentDataDate
            totalAmount = totalAmount - amountToBuy
            updateTotalAmount() #update total amount
            updateInvDate()     #update investment date
        else:
            enquiryRecord += '价格低于下四分位，但资金不足，无买入操作\n'
            print('价格低于下四分位，但资金不足，无买入操作')
    elif(currentDataValue > loweQuartile and currentDataValue < median and (currentDataDate - invDate).days>20):
        amountToBuy = investAmountStep * 0.5
        if totalAmount >= amountToBuy:
            enquiryRecord += f'中位数买入指示，买入基本步长的0.5倍。买入金额：{amountToBuy}\n'
            print(f'中位数买入指示，买入基本步长的0.5倍。买入金额：{amountToBuy}')
            invDate = currentDataDate
            totalAmount = totalAmount - amountToBuy
            updateTotalAmount() #update total amount
            updateInvDate()     #update investment date
        else:
            print('资金不足，无买入操作')       
    elif((currentDataDate - invDate).days>20 and MAFlag==True):
        print('当前为上升趋势，无法进行低价买入，改为一次性买入')
        amountToBuy = investAmountStep *3
        if totalAmount >= amountToBuy:
            enquiryRecord += f'上升趋势买入指示，买入基本步长的3倍。建议长期持有。买入金额：{amountToBuy}\n'
            print(f'上升趋势买入指示，买入基本步长的3倍。建议长期持有。买入金额：{amountToBuy}')
            invDate = currentDataDate
            totalAmount = totalAmount - amountToBuy
            updateTotalAmount() #update total amount
            updateInvDate()     #update investment date
    else:
        enquiryRecord += '当前没有低价位买入的条件\n'
        print('当前没有低价位买入的条件')

''' ----------------------------'''
''' Part V: interest calculation'''
''' ----------------------------'''
def interestCalculation():
    
    return ''


if __name__ == '__main__':
    ''' initiate global variables '''
    totalAmount = getTotalAmount()
    invDate = getInvdate()
    enquiryRecord += f'最近一个投资日期（invDate):{invDate}\n'
    data = getData()
    data['净值日期'] = pd.to_datetime(data['净值日期']).dt.date
    cursorDate,lastUpdate = getDateCursor()
    today = dt.date.today()
    historicalData = getHistoricalData()
    currentData = getCurrentData()

    if(today<cursorDate):
        print('未到下一个决策日，请等待。')
    else:
        buyAtLowPrice(historicalData,currentData)
        buyAtValley(historicalData,currentData)
        cursorDate += dt.timedelta(days=7)
        updateCursorDate(cursorDate)
        enquiryRecord +='--------------------------------------\n'
        updateEnquiryRecord()

    #draw box plot
    quartile1, median, quartile3 = np.percentile(historicalData['单位净值'], [25, 50, 75])
    fig, ax = plt.subplots()
    ax.boxplot(historicalData['单位净值'])
    ax.text(1.1, quartile1, f'{quartile1:.3f}', fontsize=12, color='blue')
    ax.text(1.1, median, f'{median:.3f}', fontsize=12, color='red')
    ax.text(1.1, quartile3, f'{quartile3:.3f}', fontsize=12, color='blue')
    point = currentData['单位净值']
  
    ax.axhline(y=point, linestyle='--', color='green', linewidth=2)
    ax.text(1.3, point, f'{point:.3f}', fontsize=12, color='green')
    ax.set_title('Current price value')
    ax.set_ylabel('Value')


    #draw valley poit chart
    valleyPoint = find_peaks_cwt(-historicalData['单位净值'],widths=np.ones(historicalData['单位净值'].shape)*2)-1
    fig2, ax2 = plt.subplots()
    ax2.plot(historicalData['净值日期'],historicalData['单位净值'])
    fig2.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gcf().autofmt_xdate()
    valleyDate = historicalData['净值日期'].iloc[valleyPoint]
    valleyValue = historicalData['单位净值'].iloc[valleyPoint]
    ax2.plot(valleyDate,valleyValue,"x")
    #present current value on the valley point chart
    ax2.plot(currentData['净值日期'],currentData['单位净值'],'o')
    ax2.set_title('Valley point chart (recent 1 year)')
    plt.show()

    #startDate = findClosestTxnDate(cursorDate)


    #cursor,last = getDateCursor()
    #print(type(cursor))
    #print(type(cursor))
    #getData()
    #print(data)

