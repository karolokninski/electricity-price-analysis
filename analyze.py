#!/usr/bin/env python
# coding: utf-8

# In[85]:


pip install pandas seaborn matplotlib plotly


# In[1]:


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from plotly import graph_objects as go


# In[2]:


data_path = './prices.csv'

df = pd.read_csv(data_path, sep=';', parse_dates=['Data'], date_format='%Y%m%d')


# In[3]:


df.head()


# In[4]:


df.RCE = df.RCE.astype('str').str.replace(',', '').astype(float)

df['Time'] = pd.to_numeric(df['Time'], errors='coerce')

df.Time = df.Time.astype(float)

df = df[df['Time'].notna()]


# In[5]:


df.groupby(by='Data').count()


# In[6]:


df.set_index('Data', inplace=True)


# In[7]:


df.index += df.Time.apply(lambda x: pd.Timedelta(f'{x}h'))


# In[8]:


df.resample('1h').max()


# In[9]:


df.resample('1d').count().plot()


# In[10]:


df2 = df.loc['2022-07-01':'2023-07-30']

for year, df_year in df2.resample('1M'):
    plt.figure(figsize=(12,6))
    sns.lineplot(x=df_year.Time, y=df_year.RCE)
    plt.title(year)


# Zalozenia symulacji:
# - w jednej godzinie mozna albo kupic albo sprzedac
# - wyznaczona pojemnosc magazynu
# - okreslona przepustowosc sieci
# - okreslona efektywnosc (straty cieplne)
# 

# In[11]:


def calc_profit(prices, capacity):
    # capacity to chyba liczba godzin 
    n = len(prices)

    sold = [0] * n
    bought = [0] * n
    when_to_buy = []
    when_to_sell = []
    to_buy_i = 0
    to_sell_i = 0

    result = 0

    rest = str(capacity).split('.')[1]
    rest = float(f'0.{rest}')

    capacity = int(capacity)

    for _ in range(n):
        max_profit = 0
        buy = float('inf')

        for i in range(0, n):
            if sold[i] or bought[i]:
                continue

            if buy > prices[i]:
                buy = prices[i]
                to_buy = i
    
            elif prices[i] - buy > max_profit:
                max_profit = prices[i] - buy
                to_buy_i = to_buy
                to_sell_i = i

        if capacity > 0 or sorted(when_to_sell)[0] < to_buy_i or sorted(when_to_buy)[-1] > to_sell_i:
            capacity -= 1

            bought[to_buy_i] = 1
            sold[to_sell_i] = 1

            when_to_buy.append(to_buy_i)
            when_to_sell.append(to_sell_i)

            result += max_profit

        elif rest:
            rest = 0

            bought[to_buy_i] = 1
            sold[to_sell_i] = 1

            when_to_buy.append(to_buy_i)
            when_to_sell.append(to_sell_i)

            result += max_profit * rest

        else:
            break

    return result, when_to_buy, when_to_sell


# In[12]:


capacity = 0.02 # in MWh
bandwidth = 0.01 # in MW
efficiency = 80 # in %

profit = []

for time, df_time in df['2023-01-01':].resample('1D'):
    mean_prices = []
#     for i in range(1, 25):
#         mean_prices.append(df_time[df_time.Time == i].RCE.mean()) # do wywalenia bo nic nie robi tak naprawdę
    prices = df_time.RCE.tolist()
    result = calc_profit(mean_prices, capacity/min(capacity, bandwidth)) # czym jest min(capacity, bandwidth) i po co

    profit.append(result[0] * min(capacity, bandwidth) * efficiency/100)

df_profit = pd.DataFrame(profit)
df_profit.describe()


# In[100]:


