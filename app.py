# %%
import pandas as pd
from datetime import date, timedelta, datetime
from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import dash_leaflet as dl

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

driver = '{ODBC Driver 18 for SQL Server}'
uid = 'kepucino'
pwd = 'ZAQ!2wsx'

conn = f'Driver={driver};Server=tcp:electricity-prices.database.windows.net,1433;Database=electricity-prices-db;Uid={uid};Pwd={pwd};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
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
                dict(count=14,
                    label='2w',
                    step='day',
                    stepmode='backward'),
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
            bgcolor = '#49f',
            thickness = 0.1,
        ),
        type='date',
    )
)


controls_prices = html.Div([
        html.Div([
            html.H5('Zakres dat:'),
            dcc.DatePickerRange(
                id='date-picker-range',
                min_date_allowed=df.index.min(),
                max_date_allowed=df.index.max(),
                start_date=df.index.min(),
                end_date=df.index.max(),
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

graph_prices = html.Div([
    dcc.Graph(id='graph-prices',
        config={'scrollZoom': True, 'displayModeBar': True, 'displaylogo': False, 'locale': 'pl'},
    ),
])


controls_profit = html.Div([
        html.Div([
            html.H5('Wybierz lokalizację:'),
            # html.Button("Dodaj lokalizację automatycznie", id="btn-location"),
            # dcc.Geolocation(id="geolocation"),
            dl.Map(id='map-location', style={'height': '250px', 'margin': '15px 0px'}, center=[52, 20], zoom=5, children=[
                dl.TileLayer(),
                dl.LayerGroup(id="layer-location"),
            ]),
        ], className="px-3 pt-3"),

        html.Hr(),

        html.Div([
            html.H5('Reszta parametrów: '),

            dcc.Input(
                id="input-peak-power",
                type='number',
                placeholder="Moc nominalna PV (kW)",
            ),

            dcc.Input(
                id="input-loss",
                type='number',
                placeholder="Straty (%)",
            ),

            dcc.Input(
                id="input-angle",
                type='number',
                placeholder="Kąt nachylenia (w stopniach)",
            ),

            dcc.Input(
                id="input-azimuth",
                type='number',
                placeholder="Kąt azymutu (w stopniach)",
            ),

            dcc.Input(
                id="input-location",
                type='text',
                placeholder="Lokalizacja",
            ),
            html.Button(
                "Wygeneruj",
                id="btn-confirm-location",
            ),

            html.P(
                id="text-info",
                children="Wprowadź dane",
            ),  

            html.Div([
                
            ]),

        ], className="px-3 pt-3"),


        html.Hr(),

        html.Div([
            html.H5('Zakres dat:'),
            dcc.DatePickerRange(
                id='date-picker-range-profit',
                min_date_allowed=date(2005, 1, 1),
                max_date_allowed=date(2020, 12, 31),
                start_date=date(2005, 1, 1),
                end_date=date(2020, 12, 31),
                className="d-flex justify-content-center",)
        ], className="px-3 pt-3"),

        html.Hr(),

        html.Div([
            html.H5('Średnia:'),
            dcc.Dropdown(
                id='aggregation-type-profit',
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
                    id='plot-type-profit',
                    labelStyle={'display': 'inline-block', 'margin':'8px', 'margin-right':'16px'})
            ], className="d-flex align-items-center border"),
        ], className="px-3 pb-3"),
    ],
    className="d-grid h-auto gap-1 border"
)

graphs_profit = html.Div([
    dbc.Row([
        dcc.Graph(
            id='graph-production',
            config={'scrollZoom': True, 'displayModeBar': True, 'displaylogo': False, 'locale': 'pl'},
        ),
        dcc.Graph(
            id='graph-profit',
            config={'scrollZoom': True, 'displayModeBar': True, 'displaylogo': False, 'locale': 'pl'},
        ),
    ], align="center")
])

app.layout = dbc.Container([
        html.H1('Dash Tabs component demo'),
        dcc.Tabs([
            dcc.Tab(label="Rynkowa cena energii elektrycznej (RCE)", children=[
                html.Br(),
                html.H1("Rynkowa cena energii elektrycznej (RCE)"),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(controls_prices, className='col-12 col-lg-3'),
                        dbc.Col(graph_prices, className='col-12 col-lg-9'),
                    ],
                    align="center",
                ),
            ]),
            dcc.Tab(label="Kalkulator zysków", children=[
                html.Br(),
                html.H1("Kalkulator zysków"),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(controls_profit, className='col-12 col-lg-3'),
                        dbc.Col(graphs_profit, className='col-12 col-lg-9'),
                    ],
                    align="center",
                ),
            ])
        ]),
        html.Div(id='tabs-content-example-graph')
    ],
    fluid=True,
    style={'height':'85vh', 'width':'99vw'},
    className="dbc"
)

# @callback(
#     Output('tabs-content-example-graph', 'children'),
#     Input('tabs-example-graph', 'value')
# )

# def render_content(tab):
#     if tab == 'tab-1-example-graph':
#         return tab_prices
    
#     elif tab == 'tab-2-example-graph':
#         return tab_profit

