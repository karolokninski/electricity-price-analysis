# %%
import pandas as pd
import time
from datetime import date, timedelta, datetime
from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

# %%
from sqlalchemy import Column, DateTime, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import urllib

Base = declarative_base()

class ElectricityPrices(Base):
    __tablename__ = 'electricity_prices'

    index = Column('index', DateTime, primary_key=True)
    RCE = Column('RCE', Float)

    def __init__(self, index, RCE):
        self.index = index
        self.RCE = RCE

    def __repr__(self):
        return f'({self.index}) {self.RCE}'

conn = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:electricity-prices.database.windows.net,1433;Database=electricity-prices-db;Uid=kepucino;Pwd=ZAQ!2wsx;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
params = urllib.parse.quote_plus(conn)
conn_str = 'mssql+pyodbc:///?autocommit=true&odbc_connect={}'.format(params)

engine = create_engine(conn_str, echo=True)

Session = sessionmaker(bind=engine)
session = Session()

my_query = 'SELECT * FROM [dbo].[electricity_prices]'

df = pd.read_sql(my_query, engine, index_col='index')

# %%
meta_tags = [{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
external_stylesheets = [dbc.themes.BOOTSTRAP]

app = Dash(__name__, meta_tags=meta_tags, external_stylesheets=external_stylesheets)
server = app.server

layout = dict(
    legend_title_text='Legenda',
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                    label='1m',
                    step='month',
                    stepmode='backward'),
                dict(count=6,
                    label='6m',
                    step='month',
                    stepmode='backward'),
                dict(count=1,
                    label='YTD',
                    step='year',
                    stepmode='todate'),
                dict(count=1,
                    label='1y',
                    step='year',
                    stepmode='backward'),
                dict(count=3,
                    label='3y',
                    step='year',
                    stepmode='backward'),
                dict(step='all')
            ]),
            activecolor = '#09f',
        ),
        rangeslider=dict(
            visible = True,
            # bordercolor = '#fff',
            bgcolor = '#49f',
            thickness = 0.1,
        ),
        type='date',
    )
)


controls = html.Div([
        html.Div([
            html.H5('Zakres dat:'),
            dcc.DatePickerRange(
                id='date-picker-range',
                min_date_allowed=date(2018, 1, 1),
                max_date_allowed=date.today() + timedelta(1),
                start_date=date(2018, 1, 1),
                end_date=date.today() + timedelta(1),
                className="d-flex justify-content-center",)
        ], className="px-3 pt-3"),

        html.Hr(),

        html.Div([
            html.H5('Średnia:'),
            dcc.Dropdown(
                id='aggregation-type',
                options=['Godzinowa', 'Dzienna', 'Tygodniowa', 'Miesięczna', 'Roczna'],
                value='Dzienna')
        ], className="px-3"),

        html.Hr(),

        html.Div([
            html.H5('Rodzaj wykresu:'),
            html.Div([
                dcc.RadioItems(
                    ['Punktowy', 'Liniowy'],
                    'Liniowy',
                    id='plot-type',
                    labelStyle={'display': 'inline-block', 'margin':'8px', 'margin-right':'16px'})
            ], className="d-flex align-items-center border"),
        ], className="px-3 pb-3"),
    ],
    className="d-grid h-auto gap-1 border"
)

graph = html.Div([
    dcc.Graph(id='graph-content',
        config={'scrollZoom': True, 'displayModeBar': True, 'displaylogo': False, 'locale': 'pl'},
    ),

    # html.Span('Najwyższa cena: '),
    # html.Span(id='graph-bottom-text')
])


app.layout = dbc.Container(
    [
        html.Br(),
        html.H1("Rynkowa cena energii elektrycznej (RCE)"),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(controls, className='col-12 col-lg-3'),
                dbc.Col(graph, className='col-12 col-lg-9'),
            ],
            align="center",
            className='h-100',
        ),
    ],
    fluid=True,
    style={'height':'85vh', 'width':'99vw'},
    # className="dbc"
)

@app.callback(
    Output('graph-content', 'figure'),
    Output('date-picker-range', 'max_date_allowed'),
    Output('date-picker-range', 'end_date'),
    # Output('graph-bottom-text', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('plot-type', 'value'),
    Input('aggregation-type', 'value')
)

def update_graph(start_date, end_date, plot_type, aggregation_type):
    max_end_date = df.index.max()

    dff = df[start_date:end_date]

    dic = {'Godzinowa':'1h', 'Dzienna':'1D', 'Tygodniowa':'1W', 'Miesięczna':'1M', 'Roczna':'1Y'}

    dff = dff.resample(dic[aggregation_type]).mean()

    if plot_type == 'Punktowy':
        fig = px.scatter(dff, labels={'variable':'Zmienna', 'value': 'Cena', 'index': 'Data'}, title='Wykres rynkowej ceny energii elektrycznej')

    else:
        fig = px.line(dff, labels={'variable':'Zmienna', 'value': 'Cena', 'index': 'Data'}, title='Wykres rynkowej ceny energii elektrycznej')

    fig.update_layout(layout)
    fig.update_layout(height=600)
    # fig.update_layout(showlegend=False)

    return fig, max_end_date, max_end_date
    # return fig, dff.RCE.max()


# if __name__ == 'app':
#     app.run_server(debug=True)

# %% [markdown]
# do zrobienia:
# - zmienic wyglad i dodac nowe funkcje