class EnergyStorage:
    def __init__(self, capacity, bandwidth):
        '''Params:
            - bandwidth - MW per h
            - capacity - MWh
        '''
        self.capacity = capacity
        self.bandwidth = bandwidth
        self.load = 0
        self.cost = 0
        self.income = 0
        
    def __repr__(self):
        return f'''EnergyStorage(
    capacity = {self.capacity},
    bandwidth = {self.bandwidth},
    load = {self.load},
    cost = {self.cost},
    income = {self.income},
    profit = {self.profit},
    profit_net = {self.profit_net}
)
'''
        
    def buy(self, price):
        """Buys one hour of energy with given price"""
        # add option to buy partially not full bandwidth in one hour
        
        if self.capacity >= self.load + self.bandwidth:
            self.cost += price * self.bandwidth
            self.load += self.bandwidth
        else:
            raise ValueError('Can\'t buy, max capacity')
        return self
            
    def sell(self, price):
        """Sels one hour of energy with given price"""
        if self.load - self.bandwidth >= 0:
            self.income += price * self.bandwidth
            self.load -= self.bandwidth
        else:
            raise ValueError('Can\'t sell, fully discharged')
        return self
    
    @property
    def is_full(self):
        return self.load + self.bandwidth > self.capacity # adding bandwidth to limit cases when can't add more
    
    @property
    def is_discharged(self):
         return self.load - self.bandwidth < 0
        
    @property
    def profit(self):
        return self.income - self.cost
    
    @property
    def profit_net(self):
        return self.profit * 0.9 * 0.81


# In[85]:


es = EnergyStorage(80, 30)
es


# In[86]:


for _ in range(0, 2):
    es.buy(100)
es.is_full


# In[87]:


es.sell(200)


# In[88]:


df = df.sort_index()


# In[89]:


df['rolling_1d_price'] = df.RCE.rolling('1d').mean()
df['low_boundry_1d_price'] = df.RCE.rolling('1d').quantile(0.4)
df['high_boundry_1d_price'] = df.RCE.rolling('1d').quantile(0.6)
df['should_buy'] = df.RCE < df['low_boundry_1d_price']
df['should_sell'] = df.RCE > df['high_boundry_1d_price']


# In[90]:


df.should_sell


# In[91]:


fig = go.Figure(
    layout=dict(
        title='Rynkowa cena energii elektrycznej'
    )
)
fig.add_trace(go.Scatter(
    x=df.index,
    y=df.RCE,
    name='price'

))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df.low_boundry_1d_price,
    name='buy boundry'
))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df.high_boundry_1d_price,
    name='sell boundry'
))


# In[76]:


fig = go.Figure(
    layout=dict(
        title='Rynkowa cena energii elektrycznej'
    )
)
fig.add_trace(go.Scatter(
    x=df.index,
    y=df.RCE,
    name='price'

))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df.should_buy,
    name='should_buy'
))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df.should_sell,
    name='should_sell'
))


# In[114]:


es = EnergyStorage(0.1, 0.01)

for idx, sdf in df.loc[:'2023-04-01'].iterrows():
    price = sdf.RCE
    if not es.is_full and sdf.should_buy:
        es.buy(price)
    elif not es.is_discharged and sdf.should_sell:
        es.sell(price)
    df.loc[idx, 'load'] = es.load
    df.loc[idx, 'cost'] = es.cost
    df.loc[idx, 'income'] = es.income
    df.loc[idx, 'profit'] = es.profit
#     print(idx, f'price={sdf.RCE}', f'buy={sdf.should_buy}', f'sell={sdf.should_sell}', )
es


# In[115]:


from plotly.subplots import make_subplots


# In[ ]:





# In[124]:


fig = make_subplots(rows=3, cols=1, shared_xaxes=True)
fig.add_trace(go.Scatter(
    x=df.index,
    y=df.RCE,
    name='price [PLN]'

))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df.low_boundry_1d_price,
    name='buy_boundry'

))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df.high_boundry_1d_price,
    name='sell_boundry'

))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df.load,
    name='load[MW]'
),row=2, col=1)

fig.add_trace(go.Scatter(
    x=df.index,
    y=df.profit,
    name='profit[PLN]'
),row=3, col=1)


# In[125]:


import plotly 


# In[126]:


plotly.offline.plot(fig, filename='energy_storage_simulation.html')


# In[120]:


fig.to_html()

