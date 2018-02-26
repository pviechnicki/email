'''Utility functions for email category viewer'''
import plotly.graph_objs as go
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import WhitespaceTokenizer
# Tip of the hat to this page https://stackoverflow.com/questions/31668493/get-indices-of-original-text-from-nltk-word-tokenize
import dash
import dash_html_components as html


#----------------------------------------------------------------------#
# Globals                                                              #
#----------------------------------------------------------------------#
snowballStemmer = SnowballStemmer("english", ignore_stopwords=True)
myTokenizer = WhitespaceTokenizer()


#-------------------------------------------------------------------------#
# Count number of tokens in text string when current tokenizer is applied
#-------------------------------------------------------------------------#
def countTokens(myText):
    global myTokenizer
    tokens = myTokenizer.tokenize(myText)
    #Don't count punctuation-only tokens
    return len([elem for elem in map(stripPunctuation, tokens) if len(elem) > 0])

#----------------------------------------------------------------------#
# Return dict of counts of terms in list in text string
#----------------------------------------------------------------------#
def countFreqs(myTermsList, myText):
    global myTokenizer
    global snowballStemmer
    result = dict()
    for term in myTermsList:
        result[term] = 0
    tokens = myTokenizer.tokenize(stripPunctuation(preprocess(myText)))
    stemmedTokens = map(snowballStemmer.stem, tokens)
    for token in stemmedTokens:
        if token in myTermsList:
            result[token] += 1
    return result

#----------------------------------------------------------------------#
# Format an email subject and body as a raw html string                #
#----------------------------------------------------------------------#
def formatEmail(mySubject, myBody):
    return ("<h3>" + mySubject + "</h3><hr>" + myBody)

#------------------------------------------------#
# Return rows and cells of classifier accuracy   #
#------------------------------------------------#
def generateAccuracyTable(myStats):
    '''Returns 2-row table with labels in column 1, accuracy, error rate'''
    return html.Table([
        html.Tr([
            html.Th(
                id='accuracyTableCell1',
                children = "Accuracy",
                className = 'highlightedCell'
            ),
            html.Td(
                id = 'accuracyTableCell2',
                children = "{:.1%}".format(myStats['accuracy']),
                className = 'highlightedCell'
            )
        ]),
        html.Tr([
            html.Th(
                id = 'errorTableCell1',
                children = "Error Rate",
                className = 'normalCell'
            ),
            html.Td(
                id = 'errorTableCell2',
                children = "{:.1%}".format(myStats['errorRate']),
                className = 'normalCell'
            )
        ])
    ])
#--------------------------------------------------#
# Return rows and cells for classifier truth table #
#--------------------------------------------------#
def generateTruthTable(myStats):
    return html.Table([
        html.Tr([
            html.Th(),
            html.Th(),
            html.Th("Ground Truth Value", style={'colspan': '2'})
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
            html.Td(
                id = 'truePositivesCell',
                children = myStats['truePositive'],
                className = 'highlightedCell'
            ),
            html.Td(
                id = 'falsePositivesCell',
                children = myStats['falsePositive'],
                className = 'normalCell'
            )
        ]),
        html.Tr([
            html.Th(),
            html.Th("Not Personal"),
            html.Td(
                id = 'falseNegativesCell',
                children = myStats['falseNegative'],
                className = 'normalCell'
            ),
            html.Td(
                id = 'trueNegativesCell',
                children = myStats['trueNegative'],
                className = 'normalCell'
            )
        ])
    ])

#-------------------------------------------------------------------------#
# Using same stemmer and preprocessor definition as used in NB classifier #
#-------------------------------------------------------------------------#
def stripPunctuation(text):
    return (text.translate({ord(c):'' for c in string.punctuation}))

def preprocess(text):
    lower_text = ''
    if (type(text)== str):
        lower_text = text.lower()
    return lower_text

