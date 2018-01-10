'''
Interactive dashboard to show characteristics of a classification model
for emails. Will display what emails were successfully categorized and which
weren't and which terms are most important for classifier.
'''

#----------------------------------------------------------------------#
# Libraries and dependencies                                           #
#----------------------------------------------------------------------#
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
from email_utils import highlightTerms, formatEmail
from email_utils import generateAccuracyTable,generateTruthTable
from email_utils import countTokens, countFreqs
import nltk
from nltk.corpus import stopwords


#------------------------------------------------------#
# Prepare input data                                   #
#Load results from classifier notebook
#------------------------------------------------------#
with open('../classify/totalTermCounts.pyc', 'rb') as f:
    totalTermCounts = pickle.load(f)
f.close()
with open('../classify/informativeTerms.pyc', 'rb') as f:
    informativeTerms = pickle.load(f)
f.close()
with open('../classify/classifierStats.pyc', 'rb') as f:
    classifierStats = pickle.load(f)
f.close()
with open('../classify/classifierTestResults.pyc', 'rb') as f:
    classifierTestResults = pickle.load(f)
f.close()
with open('../classify/feature_counts_training.pyc', 'rb') as f:
    feature_counts_training = pickle.load(f)
f.close()
with open('../classify/feature_counts_test.pyc', 'rb') as f:
    feature_counts_test = pickle.load(f)
f.close()
    
#-------------------------------------------------------------------------#
# Make 4 chunks of the test data, depending on truth value                #
#-------------------------------------------------------------------------#
resultsDF_tp = classifierTestResults[classifierTestResults['truthValue'] == 'truePositive']
resultsDF_fp = classifierTestResults[classifierTestResults['truthValue'] == 'falsePositive']
resultsDF_tn = classifierTestResults[classifierTestResults['truthValue'] == 'trueNegative']
resultsDF_fn = classifierTestResults[classifierTestResults['truthValue'] == 'falseNegative']


responseTypes = ['truePositive', 'trueNegative', 'falsePositive', 'falseNegative']

#-------------------------------------------------------------------#
# Store top 10 terms in list for easy access                        #
#-------------------------------------------------------------------#
visibleTermsList = list(informativeTerms['feature'].iloc[0:10])
numEmailsInSelectedDF = resultsDF_tp.shape[0]
emailPointer = 1

#Highlight the terms in the email which are in the visible list
highlightedEmailSubject = highlightTerms(resultsDF_tp.iloc[(emailPointer - 1)].subject, visibleTermsList)
highlightedEmailBody = highlightTerms(resultsDF_tp.iloc[(emailPointer - 1)].body, visibleTermsList)
subjectPlusBody = (resultsDF_tp.iloc[(emailPointer -1)].subject + " " + resultsDF_tp.iloc[(emailPointer - 1)].body)
currentTextTokenLength = countTokens(subjectPlusBody)
currentTextTermFreqs = countFreqs(visibleTermsList, subjectPlusBody)

#----------------------------------------------------------------------------#
#Local version of stylesheet from https://codepen.io/chriddyp/pen/bWLwgP.css #
#----------------------------------------------------------------------------#
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
                                      generateAccuracyTable(classifierStats)
                                      ],
                                  className = "six columns"
                                  ),
                              html.Div(
                                  id = "truth_table_div",
                                  children = generateTruthTable(classifierStats),
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
                options = [{'label': "{}s".format(responseType), 'value': responseType } for responseType in responseTypes ],
                value = 'truePositive',
                labelStyle={'display': 'inline-block'}
            )
        ]),
        html.Table(
            html.Tr(children=[
                html.Td(children = html.Button(id='buttonPrevious', children='<<Previous<<')),
                html.Td(id="emailNumberText", children = "Showing email #{} of {}".format(emailPointer, numEmailsInSelectedDF)),
                html.Td(children = html.Button(id='buttonNext', children='>>Next>>'))
            ])
        ),
        html.Div(id="text_div", children=[
            html.Iframe(
                id = 'email_text_iframe',
                sandbox='',
                srcDoc = formatEmail(highlightedEmailSubject,
                                     highlightedEmailBody),
                style = {'width': '450px', 'height': '250px'}
                )
        ], style= {'height':'200px'})
        ]),
        html.Div(id="graph_div", className = "six columns", children=[
            dcc.Graph(
                id='bar-chart',
                figure={
                    'data': [
                        go.Bar(
                            x = [(feature_counts_training[term]/totalTermCounts['trainTokensTotal'] * 1000)
                                 for term in visibleTermsList],
                            y = visibleTermsList,
                            name = 'Training Corpus',
                            orientation = 'h',
                            width = .2
                        ),
                        go.Bar(
                            x = [(feature_counts_test[term]/totalTermCounts['testTokensTotal'] * 1000)
                                 for term in visibleTermsList],
                            y = visibleTermsList,
                            name = 'Test Corpus',
                            orientation = 'h',
                            width = .2
                        ),
                        go.Bar(
                            x = [(currentTextTermFreqs[term]/currentTextTokenLength * 1000) for term in visibleTermsList],
                            y = visibleTermsList,
                            name = 'This Email',
                            orientation = 'h',
                            width = .2
                        )
                    ],
                    'layout': go.Layout(
                        xaxis= {'title': 'Occurrences per 1000 word tokens', 'autorange': True},
                        yaxis= {'type': 'category', 'autorange': True},
                        width=500,
                        height=500,
                        title='Most Informative Terms',
                        barmode='group'
                    )
                }
            )
        ], style={'height': '800px'}) #Text_div
    ], className = "row")
])


#-------------------------------------------------------------------#
# Define interactive behaviors from inputs                          #
#-------------------------------------------------------------------#

#-------------------------------------------------------------------#
# 2 callbacks for radio button to select email subset
#-------------------------------------------------------------------#
@app.callback(Output('emailNumberText', 'children'),
              [Input('showMe', 'value')])
def update_df_selection(input1):
    global resultsDF_tp
    global resultsDF_tn
    global resultsDF_fn
    global resultsDF_fp
    
    if input1 == 'truePositive':
        selectedDF = resultsDF_tp
    elif input1 == 'falsePositive':
        selectedDF = resultsDF_fp
    elif input1 == 'falseNegative':
        selectedDF = resultsDF_fn
    elif input1 == 'trueNegative':
        selectedDF = resultsDF_tn
        
    return ("Showing email #{} of {}".format(1, selectedDF.shape[0]))
@app.callback(Output('email_text_iframe', 'srcDoc'),
              [Input('showMe', 'value')])
def update_displayed_email_text(input1):
    global resultsDF_tp
    global resultsDF_tn
    global resultsDF_fn
    global resultsDF_fp
    global emailPointer
    
    if input1 == 'truePositive':
        selectedDF = resultsDF_tp
    elif input1 == 'falsePositive':
        selectedDF = resultsDF_fp
    elif input1 == 'falseNegative':
        selectedDF = resultsDF_fn
    elif input1 == 'trueNegative':
        selectedDF = resultsDF_tn
        
    highlightedEmailSubject = highlightTerms(selectedDF.iloc[(emailPointer - 1)].subject, visibleTermsList)
    highlightedEmailBody = highlightTerms(selectedDF.iloc[(emailPointer - 1)].body, visibleTermsList)
    return(formatEmail(highlightedEmailSubject, highlightedEmailBody))
           
if __name__ == '__main__':
    app.run_server(debug=True)

    
