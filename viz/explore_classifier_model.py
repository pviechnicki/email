'''
Interactive dashboard to show characteristics of a classification model
for emails. Will display what emails were successfully categorized and which
weren't and which terms are most important for classifier.
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
import pickle

#------------------------------------------------------#
# Prepare input data                                   #
#------------------------------------------------------#
thisDocTFIDF = defaultdict(float)

thisDocTFIDF['red'] = .7
thisDocTFIDF['green'] = .5
thisDocTFIDF['blue'] = .2
thisDocTFIDF['orange'] = 0

with open('../dotce/informativeTerms.pyc', 'rb') as f:
    allDocsTFIDF = pickle.load(f)
f.close()
with open('../dotce/classifierStats.pyc', 'rb') as f:
    classifierStats = pickle.load(f)
f.close()
with open('../dotce/classifierTestResults.pyc', 'rb') as f:
    classiferTestResults = pickle.load(f)
    
myString = ('red ' * 40) + 'green ' + 'blue'

responseTypes = ['truePositive', 'trueNegative', 'falsePositive', 'falseNegative']

#------------------------------------------------#
# Return rows and cells of classifier accuracy   #
#------------------------------------------------#
def generateAccuracyTable():
    '''Returns 2-row table with labels in column 1, accuracy, error rate'''
    return html.Table([
        html.Tr([
            html.Th("Accuracy"),
            html.Td(classifierStats['accuracy'])
        ]),
        html.Tr([
            html.Th("Error Rate"),
            html.Td(classifierStats['errorRate'])
        ])
    ])
#--------------------------------------------------#
# Return rows and cells for classifier truth table #
#--------------------------------------------------#
def generateTruthTable():
    return html.Table([
        html.Tr([
            html.Th(),
            html.Th(),
            html.Th("True Value", style={'colspan': '2'})
        ]),
        html.Tr([
            html.Th(),
            html.Th(),
            html.Th("Personal"),
            html.Th("Not Personal")
        ]),
        html.Tr([
            html.Th(children="Classifier Assigned", style={'rowSpan': 2}),
            html.Th("Personal"),
            html.Td(classifierStats['truePositive']),
            html.Td(classifierStats['falsePositive'])
        ]),
        html.Tr([
            html.Th(),
            html.Th("Not Personal"),
            html.Td(classifierStats['falseNegative']),
            html.Td(classifierStats['trueNegative'])
        ])
    ])
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
    html.H1(children = "How Well is My Email Classifier Working?", style={'textAlign': 'center'}),
    html.Div(id="classifier_stats_div", children =
             [
                 html.Div(id="performanceDiv",
                          children = [
                              html.Div(
                                  id="accuracy_table_div",
                                  children = [
                                      html.H2("Overall Classifier Performance"),
                                      generateAccuracyTable()
                                      ],
                                  className = "six columns"
                                  ),
                              html.Div(
                                  id = "truth_table_div",
                                  children = generateTruthTable(),
                                  className = "six columns"
                                  )
                          ],
                          className="row")
             ]),
    html.Div(id="text_and_graph_div", children=[
        html.Div(id="holder_div", className = "six columns", children = [
        html.H2("Performance On Each Email"),
        html.Div(id="output_class_selector_div", children=[
            html.Label("Show me..."),
            dcc.RadioItems(
                id="showMe",
                options = [{'label': responseType, 'value': responseType } for responseType in responseTypes ],
                value = 'truePositive',
                labelStyle={'display': 'inline-block'}
            )
        ]),
        html.Table(
            html.Tr(children=[
                html.Td(children = html.Button(id='buttonPrevious', children='Previous')),
                html.Td(id="emailNumberText", children = "Showing email #1 of N"),
                html.Td(children = html.Button(id='buttonNext', children='Next'))
            ])
        ),
        html.Div(id="text_div", children=[
            html.H3(id="emailSubject", children="Subject Line"),
            html.P(myString)
        ], style={'overflow-y': 'scroll', 'height': '200px'})
        ]),
        html.Div(id="graph_div", className = "six columns", children=[
            dcc.Graph(
                id='bar-chart',
                figure={
                    'data': [
                        go.Bar(
                            x = [1, 2, 3],
                            y = ['term1', 'term2', 'term3'],
                            name = 'Within this email',
                            orientation = 'h',
                            width = .2
                        ),
                        go.Bar(
                            x = [1.5, .4, 2],
                            y = ['term1', 'term2', 'term3'],
                            name = 'All emails',
                            orientation = 'h',
                            width = .2
                        ),
                    ],
                    'layout': go.Layout(
                        xaxis= {'title': 'Term Weight (TF/IDF)', 'autorange': True},
                        yaxis= {'type': 'category', 'autorange': True},
                        width=400,
                        title='Most Informative Terms',
                        barmode='group',
                        bargap = 0.01,
                        bargroupgap=0,
                        autosize=True
                    )
                }
            )
        ])
    ], className = "row")
])


#-------------------------------------------------------------------#
# Define interactive behaviors from dropdown                        #
#-------------------------------------------------------------------#

if __name__ == '__main__':
    app.run_server(debug=True)

    
