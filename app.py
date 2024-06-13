from dash import Dash, dcc, html, dash_table, Input, Output
import dash_daq as daq
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import requests
import math

# Function to fetch data and handle errors
def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to preprocess the dataframe
def preprocess_kp_dataframe(df):
    df = pd.DataFrame(df, columns=["time_tag", "Kp", "a_running", "station_count"])
    df = df.drop(0)  # Drop the header row if it exists
    df['time_tag'] = pd.to_datetime(df['time_tag'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')  # Handle parsing errors
    df = df.dropna(subset=['time_tag', 'Kp'])  # Drop rows with invalid datetime or Kp values
    df['Kp'] = pd.to_numeric(df['Kp'], errors='coerce')  # Convert Kp to numeric, coerce errors to NaN
    df = df.dropna(subset=['Kp'])  # Drop rows with invalid Kp values
    df = apply_color_mapping(df)
    return df

def preprocess_forecast_dataframe(df):
    df = pd.DataFrame(df, columns=["time_tag", "kp", "observed", "noaa_scale"])
    df = df.drop(0)  # Drop the header row if it exists
    df['time_tag'] = pd.to_datetime(df['time_tag'], format='%Y-%m-%d %H:%M:%S', errors='coerce')  # Handle parsing errors
    df = df.dropna(subset=['time_tag', 'kp'])  # Drop rows with invalid datetime or Kp values
    df['kp'] = pd.to_numeric(df['kp'], errors='coerce')  # Convert Kp to numeric, coerce errors to NaN
    df = df.dropna(subset=['kp'])  # Drop rows with invalid Kp values
    df = df[(df['observed'] == 'estimated') | (df['observed'] == 'predicted')]
    return df

# Function to map Kp values to colors
def map_color(kp_value):
    kp_value = math.ceil(kp_value)
    if kp_value < 5:
        return 'green'
    elif kp_value == 5:
        return 'yellow'
    elif kp_value == 6:
        return 'orange'
    elif kp_value == 7:
        return 'red'
    elif 8 <= kp_value <= 9:
        return 'darkred'
    else:
        return 'brown'

# Function to apply color mapping to the dataframe
def apply_color_mapping(df):
    df['color'] = df['Kp'].apply(map_color)
    return df

# Load datasets
kp_index_url = 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'
forecast_url = 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json'
kp_index_data = fetch_data(kp_index_url)
forecast_data = fetch_data(forecast_url)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Preprocess data
kp_df = preprocess_kp_dataframe(kp_index_data)
kp_forecast_df = preprocess_forecast_dataframe(forecast_data)

def create_layout(kp_df, kp_forecast_df):
    if (kp_df is not None) and (kp_forecast_df is not None):
        return dbc.Container([
            dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("", href="#")),
                dbc.NavItem(dbc.NavLink("", href="#")),
                dbc.DropdownMenu(
                nav=True,
                in_navbar=True,
                label="Menu",
                children=[
                    dbc.DropdownMenuItem("Entry 1"),
                    dbc.DropdownMenuItem("Entry 2"),
                    dbc.DropdownMenuItem(divider=True),
                    dbc.DropdownMenuItem("Entry 3"),
                ],
                ),
            ],
            brand=html.Div([
                html.Img(src="/assets/astro_dash_logo.png", height="30px"),
                html.Span("astrodash", style={"color": "#FFFFFF", "marginLeft": "10px"})
            ]),
            brand_href="#", 
            color="grey",
            ),
            dbc.Row([
            dbc.Col(html.H4(children='Kp-Index'), width=6),
            dbc.Col(
                dcc.DatePickerRange(
                id='date-picker-range',
                display_format='YYYY-MM-DD',
                className='date-picker-range',
                start_date_placeholder_text="Start Date",
                end_date_placeholder_text="End Date",
                initial_visible_month=kp_df['time_tag'].max(),
                min_date_allowed=kp_df['time_tag'].min(),
                max_date_allowed=kp_df['time_tag'].max(),
                start_date=kp_df['time_tag'].max() - pd.DateOffset(days=2),
                end_date=kp_df['time_tag'].max(),
                ),
                width=6
            )
            ]),
            dbc.Row([
            dbc.Col(dcc.Graph(
                id='graph-content', 
                config={'displayModeBar': False}), width=6),
            dbc.Col(daq.Gauge(
                size=280,
                color={"gradient": True, "ranges": {"green": [0, 5], "yellow": [5, 8], "red": [8, 9]}},
                value=kp_df['Kp'].iloc[-1],
                label='KP-index',
                scale={'start': 1, 'interval': 1, 'labelInterval': 1},
                units='Kp',
                max=9,
                min=0,
                id='gauge',
                showCurrentValue=True
            ), width=6,
                align='center',
                style={"display": "flex", "justify-content": "center"}),
            ]),
            dbc.Row([
            dbc.Col(html.H4("Kp Index Forecast"), width=12)
            ]),
            dbc.Row([
            dbc.Col(dash_table.DataTable(
                data=kp_forecast_df.to_dict('records'),
                page_size=10,
                style_table={'height': 'auto', 'overflowY': 'auto'},
                style_cell={'textAlign': 'center'},
                style_header={'fontWeight': 'bold'},
                style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'},
                                        {'if': {'column_id': 'kp', 'filter_query': '{kp} >= 0 && {kp} < 5'}, 'backgroundColor': 'green'},
                                        {'if': {'column_id': 'kp', 'filter_query': '{kp} >= 5 && {kp} < 6'}, 'backgroundColor': 'yellow'},
                                        {'if': {'column_id': 'kp', 'filter_query': '{kp} >= 6 && {kp} < 7'}, 'backgroundColor': 'orange'},
                                        {'if': {'column_id': 'kp', 'filter_query': '{kp} >= 7 && {kp} < 8'}, 'backgroundColor': 'red'},
                                        {'if': {'column_id': 'kp', 'filter_query': '{kp} >= 8 && {kp} <= 9'}, 'backgroundColor': 'darkred'},],
            ), width=12),
            ]),
        ])
    else:
        return dbc.Container([
            dbc.Alert(
                "Failed to load data. Please check the data source or your internet connection.",
                color="danger",
                dismissable=True,
            )
        ])

