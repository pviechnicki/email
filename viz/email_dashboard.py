''' Interactive dashboard to show email category usage by division
Thanks to https://community.plot.ly/t/two-graphs-side-by-side/5312/2
for side-by-side css styles
https://stackoverflow.com/questions/17154393/multiple-levels-of-keys-and-values-in-python for how to use multilevel defaultdicts
'''

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import numpy as np
import pandas as pd
import csv
from collections import defaultdict
import sys
import os
from flask import send_from_directory
import getopt
import datetime as dt


#Local version of stylesheet from https://codepen.io/chriddyp/pen/bWLwgP.css
stylesheets = ['bWLwgP.css']

#read in data
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
        from viz_utils import safe_divide, initialize_hour_tallies
        from viz_utils import update_bar_data
        from email_utils import safe_divide, initialize_hour_tallies
        from email_utils import update_bar_data
        input_directory, output_directory = directory_loader(parent_path)

raw_df = pd.read_csv(output_directory + '//' + 'Master_df.csv')

#Prepare two cross-tabs to support the pie and bar charts
ct_orgs = pd.crosstab(raw_df.sensitivity, raw_df.org_unit, margins=True)

#list of categories
my_cat_labels = (ct_orgs.index.values.tolist())[:-1]
my_orgs = ct_orgs.columns.tolist()
my_cat_values = defaultdict(list)
for i in range(0,len(my_orgs)):
    my_cat_values[my_orgs[i]] = (ct_orgs.iloc[:, i].tolist())[:-1]

#Count emails by category, org, and hour, store in multilevel defaultdict
hour_tallies = defaultdict( lambda: defaultdict(lambda: defaultdict( int )))
initialize_hour_tallies(hour_tallies, my_cat_labels, my_orgs, range(1,25))
#Now fill up with actual numbers
for index, row in raw_df.iterrows():
    row['sent_date'] = dt.datetime.strptime(row['sent_date'], "%Y-%m-%dT%H:%M:%S")
    hour_tallies[row['sensitivity']][row['org_unit']][row['sent_date'].hour] += 1
    hour_tallies[row['sensitivity']]['All'][row['sent_date'].hour] += 1
    hour_tallies['All'][row['org_unit']][row['sent_date'].hour] += 1
    hour_tallies['All']['All'][row['sent_date'].hour] += 1

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
    html.H1(children = 'Email Marking Usage by Division'),
    html.Div(id = "row-div", children =[
        html.Div(id='chart_div', children =[
            html.H2(children="Overall Proportion of Email Types"),
            dcc.Graph(
                id='pie-graph',
                figure ={
                    'data': [
                        go.Pie(labels = my_cat_labels,
                               values = my_cat_values['All'],
                               name='Series 1')],
                    'layout':
                    go.Layout()
                }
            )], className = "six columns"),
        html.Div(id='chart_div2', children = [
            html.H2('Hourly Type Usage'),
            dcc.Graph(
                id='bar-chart',
                figure={
                    'data': [
                        go.Bar(
                            x = list(range(1,25)),
                            y = list(map(safe_divide,
                                         hour_tallies['Sensitivity Personal']['All'].values(),
                                         hour_tallies['All']['All'].values())),
                            name='Personal',
                            marker={'color': '#2ca02c'}
                        ),
                        # go.Bar(
                        #     x = list(range(1,13)),
                        #     y = list(map(safe_divide,
                        #                  hour_tallies['transient']['All'].values(),
                        #                  hour_tallies['All']['All'].values())),
                        #     name='Transient',
                        #     marker={'color':'#ff7f0e'}
                        # ),
                        go.Bar(
                            x=list(range(1,25)),
                            y = list(map(safe_divide,
                                         hour_tallies['Sensitivity Official']['All'].values(),
                                         hour_tallies['All']['All'].values())),
                            name='Official',
                            marker={'color': '#1f77b4'}
                        )
                    ],
                    'layout': go.Layout(
                        xaxis={'title': 'Hour'},
                        yaxis = {'title': 'Proportion'}
                    )
                }
            )], className = "six columns")
    ], className = "row"),
    html.Div(id='dropdown_div', children= [
        html.H3("Select Division of Interest"),
        dcc.Dropdown
        (
            id='my_dropdown',
            options = [{'label': org, 'value': org} for org in my_orgs],
            value = 'All'
        )
    ]
    )
])

#-------------------------------------------------------------------#
# Define interactive behaviors from dropdown                        #
#-------------------------------------------------------------------#
@app.callback(
    Output(component_id='pie-graph', component_property='figure'),
    [Input(component_id='my_dropdown', component_property='value')]
)
def update_pie(input_value):
    #Update the pie chart data based on the dropdown
    return {
        'data': [
            go.Pie(
                labels = my_cat_labels,
                values = my_cat_values.get(input_value),
                name='Series 1'
            )
        ],
        'layout':
        go.Layout(
        )
    }
@app.callback(
    Output(component_id='bar-chart', component_property='figure'),
    [Input(component_id='my_dropdown', component_property='value')]
)
def update_bar(input_value):
    #Update bar graph based on dropdown value
    return (update_bar_data(input_value, hour_tallies))


if __name__ == '__main__':
    app.run_server(debug=True)

    
