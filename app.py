import streamlit as st, pandas as pd, yfinance as yf, warnings, io, contextlib
import plotly.graph_objects as go
warnings.filterwarnings("ignore")

st.set_page_config(layout="wide")
st.title("NSE 227 - PART 2 (114-227)")

@st.cache_data(ttl=3600)
def load():
    df=pd.read_excel("All_227_Stocks_Financial_Analysis.xlsx")
    return df['Stock'].dropna().tolist()

all_stocks = load()
companies = all_stocks[113:]
st.success(f"Part 2 Loaded: {len(companies)} stocks")

TM={"Aadhar Hsg. Fin.":"AADHARHFC","Aarti Industries":"AARTIIND","Aavas Financiers":"AAVAS","ADF Foods":"ADFFOODS","Aditya Vision":"ADITYAVISION","Affle 3i":"AFFLE","Ajanta Pharma":"AJANTPHARM","Apar Industries":"APARINDS","APL Apollo Tubes":"APLAPOLLO","Apollo Hospitals":"APOLLOHOSP","Asian Paints":"ASIANPAINT","Avenue Supermarts":"DMART","Britannia Industries":"BRITANNIA","BSE":"BSE","Campus Activewear":"CAMPUS"}
def gt(c):
    if c in TM: return TM[c]
    return c.split()[0][:10].upper()
tks=[gt(c) for c in companies]

def rsi(s):
    d=s.diff(); g=d.clip(lower=0); l=-d.clip(upper=0)
    a=g.ewm(com=13, min_periods=14).mean(); b=l.ewm(com=13, min_periods=14).mean()
    rs=a/b
    return 100-(100/(1+rs))

@st.cache_data(ttl=600, show_spinner=False)
def fetch():
    rows=[]; charts={}
    for i in range(0,len(tks),20):
        batch=[f"{x}.NS" for x in tks[i:i+20]]
        comps=companies[i:i+20]; syms=tks[i:i+20]
        f=io.StringIO()
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            try:
                d=yf.download(batch, period="6mo", group_by='ticker', threads=False, progress=False, auto_adjust=True)
                for comp,sy,ns in zip(comps,syms,batch):
                    try:
                        if len(batch)==1:
                            df=d
                        else:
                            if hasattr(d.columns,'levels') and ns in d.columns.levels[0]:
                                df=d[ns]
                            else:
                                continue
                        if len(df.dropna())<30: continue
                        df=df.dropna()
                        lo=float(df['Low'].tail(20).min()); hi=float(df['High'].tail(20).max())
                        dL=lo*0.97; dH=lo*1.03; sL=hi*0.97; sH=hi*1.03
                        r=float(rsi(df['Close']).iloc[-1]); last=float(df['Close'].iloc[-1])
                        sig="BUY" if last<=dH*1.08 and r<52 else ("SELL" if last>=sL*0.92 and r>58 else "HOLD")
                        rows.append({"Stock":comp,"Ticker":sy,"CMP":round(last,1),"Support":round(lo,1),"Resistance":round(hi,1),"Demand BOX":f"{dL:.0f}-{dH:.0f}","Supply BOX":f"{sL:.0f}-{sH:.0f}","RSI":round(r,1),"Signal":sig,"_dL":dL,"_dH":dH,"_sL":sL,"_sH":sH})
                        charts[comp]=df.tail(90)
                    except Exception as e:
                        continue
            except Exception as e:
                continue
    return pd.DataFrame(rows), charts

live,chart_dict=fetch()
if len(live)==0: st.warning("Yahoo busy, refresh after 2 mins"); st.stop()

sf=st.selectbox("Signal",["ALL","BUY","SELL","HOLD"]); sr=st.text_input("Search")
fl=live.copy()
if sf!="ALL": fl=fl[fl['Signal']==sf]
if sr: fl=fl[fl['Stock'].str.contains(sr, case=False)]
st.dataframe(fl.drop(columns=["_dL","_dH","_sL","_sH"], errors='ignore'), use_container_width=True, height=400)
st.caption(f"BUY:{len(live[live['Signal']=='BUY'])} SELL:{len(live[live['Signal']=='SELL'])} LIVE:{len(live)}/{len(companies)}")

sel=st.selectbox("Select Chart", fl['Stock'].tolist() if len(fl)>0 else live['Stock'].tolist())
row=live[live['Stock']==sel].iloc[0]; df=chart_dict.get(sel)
if df is not None:
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
    fig.add_hline(y=row['Support'], line_dash="dash", line_color="green")
    fig.add_hline(y=row['Resistance'], line_dash="dash", line_color="red")
    fig.add_shape(type="rect", x0=df.index[0], x1=df.index[-1], y0=row['_dL'], y1=row['_dH'], fillcolor="rgba(0,255,0,0.2)", line=dict(color="green", width=2))
    fig.add_shape(type="rect", x0=df.index[0], x1=df.index[-1], y0=row['_sL'], y1=row['_sH'], fillcolor="rgba(255,0,0,0.2)", line=dict(color="red", width=2))
    fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, title=f"{sel} CMP {row['CMP']} {row['Signal']}")
    st.plotly_chart(fig, use_container_width=True)
