'''Utility functions for email category viewer'''
import plotly.graph_objs as go
#------------------------------------------------#
# Divide, but check if divisor is 0 first        #
#------------------------------------------------#
def safe_divide(numerator, denominator):
    if (denominator != 0):
        return(numerator/denominator)
    else:
        return 0

#------------------------------------------------#
# Fill up multilevel dict with zeros             #
#------------------------------------------------#
def initialize_hour_tallies(myDict, labels, orgs, hours):
    for cat in labels:
        for org in orgs:
            for hour in hours:
                myDict[cat][org][hour] = 0
                myDict[cat]['All'][hour] = 0
                myDict['All']['All'][hour] = 0

#----------------------------------------------#
# Move this to utils file                      #
#----------------------------------------------#
def update_bar_data(new_value, hour_tallies):
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

