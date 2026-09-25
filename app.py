import streamlit as st, pandas as pd, yfinance as yf, warnings, logging, io, contextlib
import plotly.graph_objects as go
warnings.filterwarnings("ignore"); logging.getLogger("yfinance").setLevel(logging.CRITICAL)

st.set_page_config(layout="wide")
st.title("NSE 227 - PART 2 (114-227) BOX + Candles")

@st.cache_data(ttl=3600)
def load():
    df=pd.read_excel("All_227_Stocks_Financial_Analysis.xlsx")
    return df['Stock'].dropna().astype(str).tolist()

all_companies = load()
companies = all_companies[113:]

st.success(f"Loaded {len(companies)} Stocks (Part 2 of {len(all_companies)})")

TM={"Aadhar Hsg. Fin.":"AADHARHFC","Aarti Industries":"AARTIIND","Aavas Financiers":"AAVAS","ADF Foods":"ADFFOODS","Aditya Vision":"ADITYAVISION","Affle 3i":"AFFLE","Ajanta Pharma":"AJANTPHARM","Apar Industries":"APARINDS","APL Apollo Tubes":"APLAPOLLO","Apollo Hospitals":"APOLLOHOSP","Asian Paints":"ASIANPAINT","Avenue Supermarts":"DMART","Britannia Industries":"BRITANNIA","BSE":"BSE","Campus Activewear":"CAMPUS"}

def gt(c):
    c=c.strip()
    if c in TM: return TM[c]
    return c.split()[0][:10].upper()

tks=[gt(c) for c in companies]

def rsi(s):
    d=s.diff(); g=d.clip(lower=0); l=-d.clip(upper=0)
    a=g.ewm(com=13, min_periods=14).mean(); b=l.ewm(com=13, min_periods=14).mean()
    return 100-(100/(1+a/b))

@st.cache_data(ttl=600, show_spinner=False)
def fetch():
    rows=[]; charts={}
    for i in range(0,len(tks),30):
        batch=[f"{x}.NS" for x in tks[i:i+30]]
        comps=companies[i:i+30]; syms=tks[i:i+30]
        f=io.StringIO()
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            try:
                d=yf.download(batch, period="6mo", group_by='ticker', threads=False, progress=False, auto_adjust=True, show_errors=False)
                for comp,sy,ns in zip(comps,syms,batch):
                    try:
                        df = d if len(batch)==1 else (d[ns] if hasattr(d.columns,'levels') and ns in d.columns.levels[0] else None)
                        if df is None or len(df.dropna())<30: continue
                        df=df.dropna(); lo=float(df['Low'].tail(20).min()); hi=float(df['High'].tail(20).max())
                        dL=lo*0.97; dH=lo*1.03;
