import os 
import pandas as pd 
from posix import listdir 
import plotly.graph_objects as go 
import streamlit as st 
import yfinance as yf 
import datetime 
from datetime import datetime as dt
import time 
import pandas_ta as ta 


st.title("Crypto's Top 25 Squeeze Scanner App - J.Curry ")

# st.subheader("By Javonnii Curry")
# make the time interval variable a input variable for the app.
# """
# I have to keep the chart time w/i range of no more than 1D b/c of the limit of yf.download
# """

chart_time = ["5m", "15m", "30m", "60m", "90m", "1h", "1d"]

time_interval = st.sidebar.select_slider("Time Interval", options=chart_time)

LABEL = 'sma'

SYMBOLS = [] 

IN_SQZ = []
OUT_SQZ = []
COM_OUT = []


# make a datetime slider that goes back only 60 days due to yfinance limit 

start_date = datetime.datetime.now() - datetime.timedelta(60)
end_date = datetime.datetime.now() # not sure I need this yet


# st.markdown(f"{type(time_interval)}")
# get a snapshot of the data from yfinance and store in datasets directories

# start=start_date.strftime('%Y-%m-%d')

with open('symbols.csv') as f:
    lines = f.read().splitlines()
    
    try: #doing this try and except to bypass valueerror!
        for symbol in lines:
            data = yf.download(symbol, period="1mo", interval=time_interval)
            data.to_csv("datasets/{}.csv".format(symbol))
            SYMBOLS.append(symbol)
    except ValueError:
        pass
    
# use to debug
# st.markdown(f"{type(time_interval)}")

# iterate through csv files and convert into pandas Dataframe
# apply the TTM Squeeze indicator
# add columns for Bollinger bands upper and lower, Keltner bands upper and lower
# 20 SMA, Standard Deviation +/- 2

dataframes = {}

for filename in os.listdir("datasets"): # list all files in directory
    # print(filename)
    symbol = filename.split(".")[0]
    # print(symbol)
    
    df = pd.read_csv("datasets/{}".format(filename))
    
    # renaming 1st column to date so that I can plot w/o errors. list of names[Unnamed: 0]
    df = df.rename(columns={'Datetime':'Date'})
    
    # df = df['Date'].astype(dat)
    # df['Date'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M')
    # st.markdown(f"{df.Date}")
    
    if df.empty:
        continue
    
    # to change the
    mult = 2.0 
    multKC = 1.5 # easier squeeze to develop 
    
    # calculate simple 20 moving average and bol bands, I change from 2 to 1.5 * df['stddev']
    df['20sma'] = df['Close'].rolling(window=20).mean()
    # df['20ema'] = ta.ema(df['Close'], length=20)
    

    # if LABEL == "ema":
    #     df['20ema'] = df.ta.ema(df['Close'], length=20)
    # else:
    #     df['20sma'] = df.ta.sma(df['Close'], length=20)
        

    
    df['lower_band'] = df['Close'].rolling(window=20).mean() - df['Close'].rolling(window=20).std()* 2
    df['upper_band'] = df['Close'].rolling(window=20).mean() + df['Close'].rolling(window=20).std()* 2
    
    df['TR'] = abs(df['High'] - df['Low'])
    df['ATR'] = df['TR'].rolling(window=20).mean()
    
    
    # Keltner Channel Multiplier can adjusted to {'white': 2.0, 'red': 1.5, 'yellow': 1.0} in comparison to JS Sqz pro2
    # white dot squeeze
    df['lower_keltner'] = df['20sma'] - df['ATR'] * multKC
    df['upper_keltner'] = df['20sma'] + df['ATR'] * multKC
    
    
    def in_squeeze(df):
        return df['lower_band'] > df['lower_keltner'] and df['upper_band'] < df['upper_keltner']
    
    df['squeeze_on'] = df.apply(in_squeeze, axis= 1)
    
    if df.iloc[-3]['squeeze_on'] and not df.iloc[-1]['squeeze_on']:
        prev = float(df.iloc[-2]['20sma'])
        cur = float(df.iloc[-1]['20sma'])
        if prev <= cur:
            OUT_SQZ.append([symbol, 'Long'])
        else:
            OUT_SQZ.append([symbol, 'Short'])
                    
        # st.write("{} coming out of a squeeze on {} :chart_with_upwards_trend:".format(symbol, time_interval))
        # print("{} is coming out of a squeeze".format(symbol))
        
    if df.iloc[-1]['squeeze_on']:
        prev2 = float(df.iloc[-2]['20sma'])
        cur2 = float(df.iloc[-1]['20sma'])
        if prev2 <= cur2:
            IN_SQZ.append([symbol, 'Up'])
        else:
            IN_SQZ.append([symbol, 'Down'])
        

    
    # if df.iloc[-3]['squeeze_on'] and not df.iloc[-1]['squeeze_on']:
    #     print("{} is coming out of a squeeze".format(symbol))
        
    # if df.iloc[-1]['squeeze_on']:
    #     print("{} is in a squeeze".format(symbol))
    
    
    # store df in dictionary in reverse so that the current date is at top
    dataframes[symbol] = df
    
# Display crypto's SQZ categories
x2 = pd.DataFrame(OUT_SQZ, columns=['Release', 'Possible'])
st.write(f"Just Released on {time_interval} :bell:", x2)

x = pd.DataFrame(IN_SQZ, columns=['Squeeze', 'Trending'])
st.write(f"Squeeze on {time_interval} :no_bell:", x)


# create a sidebar select box to choose symbol to plot
syms = st.sidebar.selectbox('Crypto Symbol', options=SYMBOLS)

st.subheader("Explore {} {} Chart and Dataframe".format(syms, time_interval))

# plot selected Symbol's Dataframe
# I don't think I want to include the additional 

# st.dataframe(dataframes.get(syms, None).iloc[::-1])



def chart(df):
    candlestick = go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color= 'cyan', decreasing_line_color= 'violet')
    upper_band = go.Scatter(x=df['Date'], y=df['upper_band'], name='Upper Bollinger Band', line={'color': 'red'})
    lower_band = go.Scatter(x=df['Date'], y=df['lower_band'], name='Lower Bollinger Band', line={'color': 'red'})

    upper_keltner = go.Scatter(x=df['Date'], y=df['upper_keltner'], name='Upper Keltner Channel', line={'color': 'blue'})
    lower_keltner = go.Scatter(x=df['Date'], y=df['lower_keltner'], name='Lower Keltner Channel', line={'color': 'blue'})

    fig = go.Figure(data=[candlestick, upper_band, lower_band, upper_keltner, lower_keltner])
    fig.layout.xaxis.type = 'date'
    fig.layout.xaxis.rangeslider.visible = False
    fig.update_layout(autosize=False, width=1500, height=800) #width=800, height=800,
    st.plotly_chart(fig)
    
plot = dataframes.get(f"{syms}", None)
# chart(plot)

# st.markdown(dataframes)
    
# progress meter

with st.spinner('wait for it...'):
    time.sleep(5)
    chart(plot)
    st.dataframe(dataframes.get(syms, None).iloc[::-1])
st.success("Done!")


# Give results on whether the cryptos are in a squeeze or coming out of a squeeze.


