# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 20:34:42 2023

@author: Ray
更改记录：
 - 优化代码
"""

import numpy as np
import akshare as ak
import datetime as dt
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import find_peaks_cwt

data = [[]] #初始化数据集合
cursorDate = dt.date(2022,1,1) #初始化交易开始日期，后续按投资频率步长增加
firstTxnDateOfYear = dt.date(2022,1,1) #定义交易开始日期，用于获取年度第一个交易日的净值
txnEndDate = dt.date(2022,12,31) #定义交易结束日期
historicalDateRange = 252 #定义历史数据的长度，252为A股市场一年交易日的天数

totalAmount = 10000 #初始化总投入成本
totalAmountFixed = 10000 #定义总成本，该值固定不变，用于计算最终投入金额
avgCostHolding = 0

buystep = 5 #定义每次买入所占总金额的百分比,5代表5%
investAmount = totalAmount * buystep/100 #定义每次买入的实际金额
investDate = dt.date(2000,1,1) #初始化投资日期，每次买入/卖出都进行日期记录
holdings = [] #初始化持有资产的集合
sellStep_10 = 10
sellStep_20 = 20
sellStep_50 = 50
sellStep_80 = 80

observeDataStartDate = dt.date(2021,1,1) #定义观测数据起始时间
observeDataEndDate = dt.date(2022,12,31) #定义观测数据结束时间

def featureFlag():
    buyAtLowPrice = True
    sellWithGrossRate = True
    buyAtVallyPrice = True
    flags = {
        'buyAtLowPrice':buyAtLowPrice,
        'sellWithGrossRate':sellWithGrossRate,
        'buyAtVallyPrice':buyAtVallyPrice
    }
    return flags

def getFundCode():
    return '110020'

""" 获取源数据  """
def getData():
    global data
    global observeDataStartDate
    global observeDataEndDate
    fundCode = getFundCode()
    data = ak.fund_open_fund_info_em(fund=fundCode, indicator="单位净值走势")
    #按照观测数据的起始、结束时间截取源数据
    data = data.loc[(data['净值日期']>=observeDataStartDate) & (data['净值日期']<=observeDataEndDate)]
    
    #获取观测数据的净值和日期
    data = data[['净值日期','单位净值']]
    return data

""" 获取最近的交易日期 """
def findCloestTxnDate(date):
    global data
    tmp = data.loc[(data['净值日期']>=date)]['净值日期']
    if(len(tmp)>0):
        return tmp.iloc[0]

""" 从观测数据中，获取由前交易日开始的、1年之前的所有交易日数据进行分析  """
def getHistoricalData():
    global data
    global cursorDate
    global historicalDateRange
    #从data中截取由当前交易日开始的，过去一年的数据
    historicalData = data.loc[(data['净值日期']<cursorDate) & (data['净值日期']>(cursorDate - dt.timedelta(days=historicalDateRange)))]
    return historicalData

def getHistoricalDataByDate(date):
    global data
    global historicalDateRange
    historicalData = data.loc[(data['净值日期']<date) & (data['净值日期']>(date - dt.timedelta(days=historicalDateRange)))]
    return historicalData

""" 获取当前以及下一个交易日的数据 """
def getCurrentAndNextData():
    global data
    global cursorDate
    #在下午3点之后购买场外基金时，成交价格应该是当前交易日下一个交易日的价格。因此向后推算一个交易日
    currentDate = findCloestTxnDate(cursorDate)
    nextDate = findCloestTxnDate(currentDate + dt.timedelta(days=1))    #下一个交易日为当前交易日加1后寻找到的最近一个交易日
    #获取数据
    currentData = data.loc[(data['净值日期']==currentDate)]
    nextData = data.loc[(data['净值日期']==nextDate)]
    return currentData,nextData

def getCurrentAndNextDataByDate(date):
    global data    
    currentDate = findCloestTxnDate(date)
    nextDate = findCloestTxnDate(currentDate + dt.timedelta(days=1))    #下一个交易日为当前交易日加1后寻找到的最近一个交易日
    #获取数据
    currentData = data.loc[(data['净值日期']==currentDate)]
    nextData = data.loc[(data['净值日期']==nextDate)]
    return currentData,nextData    

""" 谷底价格买入决策 """
def buyAtValley(historicalData,currentData,nextData):
    currentDataValue = currentData['单位净值'].iloc[0]
    currentDataDate = currentData['净值日期'].iloc[0]
    nextDataValue = nextData['单位净值'].iloc[0]
    
    isAroundValley,minValley = valleyPointAnalysis(historicalData,currentData)
    #价格处于谷底，购买额外多的份额。优先执行
    amountToBuy = investAmount*2
    if(isAroundValley and (currentDataDate - investDate).days>10):
        if(totalAmount >= amountToBuy):
            quantity = round((amountToBuy/nextDataValue),2)
            doBuy(amountToBuy,nextDataValue,quantity,currentDataDate,3,currentDataValue)
        else:
            print('谷底价格，但资金不足，无法买入')

def valleyPointAnalysis(historicalData,currentData):
    isValley = False
    value = historicalData['单位净值']
    date = historicalData['净值日期']
    valleyPoint = find_peaks_cwt(-value,widths=np.ones(value.shape)*2) -1
    minValley = np.min(value.iloc[valleyPoint])
    currentValue = currentData['单位净值'].iloc[0]
    if(abs((currentValue - minValley)/minValley)<=0.05):
        print(f'谷底最低價：{minValley}，當前價格:{currentValue}')
        isValley = True

    #drawVallyPoint(date,value,date.iloc[valleyPoint],value.iloc[valleyPoint]) 
    return isValley,minValley

def drawVallyPoint(date,value,valleyDate,valleyValue):
    plt.plot(date,value)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gcf().autofmt_xdate()
    plt.plot(valleyDate,valleyValue,"x")

    plt.show() 

""" 低价买入决策 """
def buyAtLowPrice(historicalData,currentData,nextData):
    global totalAmount
    global buystep
    global investDate
    global holdings
    global investAmount
    q1 = np.percentile(historicalData['单位净值'], 25)  #下四分位值
    q1 = round(q1,2)
    q3 = np.percentile(historicalData['单位净值'], 75)  #上四分位值
    q3 = round(q3,2)
    median = np.median(historicalData['单位净值'])
    median = round(median,2)
    currentDataValue = currentData['单位净值'].iloc[0]
    currentDataDate = currentData['净值日期'].iloc[0]
    nextDataValue = nextData['单位净值'].iloc[0]

    print(f'当前日期：{currentDataDate}，下四分位:{q1}，上四分位:{q3}，中位数:{median}。|当前价格：{currentDataValue}')

    if(currentDataValue < q1 and (currentDataDate - investDate).days>30):
        amountToBuy = investAmount * 2
        if totalAmount >= amountToBuy:
            quantity = round((amountToBuy/nextDataValue),2)
            #下单日期为当前交易日3点之后，成交价格为下一个交易日的价格
            doBuy(amountToBuy,nextDataValue,quantity,currentDataDate,1,currentDataValue)
        else:
            pass
            print('资金不足，无买入操作')
    
    elif(currentDataValue > q1 and currentDataValue < median and (currentDataDate - investDate).days>30):
        amountToBuy = investAmount * 0.5
        if totalAmount > investAmount:
            quantity = round((amountToBuy/nextDataValue),2)
            doBuy(amountToBuy,nextDataValue,quantity,currentDataDate,2,currentDataValue)
        else:
            print('资金不足，无买入操作')

def doBuy(amount,price,quantity,txnDate,type,currPrice):
    global totalAmount
    global buystep
    global investDate
    global holdings
    global investAmount
    global avgCostHolding
    totalshare_before = calculateTotalShares()
    
    performBuy = {
            'amount': amount,
            'price': price,
            'quantity': quantity,
            'txnDate': txnDate
    }
    holdings.append(performBuy)
    totalAmount = totalAmount - amount
    investDate = txnDate

    totalshare_after = calculateTotalShares()
    
    ''' 计算持仓成本'''
    print(f'totalshare after:{totalshare_after}')
    if(totalshare_after > 0):
        avgCostHolding = (totalshare_before * avgCostHolding + amount)/totalshare_after
    else:
        avgCostHolding = 0
    
    if(type == 1):
        print(f'下四分位区间买入操作，金额：{amount}, 价格:{price},数量：{quantity}')
    elif(type == 2):
        print(f'中位区间买入操作，金额：{amount}, 价格:{price},数量：{quantity}')
    elif(type == 3):
        print(f'谷底价格买入操作，金额：{amount}, 价格:{price},数量：{quantity}')


""" 卖出决策 """
def sellAtRate(historicalData,currentData,nextData):
    global totalAmount
    global holdings
    global investDate
    global sellStep_10
    global sellStep_20
    global sellStep_50
    global sellStep_80
    global avgCostHolding
    

    #获取持有总份额
    totalShare = calculateTotalShares()
    
    #获取当前价格
    currentPrice = currentData['单位净值'].iloc[0]
    currentDate = currentData['净值日期'].iloc[0]
    nextPrice = nextData['单位净值'].iloc[0]

    holdingAmount = totalShare * currentPrice
    totalAsset = totalAmount + holdingAmount
    print(f'总资产:{totalAsset},投入中资产:{holdingAmount}，现金：{totalAmount}')
    print(f'持仓成本:{avgCostHolding}')
    
    if (totalShare >= 5):    #持有金额多余10元时才可卖出
        gross = (currentPrice - avgCostHolding)/avgCostHolding
        print(f'賣出決策中|当前日期:{currentDate},当前价格：{currentPrice},总持有份额：{totalShare},持有平均价格:{avgCostHolding}，收益率：{gross}')

        if(gross > 0.01 and gross < 0.03):
            print('卖出总份额的20%')
            sellQuantity = totalShare * sellStep_20/100
            sellAmount = sellQuantity * nextPrice
            doSell(sellAmount,nextPrice,sellQuantity,currentDate,currentPrice)
   
        elif(gross >0.03 and gross < 0.05):
            print('卖出总份额的80%')
            sellQuantity = totalShare * sellStep_80/100
            sellAmount = sellQuantity * nextPrice
            doSell(sellAmount,nextPrice,sellQuantity,currentDate,currentPrice)            

        elif(gross>0.05):
            print('卖出总份额的100%')
            sellQuantity = totalShare
            sellAmount = sellQuantity * nextPrice
            doSell(sellAmount,nextPrice,sellQuantity,currentDate,currentPrice)            
 
    else:
        print('当前份额为0，不可卖出')

def calculateTotalShares():
    global holdings
    totalShare = 0
    for i in holdings:
        totalShare += i['quantity']
    return totalShare

def doSell(amount,price,quantity,txnDate,currPrice):
    global totalAmount
    global buystep
    global investDate
    global holdings
    global investAmount
    global avgCostHolding
    totalshare_before = calculateTotalShares()
    
    performSell = {
            'amount': amount,
            'price': price,
            'quantity': 0-quantity,
            'txnDate': txnDate
    }
    holdings.append(performSell)
    totalAmount = totalAmount + amount
    
    totalshare_after = calculateTotalShares()

    ''' 计算持仓成本 '''
    if(totalshare_after > 0):
        avgCostHolding = (totalshare_before * avgCostHolding - amount)/totalshare_after
    else:
        avgCostHolding = 0
    investDate = txnDate

""" 获取年终产品的净值 """
def getLastTxnDateValue():
    global txnEndDate
    global data
    lastRecordofYear = data.loc[(data['净值日期']<=txnEndDate)].tail(1)
    return lastRecordofYear['单位净值'].iloc[0],lastRecordofYear['净值日期'].iloc[0]

""" 获取年初产品的净值 """
def getFirstTxnDateValue():
    global firstTxnDateOfYear
    global data
    firstRecordofYear = data.loc[(data['净值日期']>=firstTxnDateOfYear)]
    return firstRecordofYear['单位净值'].iloc[0],firstRecordofYear['净值日期'].iloc[0] 

""" 计算收益率 """
def calculateGrossRate(holdings):
    totalShare = calculateTotalShares()
    lastValue,lastDate = getLastTxnDateValue()
    totalAmountHolding = totalAmount + lastValue * totalShare
    gross = (totalAmountHolding - totalAmountFixed)/totalAmountFixed
    print(f'资产总额:{totalAmountHolding}，包括：1)持有中金额:{lastValue * totalShare};2)总现金:{totalAmount}')
    print(f'模型总收益:{gross}')
    
    firstValue,firstDate = getFirstTxnDateValue()
    yearMarketNetRate = (lastValue - firstValue)/firstValue
    print(f'市场年初净值:{firstValue}')
    print(f'市场年末净值:{lastValue}')
    print(f'市场全年总收益:{yearMarketNetRate}')
    

def transactionHistory():
    global holdings
    cal = 0
    for i in holdings:
        cal += i['price'] * i['quantity']
        print(f'下單日期:{i["txnDate"]},金額:{i["amount"]},價格:{i["price"]},份額:{i["quantity"]}')
    print(f'cal:{cal}')

def drawTransactionChart():
    global data
    global observeDataEndDate
    data = data.loc[(data['净值日期']>=firstTxnDateOfYear) & (data['净值日期']<=observeDataEndDate)]
    date = data['净值日期']
    value = data['单位净值']
    plt.plot(date,value)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gcf().autofmt_xdate()

    txnRecordDate = []
    txnRecordPrice = []
    for i in holdings:
        txndate = i['txnDate'] + dt.timedelta(days=1)
        record = data[data['净值日期']==txndate]
        if(i['quantity']>0):
            plt.plot(record['净值日期'],record['单位净值'],'ro')
        elif(i['quantity']<0):
            plt.plot(record['净值日期'],record['单位净值'],'bo')
        
        
    plt.show()

if __name__ == '__main__':
    data = pd.read_excel("~/Desktop/python/沪深300.xlsx")
    data['净值日期'] = pd.to_datetime(data['净值日期']).dt.date

    startDate = findCloestTxnDate(cursorDate)
    yearFirstValue,yearFirstDate = getFirstTxnDateValue()
    lastValue,lastDate = getLastTxnDateValue()
    count = 0
    #从起始交易日开始执行买入操作
    flags = featureFlag()
    flag_1 = flags['buyAtLowPrice']
    flag_2 = flags['sellWithGrossRate']
    flag_3 = flags['buyAtVallyPrice']

    while(totalAmount > 0 and cursorDate<txnEndDate):
        count += 1
        historicalData = getHistoricalData()
        currentData,nextData = getCurrentAndNextData()   
        if(flag_1):
            buyAtLowPrice(historicalData,currentData,nextData)
        if(currentData['净值日期'].iloc[0] != yearFirstDate and currentData['净值日期'].iloc[0] != lastDate and len(holdings)!=0):
            if(flag_2):
                sellAtRate(historicalData,currentData,nextData)
        if(flag_3):
                buyAtValley(historicalData,currentData,nextData)
        print('-------------------------------')
        cursorDate = currentData['净值日期'].iloc[0] + dt.timedelta(days=7)

    
    print(f'總共輪詢次數:{count}')
    calculateGrossRate(holdings)
    print('交易紀錄:')
    transactionHistory()
    drawTransactionChart()
