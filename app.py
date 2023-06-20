# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import urllib.request
import time
from datetime import date, timedelta, datetime
import os
from jupyter_dash import JupyterDash
from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import plotly.express as px
import plotly.graph_objects as go
from pytz import utc

# %%
data_path = 'prices.csv'
dateparse = lambda x: datetime.strptime(x, '%Y%m%d')

df = pd.read_csv(data_path, sep=';', index_col=0, parse_dates=['Data'], date_parser=dateparse)

# %% [markdown]
# Data cleaning

# %%
df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
df = df[df['Time'].notna()]
df.RCE = df.RCE.astype(float)
df.Time = df.Time.astype(int)
df.index += df.Time.apply(lambda x: pd.Timedelta(f'{x-1}h'))
df = df.drop('Time', axis=1)
df = df.resample('1h').mean()

# df.groupby(by='Data').count()
# df.asfreq(freq='30D')

# %% [markdown]
# Creating a dash app

# %%
def get_data():
    tomorrow = date.today() + timedelta(1)
    next_day = tomorrow + timedelta(1)

    first_day = tomorrow.strftime('%Y%m%d')
    last_day = next_day.strftime('%Y%m%d')

    # Replace with the actual download link
    download_link = f'https://www.pse.pl/getcsv/-/export/csv/EN_PRICE/data_od/{first_day}/data_do/{last_day}'

    # Download the file
    urllib.request.urlretrieve(download_link, f'new-prices.csv')

    # Wait for the download to complete
    while True:
        time.sleep(1)
        if f'new-prices.csv.crdownload' not in os.listdir():
            break

def update_csv():
    file1 = 'new-prices.csv'
    file2 = 'prices.csv'

    with open(file1, "r") as f:
        rows = f.readlines()[1:]

    target_file = open(file2, 'a')

    for row in rows:
        target_file.write(row)

    target_file.close()

def create_new_df():
    data_path = 'new-prices.csv'
    dateparse = lambda x: datetime.strptime(x, '%Y%m%d')

    dff = pd.read_csv(data_path, sep=';', index_col=0, parse_dates=['Data'], date_parser=dateparse)

    dff['Time'] = pd.to_numeric(dff['Time'], errors='coerce')
    dff = dff[dff['Time'].notna()]
    dff.RCE = dff.RCE.astype(float)
    dff.Time = dff.Time.astype(int)
    dff.index += dff.Time.apply(lambda x: pd.Timedelta(f'{x-1}h'))
    dff = dff.drop('Time', axis=1)

    return dff

def update_data():
    print("Updating...")
    get_data()
    update_csv()
    global df
    df = pd.concat([df, create_new_df()])
    print("Done.")

# %%
meta_tags = [{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
load_figure_template("materia")
external_stylesheets = [dbc.themes.MATERIA]

app = JupyterDash(__name__, meta_tags=meta_tags, external_stylesheets=external_stylesheets)

fig = go.Figure()
fig = px.scatter(df, labels={'variable':'Zmienna', 'value': 'Cena', 'index': 'Data'}, title='Wykres rynkowej ceny energii elektrycznej')
fig.update_layout(legend_title_text='Legenda')
fig.update_layout(showlegend=False)

controls = html.Div([
        html.Div([
            html.H5('Zakres dat:'),
            dcc.DatePickerRange(
                id='date-picker-range',
                min_date_allowed=date(2020, 1, 1),
                max_date_allowed=date.today() + timedelta(1),
                start_date=date(2020, 1, 1),
                end_date=date.today() + timedelta(1),
                className="d-flex justify-content-center",)
        ], className="px-3 pt-3"),

        html.Hr(),

        html.Div([
            html.H5('Średnia:'),
            dcc.Dropdown(
                id='aggregation-type',
                options=['Godzinowa', 'Dzienna', 'Tygodniowa', 'Miesięczna', 'Roczna'],
                value='Godzinowa')
        ], className="px-3"),

        html.Hr(),

        html.Div([
            html.H5('Rodzaj wykresu:'),
            html.Div([
                dcc.RadioItems(
                    ['Punktowy', 'Liniowy'],
                    'Punktowy',
                    id='plot-type',
                    labelStyle={'display': 'inline-block', 'margin':'8px', 'margin-right':'16px'})
            ], className="d-flex align-items-center border"),
        ], className="px-3 pb-3"),
    ],
    className="d-grid h-auto gap-1 border"
)

graph = dbc.Row([
    dcc.Graph(id='graph-content', 
        style={'height':'100%'},
        figure=fig,
        config={'scrollZoom': True, 'displayModeBar': True, 'displaylogo': False, 'locale': 'pl'}),
    # html.Span('Najwyższa cena: '),
    # html.Span(id='graph-bottom-text')
])


app.layout = dbc.Container(
    [
        html.H1("Rynkowa cena energii elektrycznej (RCE)"),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(controls, className='col-12 col-lg-3'),
                dbc.Col(graph, className='col-12 col-lg-9 h-75'),
            ],
            align="center",
            className='h-100',
        ),
    ],
    fluid=True,
    style={'height':'85vh'},
    className="dbc"
)

@app.callback(
    Output('graph-content', 'figure'),
    # Output('graph-bottom-text', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('plot-type', 'value'),
    Input('aggregation-type', 'value')
)

def update_graph(start_date, end_date, plot_type, aggregation_type):
    dff = df[start_date:end_date]

    dic = {'Godzinowa':'1h', 'Dzienna':'1D', 'Tygodniowa':'1W', 'Miesięczna':'1M', 'Roczna':'1Y'}

    dff = dff.resample(dic[aggregation_type]).mean()

    fig = go.Figure()

    if plot_type == 'Punktowy':
        fig = px.scatter(dff, labels={'variable':'Zmienna', 'value': 'Cena', 'index': 'Data'}, title='Wykres rynkowej ceny energii elektrycznej')

    else:
        fig = px.line(dff, labels={'variable':'Zmienna', 'value': 'Cena', 'index': 'Data'}, title='Wykres rynkowej ceny energii elektrycznej')

    fig.update_layout(legend_title_text='Legenda')
    fig.update_layout(showlegend=False)

    return fig
    # return fig, dff.RCE.max()


if __name__ == '__main__':
    app.run_server(debug=True)

    scheduler = BackgroundScheduler()
    scheduler.configure(timezone=utc)
    scheduler.add_job(update_data, 'interval', days=1)
    scheduler.start()

# %% [markdown]
# do zrobienia:
# - zmienic wyglad i dodac nowe funkcje
