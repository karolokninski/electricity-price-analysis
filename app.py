# %%
import pandas as pd
from datetime import datetime

# %%
data_path = '/home/karol/electricity-prices-app/prices.csv'
dateparse = lambda x: datetime.strptime(x, '%Y%m%d')

df = pd.read_csv(data_path, sep=';', parse_dates=['Data'], date_parser=dateparse)

# %% [markdown]
# Data cleaning

# %%
for i in range(len(df.RCE)):
    df.RCE[i] = df.RCE[i].replace(',', '')

df['Time'] = pd.to_numeric(df['Time'], errors='coerce')

df.RCE = df.RCE.astype(float)
df.Time = df.Time.astype(float)

df = df[df['Time'].notna()]

df.set_index('Data', inplace=True)
df.index += df.Time.apply(lambda x: pd.Timedelta(f'{x}h'))
df = df.drop('Time', axis=1)

# %%
# df.groupby(by='Data').count()
# df.asfreq(freq='30D')

# %% [markdown]
# Creating a dash app

# %%
# from jupyter_dash import JupyterDash
from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

import plotly.express as px
import plotly.graph_objects as go

from datetime import date

# %%
meta_tags = [{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
load_figure_template("materia")
external_stylesheets = [dbc.themes.MATERIA]

app = Dash(__name__, meta_tags=meta_tags, external_stylesheets=external_stylesheets)

fig = go.Figure()
fig = px.scatter(df, labels={'variable':'Zmienna', 'value': 'Cena', 'index': 'Data'}, title='Wykres rynkowej ceny energii elektrycznej')
fig.update_layout(legend_title_text='Legenda')
# fig.update_layout(showlegend=False)

controls = html.Div([
        html.Div([
            html.H5('Zakres dat:'),
            dcc.DatePickerRange(
                id='date-picker-range',
                min_date_allowed=date(2020, 1, 1),
                max_date_allowed=date(2023, 5, 10),
                start_date=date(2020, 1, 1),
                end_date=date(2023, 5, 10),
                className="d-flex justify-content-center",)
        ], className="px-3 pt-3"),

        html.Hr(),

        html.Div([
            html.H5('Średnia:'),
            dcc.Dropdown(
                id='aggregation-type',
                options=['Godzinowa', 'Dzienna', 'Tygodniowa', 'Miesięczna', 'Roczna', 'Automatyczna'],
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

graph = dcc.Graph(id='graph-content', 
                  style={'height':'100%'},
                  figure=fig,
                  config={'scrollZoom': True, 'displayModeBar': True, 'displaylogo': False, 'locale': 'pl'})

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
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('plot-type', 'value'),
    Input('aggregation-type', 'value')
)

def update_graph(start_date, end_date, plot_type, aggregation_type):
    dff = df[start_date:end_date]

    # if aggregation_type == 'Automatyczna':

    dic = {'Godzinowa':'1h', 'Dzienna':'1D', 'Tygodniowa':'1W', 'Miesięczna':'1M', 'Roczna':'1Y'}

    dff = dff.resample(dic[aggregation_type]).mean()

    fig = go.Figure()

    if plot_type == 'Punktowy':
        fig = px.scatter(dff, labels={'variable':'Zmienna', 'value': 'Cena', 'index': 'Data'}, title='Wykres rynkowej ceny energii elektrycznej')

    else:
        fig = px.line(dff, labels={'variable':'Zmienna', 'value': 'Cena', 'index': 'Data'}, title='Wykres rynkowej ceny energii elektrycznej')

    fig.update_layout(legend_title_text='Legenda')
    # fig.update_layout(showlegend=False)

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

# %% [markdown]
# do zrobienia:
# - zmienic wyglad i dodac nowe funkcje
# - docker
# - sprobowac stworzyc obraz na dockerze