def myTokenize(text):
    global snowballStemmer
    global myTokenizer
    
    tokens = []
    filtered = []
    stemmed = []
    
    cleaned = preprocess(text)

    #Generate a list of tokens and also the spans from the preprocessed text
    rawTokens = myTokenizer.tokenize(cleaned)
    span_generator = myTokenizer.span_tokenize(cleaned)
    rawSpans = [span for span in span_generator]

    cleanedTokens = []
    cleanedSpans = []
    for i in range(0,len(rawTokens)):
        #Strip out punctuation from tokens
        cleanToken = stripPunctuation(rawTokens[i])
        #Discard tokens which only contained punctuation
        if (len(cleanToken) > 0):
            cleanedTokens.append(cleanToken)
            cleanedSpans.append(rawSpans[i])

    tokens_with_spans = zip(cleanedTokens, cleanedSpans)

    #Remove stop words
    filtered = [(w,s) for (w,s) in tokens_with_spans if not w in stopwords.words('english')]

    #Stem each token

    stemmedTerms = [snowballStemmer.stem(item[0]) for item in filtered]
    spans = [item[1] for item in filtered]
    stemmed = list(zip(stemmedTerms, spans))
    return stemmed

#------------------------------------------------#
#Wrap string with span tags and class info       #
#------------------------------------------------#
def wrapSpan(string):
    return("<span class=\"highlightme\" style=\"background-color: #2ca02c\">" + string + "</span>")

#------------------------------------------------#
# Highlight all terms in string matching list
# wrap with span tags and highlight class 
# lifting methods from here https://stackoverflow.com/questions/34956423/python-tkinter-change-text-background-of-some-textual-spans?rq=1
#------------------------------------------------#
def highlightTerms(textString, termsList):
    '''
    Highlight all terms in input string matching list of terms in 2nd arg
    '''

    rawText = textString
    highlightedText = [] #empty for now
    
    inputTerms_with_spans = myTokenize(rawText)
    currentOffset = 0
    
    for (term, span) in inputTerms_with_spans:
        if (term in termsList):
            start = span[0]
            end = span[1]
            highlightedText += rawText[currentOffset:start]
            highlightedText += list("<span style=\"background-color: #2ca02c\">")
            highlightedText += rawText[start:end]
            highlightedText += list("</span>")
            currentOffset = (end)

    highlightedText += rawText[currentOffset:]
        
    return(''.join(highlightedText))

#------------------------------------------------#
# Divide, but check if divisor is 0 first        #
#------------------------------------------------#
def safe_divide(numerator, denominator):
    '''Divide but check if denominator is zero first'''
    if (denominator != 0):
        return(numerator/denominator)
    else:
        return 0

#------------------------------------------------#
# Fill up multilevel dict with zeros             #
#------------------------------------------------#
def initialize_hour_tallies(myDict, labels, orgs, hours):
    '''Fill up multilevel dict with zeros'''
    for cat in labels:
        for org in orgs:
            for hour in hours:
                myDict[cat][org][hour] = 0
                myDict[cat]['All'][hour] = 0
                myDict['All']['All'][hour] = 0

#----------------------------------------------#
# update the values in the hourly usage chart
# depending on what org is selected
#----------------------------------------------#
def update_bar_data(new_value, hour_tallies):
    '''
    update the values in the hourly usage chart
    depending on what org is selected
    '''
    personal_list = []
    for i in range(1,13):
        personal_list.append(safe_divide(
            hour_tallies['personal'][new_value][i],
            hour_tallies['All'][new_value][i]))

    transient_list = []
    for i in range(1,13):
        transient_list.append(safe_divide(
            hour_tallies['transient'][new_value][i],
            hour_tallies['All'][new_value][i]))
    official_list = []
    for i in range(1,13):
        official_list.append(safe_divide(
            hour_tallies['official'][new_value][i],
            hour_tallies['All'][new_value][i]))

    return {
        'data': [
            go.Bar(
                x=list(range(1,13)),
                y=personal_list,
                name='Personal',
                marker={'color': '#2ca02c'}
            ),
            go.Bar(
                x=list(range(1,13)),
                y=transient_list,
                name='Transient',
                marker={'color': '#ff7f0e'}
            ),
            go.Bar(
                x=list(range(1,13)),
                y=official_list,
                name='Official',
                marker={'color': '#1f77b4'}
            ),
            
        ],
        'layout': go.Layout(
            xaxis={'title': 'Hour'},
            yaxis={'title': 'Proportion'}
        )
    }

