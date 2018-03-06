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
import getopt

#create dataframe
def usage():
    sys.stdout.write("Usage: python wrangle.py [-d|--directory= <top directory of the github repository where your directory yaml sits>] [-n|--number= <number of output emails requested>] [-h|?|--help]") 
    
try:
    opts, args = getopt.getopt(sys.argv[1:], "d:n:h?", ["--directory=", "--number=", "--help"])
except getopt.GetoptError as err:
    #Exit if can't parse args
    usage() 
    sys.exit(2)
for o, a in opts:
    if (o == '-h' or o == '-?'):
        usage()
        exit(0)
    elif o in ('-d', '--directory'):
        parent_path = a
        sys.path.insert(0, parent_path + '//' + 'utils')
        from load_directories import directory_loader
        input_directory, output_directory = directory_loader(parent_path)

email_df = pd.read_csv(output_directory + '//' + 'Master_df.csv')

geolocator = Nominatim()
country_df = email_df.groupby(['country', 'sensitivity','user_type'])['messageId'].count()
country_df = country_df.to_frame()
country_df.reset_index(inplace=True)
country_df['long'] = ''
country_df['lat'] = ''

for i, row in country_df.iterrows():
    country = geolocator.geocode(row['country'])
    country_df = country_df.set_value(i, 'long', country.longitude)
    country_df = country_df.set_value(i, 'lat', country.latitude)
print(country_df.head())

my_sensitivities = list(set(country_df['sensitivity']))
country_df['display_text'] = country_df['country'] + str(country_df['messageId'])

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
                                color = country_df['sensitivity'],
                            text = country_df['country']
                            	# color = country_df['sensitivity']
                            ) #data dict
                        ], #data
                    "layout": dict(
                        height = 500,
                        width = 1000,
                        geo = dict(
                            showland = True,
                            showcoastlines = True,
                            showocean = True,
                            showcountries = True,
                            oceancolor = 'rgb(240,248,255)',
                            landcolor = 'rgb(128,128,1281)',
                            countrycolor = "rgb(255, 255, 255)" ,
                            coastlinecolor = "rgb(255, 255, 255)",
                            projection = dict(
                                type = 'Mercator'
                                )
                            )
                        ) #layout dict
                    } #figure
            ) #dcc.graph
        ]
    ),
        html.Div(
        id = "bar",
        children =
        [
            dcc.Graph(
                id='myBar',
                figure={
                    "data": [
                        go.Bar(
                            x = list((country_df['messageId'])),
                            y = list(country_df['user_type']),
                            marker = go.Marker(
                                color = 'rgb(26,118,255)')

                                # color = country_df['sensitivity']
                            ) #data dict
                        ], #data
                    "layout": dict(
                        height = 500,
                        width = 1000,
                        ) #layout dict
                    } #figure
            ) #dcc.graph
        ]
    ),
    html.Div(id='dropdown_div', children= [
        html.H3("Select Sensitivity of Interest"),
        dcc.Dropdown
        (
            id='my_dropdown',
            options = [{'label': sensitivity, 'value': sensitivity} for sensitivity in my_sensitivities],
            value = 'All'
        )
    ]
    )
])

@app.callback(
    Output(component_id='myMap', component_property='figure'),
    [Input(component_id='my_dropdown', component_property='value')]
)


def update_map_data(new_value):
    filtered_df = country_df[country_df['sensitivity'] == new_value]
    return {
        "data": [
            dict(
                type = 'scattergeo',
                mode = 'markers',
                lat = filtered_df['lat'],
                lon = filtered_df['long'],
                marker = dict(
                    size = filtered_df['messageId']),
                text = filtered_df['country'],
                    # color = country_df['sensitivity']
                ) #data dict
            ], #data
        "layout": dict(
            height = 500,
            width = 1000,
            geo = dict(
                showland = True,
                showcoastlines = True,
                showocean = True,
                showcountries = True,
                oceancolor = 'rgb(240,248,255)',
                landcolor = 'rgb(128,128,128)',
                countrycolor = "rgb(255, 255, 255)" ,
                coastlinecolor = "rgb(255, 255, 255)",
                projection = dict(
                    type = 'Mercator'
                    )
                )
            ) #layout dict
        } #figure
@app.callback(
    Output(component_id='myBar', component_property='figure'),
    [Input(component_id='my_dropdown', component_property='value')]
)
def update_bar_data(new_value):
    filtered_df = country_df[country_df['sensitivity'] == new_value]

    return {"data": [
                go.Bar(
                    x = list(filtered_df['messageId']),
                    y = list(filtered_df['user_type']),
                    marker = go.Marker(
                        color = 'rgb(26,118,255)')

                        # color = country_df['sensitivity']
                    ) #data dict
                ], #data
            "layout": dict(
                height = 500,
                width = 1000,
                )
        }


if __name__ == '__main__':
    app.run_server(debug=True)