@app.callback(
    Output('graph-prices', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('plot-type', 'value'),
    Input('aggregation-type', 'value')
)

def update_prices_graph(start_date, end_date, plot_type, aggregation_type):
    dff = df[start_date:end_date]

    dic = {'Godzinowa':'1h', 'Dzienna':'1D', 'Tygodniowa':'1W', 'Miesięczna':'1M', 'Roczna':'1Y'}

    dff = dff.resample(dic[aggregation_type]).mean()

    labels = {'variable':'Zmienna', 'value': 'Cena', 'index': 'Data'}
    title = 'Wykres rynkowej ceny energii elektrycznej'

    if plot_type == 'Punktowy':
        fig = px.scatter(dff, labels=labels, title=title)

    else:
        fig = px.line(dff, labels=labels, title=title)

    fig.update_layout(layout)
    fig.update_layout(height=600)
    # fig.update_layout(showlegend=False)

    return fig

@app.callback(
    Output('input-location', 'value'),
    Output("layer-location", "children"),
    [Input('map-location', 'click_lat_lng')],
    Input('map-location', 'center')
)

def update_location(pos, initial_val):
    if pos:
        return "{:.4f}, {:.4f}".format(*pos), [dl.Marker(position=pos, children=dl.Tooltip("{:.4f}, {:.4f}".format(*pos)))]
    
    return "Wprowadź lokalizację", [dl.Marker(position=initial_val, children=dl.Tooltip("{:.4f}, {:.4f}".format(*initial_val)))]

@app.callback(
    Output('graph-production', 'figure'),
    Output('graph-profit', 'figure'),
    Output('text-info', 'children'),
    Input('btn-confirm-location', 'n_clicks'),
    Input('input-peak-power', 'value'),
    Input('input-loss', 'value'),
    Input('input-angle', 'value'),
    Input('input-azimuth', 'value'),
    Input('input-location', 'value'),
    Input('date-picker-range-profit', 'start_date'),
    Input('date-picker-range-profit', 'end_date'),
    Input('plot-type-profit', 'value'),
    Input('aggregation-type-profit', 'value')
)

def update_profit_graphs(click, peak_power, loss, angle, azimuth, location, start_date, end_date, plot_type, aggregation_type):
    # peak_power, loss, angle, azimuth, location = 5, 90, 30, 0, "52.2297, 21.0122"

    if not (click != None and click > 0 and peak_power != None and loss != None and angle != None and azimuth != None and location != None):
        return {}, {}, 'Źle podane dane'

    pos = location.split(", ")

    API_string = f'https://re.jrc.ec.europa.eu/api/v5_2/seriescalc?pvcalculation=1&peakpower={peak_power}&loss={loss}&angle={angle}&aspect={azimuth}&lat={pos[0]}&lon={pos[1]}&startyear={start_date[0:4]}&endyear={end_date[0:4]}'

    dff = pd.read_csv(API_string, skiprows=10, skipfooter=11)

    dff.index = dff.time.apply(lambda x: datetime(int(x[0:4]), int(x[4:6]), int(x[6:8]), int(x[9:11])))
    dff = dff.drop('time', axis=1)
    dff = dff[start_date:end_date]

    dic = {'Godzinowa':'1h', 'Dzienna':'1D', 'Tygodniowa':'1W', 'Miesięczna':'1M', 'Roczna':'1Y'}

    dff = dff.resample(dic[aggregation_type]).mean()

    labels = {'variable':'Zmienna', 'value': 'Wartość', 'time': 'Data'}
    title = 'Wykres produkcji energii po zastosowaniu fotowoltaiki'

    if plot_type == 'Punktowy':
        fig = px.scatter(dff, labels=labels, title=title)

    else:
        fig = px.line(dff, labels=labels, title=title)

    fig.update_layout(layout)
    fig.update_layout(height=500)
    # fig.update_layout(showlegend=False)
    
    begin = max(dff.index.min(), df.index.min())
    end = min(dff.index.max(), df.index.max())
    dff['profit'] = ''
    dff.profit = dff[begin:end].P * df.RCE # blad z df.RCE[begin:end]
    dff.profit = dff.profit[begin:end]
    dff['linear_profit'] = ''
    dff.linear_profit = dff.profit.cumsum(axis=0)
    dff.linear_profit = dff.linear_profit[begin:end]
    dff = dff.dropna()

    labels = {'variable':'Zmienna', 'value': 'Wartość', 'time': 'Data'}
    title = 'Wykres produkcji energii po zastosowaniu fotowoltaiki'

    if plot_type == 'Punktowy':
        fig2 = px.scatter(dff[['profit', 'linear_profit']], labels=labels, title=title)

    else:
        fig2 = px.line(dff[['profit', 'linear_profit']], labels=labels, title=title)

    fig.update_layout(layout)
    fig.update_layout(height=500)
    # fig.update_layout(showlegend=False)

    return fig, fig2, f'lat={pos[0]}&lon={pos[1]}'

# @callback(
#     Output("geolocation", "update_now"),
#     Input("btn-location", "n_clicks")
# )

# def update_now(click):
#     return click and click > 0

# @callback(
#     Output("input-location", "value", allow_duplicate=True),
#     Input("geolocation", "position"),
# )

# def display_output(pos):
#     if pos:
#         return "({:.4f}, {:.4f})".format(*pos)
    
#     return "No position data available"


# if __name__ == '__main__':
#     app.run_server(debug=True)

    # scheduler = BackgroundScheduler()
    # scheduler.configure(timezone=utc)
    # scheduler.add_job(update_data, 'interval', days=1)
    # scheduler.start()

# %%
# df2 = pd.read_csv('https://re.jrc.ec.europa.eu/api/v5_2/seriescalc?lat=52.5363&lon=21.4877&pvcalculation=1&peakpower=3&loss=90&angle=30&aspect=0&startyear=2015&endyear=2020', skiprows=10, skipfooter=11)
# df2.index = df2.time.apply(lambda x: datetime(int(x[0:4]), int(x[4:6]), int(x[6:8]), int(x[9:11])))
# df2 = df2.drop('time', axis=1)
# # df2.index += pd.DateOffset(years=5)

# consumption = [0, 0, 0, 0, 0, 0, 50, 150, 100, 0, 0, 0, 0, 0, 0, 0, 100, 300, 350, 100, 50, 0, 0, 0, ]


