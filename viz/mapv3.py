import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import numpy as np
import pandas as pd
import csv
import sys
import os
from flask import send_from_directory
import geopy
from geopy.geocoders import Nominatim

#create dataframe

email_df = pd.read_csv('C:/Users/embicks/Documents/DOTCE/email_marker/email/data/Output/Master_df.csv')

geolocator = Nominatim()
country_df = email_df.groupby(['country', 'sensitivity'])['messageId'].count()
country_df = country_df.to_frame()
country_df.reset_index(inplace=True)
country_df['long'] = ''
country_df['lat'] = ''

for i, row in country_df.iterrows():
    country = geolocator.geocode(row['country'])
    country_df = country_df.set_value(i, 'long', country.longitude)
    country_df = country_df.set_value(i, 'lat', country.latitude)
print(country_df.head())

#Local version of stylesheet from https://codepen.io/chriddyp/pen/bWLwgP.css
stylesheets = ['bWLwgP.css']


#--------------------------------------------#    
# Start building the dashboard - initialize  #
#--------------------------------------------#    
app = dash.Dash()

#--------------------------------------------#    
#Allow locally-served css
#--------------------------------------------#    
app.css.config.serve_locally=True
app.scripts.config.serve_locally=True

@app.server.route('/static/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'static')
    return send_from_directory(static_folder, path)

#-----------------------------------------------------#
# Layout dashboard with HTML and dash core components #
#-----------------------------------------------------#    
app.layout = html.Div(children = [
     html.Link(
        rel='stylesheet',
        href='/static/bWLwgP.css'
    ),
    html.H1(children = 'My Map'),
    html.Div(
        id = "mapDiv",
        children =
        [
            dcc.Graph(
                id='myMap',
                figure={
                    "data": [
                        dict(
                            type = 'scattergeo',
                            mode = 'markers',
                            lat = country_df['lat'],
                            lon = country_df['long'],
                            marker = dict(
                            	size = country_df['messageId']),
                            	# color = country_df['sensitivity']
                            ) #data dict
                        ], #data
                    "layout": dict(
                        autosize = True
                        ) #layout dict
                    } #figure
            ) #dcc.graph
        ]
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)

