from dash import Dash, html, dcc, Input, Output, callback
import plotly.express as px
import pandas as pd
import requests
import math

# Function to fetch data and handle errors
def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Load dataset
data_url = 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'
data = fetch_data(data_url)

if data is not None:
    df = pd.DataFrame(data, columns=["time_tag", "Kp", "a_running", "station_count"])
    df = df.drop(0)  # Drop the header row if it exists
    df['time_tag'] = pd.to_datetime(df['time_tag'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')  # Handle parsing errors

    # Preprocess data to handle missing or invalid values
    df = df.dropna(subset=['time_tag', 'Kp'])  # Drop rows with invalid datetime or Kp values
    df['Kp'] = pd.to_numeric(df['Kp'], errors='coerce')  # Convert Kp to numeric, coerce errors to NaN
    df = df.dropna(subset=['Kp'])  # Drop rows with invalid Kp values

    # Define color mapping for Kp value ranges
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

    # Apply the color mapping to the dataframe
    df['color'] = df['Kp'].apply(map_color)

    # Create the Dash app
    app = Dash(__name__)

    # Define the layout of the app
    app.layout = html.Div([
        html.H1(children='AuroraDash', style={'textAlign': 'center'}),
        dcc.DatePickerRange(
            id='date-picker-range',
            start_date=df['time_tag'].min(),
            end_date=df['time_tag'].max(),
            display_format='YYYY-MM-DD HH:mm:ss'
        ),
        dcc.Graph(id='graph-content')
    ])

    # Define the callback to update the graph
    @callback(
        Output('graph-content', 'figure'),
        Input('date-picker-range', 'start_date'),
        Input('date-picker-range', 'end_date')
    )
    def update_graph(start_date, end_date):
        # Filter dataframe based on selected date range
        mask = (df['time_tag'] >= start_date) & (df['time_tag'] <= end_date)
        filtered_df = df.loc[mask]

        fig = px.bar(filtered_df, x='time_tag', y='Kp', title='NOAA Planetary K-index', color='color',
                     color_discrete_map={
                         'green': 'green',
                         'yellow': 'yellow',
                         'orange': 'orange',
                         'red': 'red',
                         'darkred': 'darkred',
                         'brown': 'brown'
                     })
        fig.update_layout(
            xaxis_title='Universal Time', 
            yaxis_title='Kp Index',
            yaxis=dict(range=[0, 9])  # Set y-axis range to 0-9
        )
        return fig

    # Run the app
    if __name__ == '__main__':
        app.run_server(debug=True, host='0.0.0.0')
else:
    print("Failed to load data. Please check the data source or your internet connection.")
