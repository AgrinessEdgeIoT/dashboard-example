######################### IMPORTS #########################

import pandas                                # Data analysis tools for Python
import plotly.graph_objs as plotlygo         # Modern visualization for the data era
import plotly.offline as plotly
import pytz                                  # World timezone definitions for Python

from dateutil import tz                      # Powerful extensions to datetime
from portiapy import utils as portiapy_utils # A package for handling Agriness Edge’s REST API

######################### FUNCTIONS #########################

# Initializing plotly
plotly.offline.init_notebook_mode(connected=True)

def mapClientsToWidget(clientList):
    mapping = {}
    for client in clientList:
        mapping[client.name] = "{0}".format(client.id)
    return mapping

def mapFarmsToWidget(farmList):
    mapping = {}
    for farm in farmList:
        mapping[farm.name] = "{0}".format(farm.id) 
    return mapping

def mapSpotsToWidget(spotList):
    mapping = {}
    for spot in spotList:
        mapping[spot.label] = "{0}".format(spot.id)       
    return mapping

def mapDevicesToWidget(deviceList):
    mapping = {}
    for device in deviceList:
        mapping[device.edgeid] = "{0}".format(device.edgeid)       
    return mapping

def mapDimensionsToWidget(dimensionList):
    mapping = {}
    for d in dimensionList:
        dimensionKey = "/device/{1}/port/{2}/sensor/{3}/dimension/{4}      -      {0:30}   ".format( portiapy_utils.translateDimensionCode( "{0}".format(d.dimension) ), d.edgeid, d.port, d.sensor, d.dimension )
        
        dimensionValue = "{0}".format( str(d.__dict__).replace("<", "'").replace(">", "'") )
        
        mapping[dimensionKey] = dimensionValue
    return mapping

def plotSelectionsFromDataframes(dataFrames, timezone='Etc/GMT-3'):

    lines = []

    for i, dataFrame in enumerate(dataFrames):
        dataFrame['header_timestamp'] = pandas.to_datetime(dataFrame['header_timestamp'], unit='ms').dt.tz_localize(timezone)
        lines.append( plotlygo.Scatter( y=dataFrame.dimension_value, x=dataFrame.header_timestamp, mode = 'lines+markers', name = "Sensor {0}".format(i) ) )

    data   = plotlygo.Data(lines)
    layout = plotlygo.Layout(width=1100, height=650)
    plotly.iplot( plotlygo.Figure(data=data, layout=layout) )

def plotSummariesFromDataframes(dataFrames, timezone='Etc/GMT-3'):
   
    lines = []

    for dataFrame in dataFrames:
        dataFrame['header_timestamp'] = pandas.to_datetime(dataFrame['header_timestamp'], unit='ms').dt.tz_localize(timezone)

#         timeAxis = []
#         for i, line in enumerate(dataFrame['header_timestamp']):
#             timeAxis.append( dataFrame['header_timestamp'][i] )

        lines.append( plotlygo.Bar(y=dataFrame['number_of_packages'], x=dataFrame.header_timestamp, name = "Packages", opacity = 0.1 ) )
        if 'max' in dataFrame.columns:
            lines.append( plotlygo.Scatter(y=dataFrame['max'],    x=dataFrame.header_timestamp, mode = 'lines+markers', name = "Max",    yaxis = 'y2' ))
        if 'avg' in dataFrame.columns:
            lines.append( plotlygo.Scatter(y=dataFrame['avg'],    x=dataFrame.header_timestamp, mode = 'lines+markers', name = "Avg",    yaxis = 'y2' ))
        if 'min' in dataFrame.columns:
            lines.append( plotlygo.Scatter(y=dataFrame['min'],    x=dataFrame.header_timestamp, mode = 'lines+markers', name = "Min",    yaxis = 'y2' ))
        if 'median' in dataFrame.columns:
            lines.append( plotlygo.Scatter(y=dataFrame['median'], x=dataFrame.header_timestamp, mode = 'lines+markers', name = "Median", yaxis = 'y2' ))
        if 'mode' in dataFrame.columns:
            lines.append( plotlygo.Scatter(y=dataFrame['mode'],   x=dataFrame.header_timestamp, mode = 'lines+markers', name = "Mode",   yaxis = 'y2' ))
        if 'sum' in dataFrame.columns:
            lines.append( plotlygo.Scatter(y=dataFrame['sum'],    x=dataFrame.header_timestamp, mode = 'lines+markers', name = "Sum",    yaxis = 'y2', visible= 'legendonly') )
        if 'stddev' in dataFrame.columns:
            lines.append( plotlygo.Scatter(y=dataFrame['stddev'], x=dataFrame.header_timestamp, mode = 'lines+markers', name = "Stddev", yaxis = 'y2', visible= 'legendonly') )
        if 'spread' in dataFrame.columns:
            lines.append( plotlygo.Scatter(y=dataFrame['spread'], x=dataFrame.header_timestamp, mode = 'lines+markers', name = "Spread", yaxis = 'y2', visible= 'legendonly') )

    data = plotlygo.Data(lines)
    layout = plotlygo.Layout(width=1100, height=650, yaxis=dict(title='Number of Packages', side='right'), yaxis2=dict(title='Dimension Value', overlaying='y',side='left'))
    plotly.iplot( plotlygo.Figure(data=data, layout=layout) ) 