# Set the layout of the app
app.layout = create_layout(kp_df, kp_forecast_df)

def convert_to_datetime(date_str):
    """
    Convert a date string to pandas datetime.
    """
    try:
        return pd.to_datetime(date_str)
    except Exception as e:
        print(f"Error parsing date {date_str}: {e}")
        return None

def filter_dataframe(df, start_date, end_date):
    """
    Filter the DataFrame based on the date range.
    """
    return df[(df['time_tag'] >= start_date) & (df['time_tag'] <= end_date)]

def get_tick_values_and_labels(filtered_df):
    """
    Generate tick values and labels for the x-axis.
    """
    tickvals = filtered_df['time_tag'].tolist()
    ticktext = [time.strftime('%H:%M %d %b') if time.hour == 0 else time.strftime('%H:%M') for time in filtered_df['time_tag']]
    return tickvals, ticktext

def create_figure(filtered_df):
    """
    Create the Plotly figure for the graph.
    """
    color_mapping = {
        'green': 'green',
        'yellow': 'yellow',
        'orange': 'orange',
        'red': 'red',
        'darkred': 'darkred',
        'brown': 'brown'
    }

    fig = px.bar(filtered_df, x='time_tag', y='Kp', color='color', color_discrete_map=color_mapping)
    tickvals, ticktext = get_tick_values_and_labels(filtered_df)
    
    fig.update_layout(
        xaxis_title='Universal Time',
        yaxis_title='Kp Index',
        yaxis=dict(range=[0, 9]),  # Set y-axis range to 0-9
        xaxis=dict(tickmode='array', tickvals=tickvals, ticktext=ticktext),
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig

# Define the callback to update the graph
@app.callback(
    Output('graph-content', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_graph(start_date, end_date):
    """
    Update the graph based on the selected date range.
    
    Parameters:
    start_date (str): The start date from the date picker.
    end_date (str): The end date from the date picker.
    
    Returns:
    plotly.graph_objs._figure.Figure: The updated figure.
    """
    start_date = convert_to_datetime(start_date)
    end_date = convert_to_datetime(end_date)
    
    if start_date is None or end_date is None:
        return {}  # Return an empty figure if dates are invalid

    filtered_df = filter_dataframe(kp_df, start_date, end_date)
    return create_figure(filtered_df)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
