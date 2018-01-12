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
from dash.dependencies import Input, Output, State
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

#---------------------------------------------------#
# Return name of dataframe based on input parameter #
#---------------------------------------------------#
def chooseDF(responseClass):

    if responseClass == 'truePositive':
        return (resultsDF_tp)
    elif responseClass == 'falsePositive':
        return (resultsDF_fp)
    elif responseClass == 'falseNegative':
        return (resultsDF_fn)
    elif responseClass == 'trueNegative':
        return (resultsDF_tn)
    else:
        return Null

#------------------------------------------------------------#
# Update the bar chart based on the current email            #
#------------------------------------------------------------#
def updateBarChartData(currentEmail):
    global feature_counts_training
    global feature_counts_test
    global visibleTermsList

    currentTextTokenLength = countTokens(currentEmail)
    currentTextTermFreqs = countFreqs(visibleTermsList, currentEmail)

    myFigure = {
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
            xaxis= {
                'title': 'Occurrences per 1000 word tokens',
                'autorange': True
            },
            yaxis= {
                'type': 'category',
                'autorange': True,
                'ticksuffix': '  ',
                'categoryorder': 'category descending'},
            width=500,
            height=500,
            title='Most Informative Terms',
            barmode='group'
        )
    }
    
    return(myFigure)

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
selectedDF = resultsDF_tp
numEmailsInSelectedDF = selectedDF.shape[0]
emailPointer = 1

#Highlight the terms in the email which are in the visible list
highlightedEmailSubject = highlightTerms(resultsDF_tp.iloc[(emailPointer - 1)].subject, visibleTermsList)
highlightedEmailBody = highlightTerms(resultsDF_tp.iloc[(emailPointer - 1)].body, visibleTermsList)
subjectPlusBody = (resultsDF_tp.iloc[(emailPointer -1)].subject + " " + resultsDF_tp.iloc[(emailPointer - 1)].body)
initialTextTokenLength = countTokens(subjectPlusBody)
initialTextTermFreqs = countFreqs(visibleTermsList, subjectPlusBody)

#----------------------------------------------------------------------------#
#Local version of stylesheet from https://codepen.io/chriddyp/pen/bWLwgP.css #
#----------------------------------------------------------------------------#
stylesheets = ['bWLwgP.css']

#--------------------------------------------#    
# Start building the dashboard - initialize  #
#--------------------------------------------#    
app = dash.Dash()
app.title = "Explore Email Classifier Performance"

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
             ]), #classifier_stats_div
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
            html.Table(id = 'tableJumpTo', children = [
                html.Tr(children = [
                    html.Td(html.Label("Jump to Email No.")),
                    html.Td(dcc.Input(id='inputEmailNumber', value = 1, type='number')), #Returns unicode string even though we request a number!
                    html.Td(html.P(id = 'pTotalEmails', children = " of {}".format(numEmailsInSelectedDF))),
                    html.Td(html.Button(id='buttonSubmit', children="Submit")),
                ]) #tr
            ]), #tableJumpTo
            html.P("Display N terms/features:"),
            dcc.Slider(
                id = 'sliderVisibleTerms',
                min = 3,
                max = 30,
                value = 10,
                step = None,
                marks = {str(num): str(num) for num in range(1,30)}
            ),
            html.Div(id="text_div", children=[
                html.Iframe(
                    id = 'email_text_iframe',
                    sandbox='',
                    srcDoc = formatEmail(highlightedEmailSubject,
                                         highlightedEmailBody),
                    style = {'width': '550px', 'height': '200px'}
                )
            ], style= {'height':'200px', 'padding-top': '20px'})
        ]), #holder div
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
                        x = [(initialTextTermFreqs[term]/initialTextTokenLength * 1000) for term in visibleTermsList],
                        y = visibleTermsList,
                        name = 'This Email',
                        orientation = 'h',
                        width = .2
                    )
                ],
                'layout': go.Layout(
                    xaxis= {
                        'title': 'Occurrences per 1000 word tokens',
                        'autorange': True},
                    yaxis= {
                        'type': 'category',
                        'autorange': True,
                        'ticksuffix': '  ',
                        'categoryorder': 'category descending'},
                    width=500,
                    height=500,
                    title='Most Informative Terms',
                    barmode='group'
                )
            }
        )
    ], style={'height': '800px'}) #Text_div
], className = "row") #text_and_graph_div


#-------------------------------------------------------------------#
# Define interactive behaviors from inputs                          #
#-------------------------------------------------------------------#

#-------------------------------------------------------------------#
# callbacks for radio button to select email subset and number      #
#-------------------------------------------------------------------#
@app.callback(Output('pTotalEmails', 'children'),
              [Input('showMe', 'value')])
def update_df_selection(input1):
    global resultsDF_tp
    global resultsDF_tn
    global resultsDF_fn
    global resultsDF_fp
    global emailPointer
    
    selectedDF = chooseDF(input1)#

    #Reset to ist email
    emailPointer = 1
        
    return (" of {}".format(selectedDF.shape[0]))

#------------------------------------------------------------#
# Update the text in the iframe                              #
# depending on which class of data and number email selected #
#------------------------------------------------------------#
@app.callback(Output('email_text_iframe', 'srcDoc'),
              [Input('buttonSubmit', 'n_clicks')],
              [State('showMe', 'value'),
               State('inputEmailNumber', 'value'),
               State('sliderVisibleTerms', 'value')])
def update_displayed_email_text(nClicks, inputDF, inputEmailNumber, numTerms):
    print("Updating email text")
    global resultsDF_tp
    global resultsDF_tn
    global resultsDF_fn
    global resultsDF_fp
    global selectedDF
    global emailPointer
    global visibleTermsList
    global informativeTerms

    #Switch to selected type of emails, true positive, false pos, etc
    selectedDF = chooseDF(inputDF)

    #Refresh visible terms list to number set by slider
    visibleTermsList = list(informativeTerms['feature'].iloc[0:numTerms])

    if (int(inputEmailNumber) > selectedDF.shape[0]):
        emailPointer = 1
    else:
        emailPointer = int(inputEmailNumber)
    
    highlightedEmailSubject = highlightTerms(selectedDF.iloc[(emailPointer - 1)].subject, visibleTermsList)
    highlightedEmailBody = highlightTerms(selectedDF.iloc[(emailPointer - 1)].body, visibleTermsList)
    return(formatEmail(highlightedEmailSubject, highlightedEmailBody))

#---------------------------------------------------------#
# Refresh the bar chart values based on the current email #
#---------------------------------------------------------#
@app.callback(Output('bar-chart', 'figure'),
              [Input('buttonSubmit', 'n_clicks')],
              [State('showMe', 'value'),
               State('inputEmailNumber', 'value'),
               State('sliderVisibleTerms', 'value')])
def updateBarChart(n_clicks, chosenDF, myEmailNumber, numTerms):
    #I'm not actually using n_clicks
    print("Updating Bar Chart")
    global selectedDF
    global emailPointer
    global visibleTermsList
    global informativeTerms

    selectDF = chooseDF(chosenDF)
    emailPointer = int(myEmailNumber)

    #Update the list of visible terms to show in graph based on slider
    visibleTermsList = list(informativeTerms['feature'].iloc[0:numTerms])
    
    subjectPlusBody = (selectedDF.iloc[(emailPointer -1)].subject + " " + selectedDF.iloc[(emailPointer - 1)].body)
    newFigure = updateBarChartData(subjectPlusBody)
    return (newFigure)


if __name__ == '__main__':
    app.run_server(debug=True)

    
                
