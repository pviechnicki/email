''' Interactive dashboard to show email category usage by division
Thanks to https://community.plot.ly/t/two-graphs-side-by-side/5312/2
for side-by-side css.
Thanks to 
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

#read in csv
raw_df = pd.read_csv('../data/email_cats.csv', header=0)

#Prepare two cross-tabs to support the pie and bar charts
ct_orgs = pd.crosstab(raw_df.cat, raw_df.org, margins=True)

#list of categories
my_cat_labels = (ct_orgs.index.values.tolist())[:-1]
my_orgs = ct_orgs.columns.tolist()
my_cat_values = defaultdict(list)
for i in range(0,len(my_orgs)):
    my_cat_values[my_orgs[i]] = (ct_orgs.iloc[:, i].tolist())[:-1]

#Count emails by category, org, and hour, store in multilevel defaultdict

hour_tallies = defaultdict( lambda: defaultdict(lambda: defaultdict( int )))
for cat in my_cat_labels:
    for org in my_orgs:
        for hour in range(1,13):
            hour_tallies[cat][org][hour] = 0

#Now fill up with actual numbers
for index, row in raw_df.iterrows():
    hour_tallies[row['cat']][row['org']][row['hour']] += 1
    hour_tallies[row['cat']]['All'][row['hour']] += 1
    

#Make pie chart
app = dash.Dash()

app.layout = html.Div(children = [
    html.H1(children = 'Email Marking Usage by Division'),
    html.Div(id = "row-div", children =[
        html.Div(id='chart_div', children =[
            html.H2(children="Overall Proportion of Email Types"),

            dcc.Graph(
                id='pie-graph',
                figure ={
                    'data': [
                        go.Pie(
                            labels = my_cat_labels,
                            values = my_cat_values['All'],
                            name='Series 1'
                        )
                    ],
                    'layout':
                    go.Layout(
                    )
                }
            )], className = "six columns"),
        html.Div(id='chart_div2', children = [
            html.H2('Hourly Type Usage'),
            dcc.Graph(
                id='bar-chart',
                figure={
                    'data': [
                        go.Bar(
                            x=list(range(1,13)),
                            y=list(hour_tallies['personal']['All'].values()),
                            name='Personal'
                        ),
                        go.Bar(
                            x = list(range(1,13)),
                            y = list(hour_tallies['transient']['All'].values()),
                            name='Transient'
                            ),
                        go.Bar(
                            x = list(range(1,13)),
                            y=list(hour_tallies['official']['All'].values()),
                            name='Official'
                            )
                    ],
                    'layout': go.Layout()
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
    ])
])


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
    return {
        'data': [
            go.Bar(
                x=list(range(1,13)),
                y=list(hour_tallies['personal'][input_value].values()),
                name='Personal'
            ),
            go.Bar(
                x = list(range(1,13)),
                y = list(hour_tallies['transient'][input_value].values()),
                name='Transient'
            ),
            go.Bar(
                x = list(range(1,13)),
                y=list(hour_tallies['official'][input_value].values()),
                name='Official'
            )
        ],
        'layout': go.Layout()
    }

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

if __name__ == '__main__':
    app.run_server(debug=True)


