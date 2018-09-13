######################### IMPORTS #########################

import ast                                       # Abstract syntax trees
import json                                      # JSON encoder and decoder
import pandas                                    # Python data analysis library
import random                                    # Generate pseudo-random numbers
import time                                      # Time access and conversions
import ipywidgets as widgets                     # Interactive HTML widgets

from modules  import utils
from datetime import date, timedelta, datetime   # Basic date and time types
from portiapy import utils as PortiaUtils        # A package for handling Agriness Edge’s REST API
from portiapy.portia import PortiaApi
from portiapy.summary import SummaryStrategies
from IPython.display import FileLink, Javascript # Interactive computing
from IPython.core.display import display, HTML

########################## UTILS ##########################

## Variables
toTimestamp   = int( time.time() ) * 1000                # ms
fromTimestamp = toTimestamp - (1000 * 60 * 60 * 24 * 10) # 10 days

portiaConfig = {
    'baseurl'       : 'http://edge-portia-api.sa-east-1.elasticbeanstalk.com/v3',
    'authorization' : None,
    'debug'         : False
}
portiaApi = PortiaApi(portiaConfig)

## Display header
display(HTML("""
    <!DOCTYPE html>
    <html>
        <head>
            <link href='https://fonts.googleapis.com/css?family=Audiowide' rel='stylesheet'>
        </head>
        <body>
            <div align="center" style=" font-family: 'Audiowide'"><h1><img width="40px" src="./resources/images/as-small.png"/>AgroSensor 3 Prototype - The Dashboard</h1> <hr>
        </body>
    </html>
"""))

## Functions
def getBlankspace(width=None):
    if width is None:
        return widgets.Label( description='' )
    else:
        return widgets.Label( description='', layout=widgets.Layout( width='{}%'.format(width) ) )

###########################################################

##################### DATABASE WIDGETS ####################

dropdown_clients = widgets.Dropdown( description='Client:  ', options=['...'], continuous_update=False, layout=widgets.Layout(width='33%') )
dropdown_farms   = widgets.Dropdown( description='Farms:   ', options=['...'], continuous_update=False, layout=widgets.Layout(width='33%') )
dropdown_spots   = widgets.Dropdown( description='Areas:   ', options=['...'], continuous_update=False, layout=widgets.Layout(width='33%') )
dropdown_devices = widgets.Dropdown( description='Devices: ', options=['...'], continuous_update=False, layout=widgets.Layout(width='33%') )

select_multiple_dimensions = widgets.SelectMultiple( description='Dimensions: ', rows=3, options=[], continuous_update=False, layout=widgets.Layout(width='66%') )

text_client_email      = widgets.Text( description='Email:       ', value='...', disabled=True, layout=widgets.Layout(width='33%') )
text_farm_description  = widgets.Text( description='Description: ', value='...', disabled=True, layout=widgets.Layout(width='33%') )
text_device_type       = widgets.Text( description='Device Type: ', value='...', disabled=True, layout=widgets.Layout(width='33%') )

# On update functions
def on_dropdown_clients_update(x):
    global dashDatabase
    
    if dropdown_clients.value is not None and dropdown_clients.value != '...':
        # Updating client info
        clientEmail = dashDatabase.getClient(dropdown_clients.value).email
        if clientEmail is not None:
            text_client_email.value = clientEmail
        
        # Updating farms
        farmList = dashDatabase.getClientFarms(dropdown_clients.value)
        dropdown_farms.options = utils.mapFarmsToWidget(farmList)
    else:
        text_client_email.value = '...'
        
        dropdown_farms.options = ['...']
        dropdown_farms.value = '...'

def on_dropdown_farms_update(x):
    global dashDatabase
    
    if dropdown_farms.value is not None and dropdown_farms.value != '...':
        # Updating farm info
        farmDescription = dashDatabase.getFarm(dropdown_farms.value).description
        if farmDescription is not None:
            text_farm_description.value = farmDescription
    
        # Updating spots
        spotList = dashDatabase.getFarmSpots(dropdown_farms.value)
        dropdown_spots.options = utils.mapSpotsToWidget(spotList)
        
        # Updating devices
        deviceList = dashDatabase.getFarmDevices(dropdown_farms.value)
        dropdown_devices.options = utils.mapDevicesToWidget(deviceList)
    else:
        text_farm_description.value = '...'
        
        dropdown_spots.options = ['...']
        dropdown_spots.value = '...'
        
        dropdown_devices.options = ['...']
        dropdown_devices.value = '...'

def on_dropdown_spots_update(x):
    global dashDatabase
    
    if dropdown_spots.value is not None and dropdown_spots.value != '...':
        # Updating dimensions
        dimensionList = dashDatabase.getSpotDimensions(dropdown_spots.value)
        select_multiple_dimensions.options = utils.mapDimensionsToWidget(dimensionList)
    else:
        select_multiple_dimensions.options = ['...']
        
def on_dropdown_devices_update(x):
    global dashDatabase
    
    if dropdown_devices.value is not None and dropdown_devices.value != '...':
        # Updating device type
        deviceThingCode = dashDatabase.getDevice(dropdown_devices.value, dropdown_clients.value).thing_code
        if deviceThingCode is not None:
            text_device_type.value = PortiaUtils.translateThingCode( int(deviceThingCode) )
            
        # Updating dimensions
        dimensionList = dashDatabase.getSpotDimensions(dropdown_spots.value)
        select_multiple_dimensions.options = utils.mapDimensionsToWidget(dimensionList)
    else:
        text_device_type.value = '...'

dropdown_clients.observe(on_dropdown_clients_update, names='value')
dropdown_farms  .observe(on_dropdown_farms_update,   names='value')
dropdown_spots  .observe(on_dropdown_spots_update,   names='value')
dropdown_devices.observe(on_dropdown_devices_update, names='value')

###########################################################

######################## DASHBOARD ########################

# Building dashboard header
tab_dashboard_header_hbox_1 = widgets.HBox([dropdown_clients, dropdown_farms, dropdown_spots])
tab_dashboard_header_hbox_2 = widgets.HBox([select_multiple_dimensions])
tab_dashboard_header_vbox   = widgets.VBox([tab_dashboard_header_hbox_1, tab_dashboard_header_hbox_2])

# label_dashboard_resume  = widgets.Label( description='Resum' ) # não remover
# label_dashboard_init    = widgets.Label( description='Init' )  # não remover

# Creating body widgets
tab_dashboard_body_date_picker_from = widgets.DatePicker( description='From: ', disabled=False, value=date.today() - timedelta(days=2) )
tab_dashboard_body_date_picker_to   = widgets.DatePicker( description='To: ',   disabled=False, value=date.today() )
tab_dashboard_body_int_slider_days  = widgets.IntSlider( description='Last Days', min=1, max=120, step=1, value=100, continuous_update=True )

# On update functions
def on_tab_dashboard_body_date_picker_from_update(x):
    tab_dashboard_body_int_slider_days.value = (tab_dashboard_body_date_picker_to.value - tab_dashboard_body_date_picker_from.value).days

def on_tab_dashboard_body_date_picker_to_update(x):
    tab_dashboard_body_int_slider_days.value = (tab_dashboard_body_date_picker_to.value - tab_dashboard_body_date_picker_from.value).days

def on_tab_dashboard_body_int_slider_days_update(x):
    tab_dashboard_body_date_picker_from.value = date.today() - timedelta(days=x)
    tab_dashboard_body_date_picker_to.value   = date.today()

# Configuring body widgets
tab_dashboard_body_interactive_days = widgets.interactive(on_tab_dashboard_body_int_slider_days_update,  x = tab_dashboard_body_int_slider_days)
tab_dashboard_body_interactive_from = widgets.interactive(on_tab_dashboard_body_date_picker_from_update, x = tab_dashboard_body_date_picker_from)
tab_dashboard_body_interactive_to   = widgets.interactive(on_tab_dashboard_body_date_picker_to_update,   x = tab_dashboard_body_date_picker_to)

# Building dashboard body
tab_dashboard_body_hbox_date_controls = widgets.HBox([tab_dashboard_body_interactive_from, getBlankspace(), tab_dashboard_body_interactive_to, getBlankspace(), tab_dashboard_body_interactive_days])

########################## SELECT #########################

# Creating select widgets
tab_dashboard_select_button_load_data = widgets.Button( description='Load Data' )
tab_dashboard_select_label_update     = widgets.Label( description='Init' )

# On click functions
def on_tab_dashboard_select_button_load_data_click(x):
    tab_dashboard_select_label_update.value = "Execution #{0}".format( random.randrange(10000) )

def executeSelection(x):
    dfs = []
    for item in select_multiple_dimensions.value:
        item = ast.literal_eval(item)
                                       
        fromTimestamp = datetime.combine( tab_dashboard_body_date_picker_from.value, datetime.min.time() ).timestamp() * 1000
        toTimestamp   = datetime.combine( tab_dashboard_body_date_picker_to.value,   datetime.min.time() ).timestamp() * 1000

        if portiaConfig['debug']:
            print( "Querying for the last {0} days ".format(tab_dashboard_body_int_slider_days.value) )

        try:
            df = portiaApi.device(item['edgeid']).port(item['port']).sensor(item['sensor']).dimension(item['dimension']).select(params={ 'from': int(fromTimestamp), 'to': int(toTimestamp), 'precision': 'ms' })
            dfs.append(df)
        except Exception as e: 
            print(e)
    utils.plotSelectionsFromDataframes(dfs)

# Configuring buttons
tab_dashboard_select_button_load_data.on_click(on_tab_dashboard_select_button_load_data_click)

# Configuring labels
tab_dashboard_select_interactive_update = widgets.interactive(executeSelection, x = tab_dashboard_select_label_update)

# Building tab select
tab_dashboard_select_hbox_widgets = widgets.HBox([tab_dashboard_select_button_load_data])
tab_dashboard_select_vbox         = widgets.VBox([tab_dashboard_body_hbox_date_controls, tab_dashboard_select_hbox_widgets, tab_dashboard_select_interactive_update])

######################### SUMMARY #########################

# Creating summary widgets
tab_dashboard_summary_int_slider_interval      = widgets.IntSlider( description='Interval:', min=1, max=100, step=1, value=1, continuous_update=True )
tab_dashboard_summary_dropdown_strategy        = widgets.Dropdown( description='Strategy:', orientation='horizontal', options=['perminute', 'perhour', 'perday', 'permonth', 'peryear'], value='perday', disabled=False )
tab_dashboard_summary_select_multiple_features = widgets.SelectMultiple( description='Features:', rows=3, options=['min', 'max', 'sum', 'avg', 'median', 'mode', 'stddev', 'spread'], disabled=False )

tab_dashboard_summary_button_load_data = widgets.Button( description='Load Data' )
tab_dashboard_summary_label_update     = widgets.Label( description='Init' )

# On click functions
def on_tab_dashboard_summary_button_load_data_click(x):
    tab_dashboard_summary_label_update.value = "Execution #{0}".format( random.randrange(10000) )
                                       
def executeSummary(x):
    dfs = []
    for item in select_multiple_dimensions.value:
        item = ast.literal_eval(item)
                                       
        fromTimestamp = datetime.combine( tab_dashboard_body_date_picker_from.value, datetime.min.time() ).timestamp() * 1000
        toTimestamp   = datetime.combine( tab_dashboard_body_date_picker_to.value,   datetime.min.time() ).timestamp() * 1000
                                       
        if portiaConfig['debug']:
            print( "Querying for the last {0} days ".format(tab_dashboard_body_int_slider_days.value))
                                       
        try:
            
            # Verifying strategy
            strategy = None
            if tab_dashboard_summary_dropdown_strategy.value   == 'perminute':
                strategy = SummaryStrategies.PER_MINUTE
            elif tab_dashboard_summary_dropdown_strategy.value == 'perhour':
                strategy = SummaryStrategies.PER_HOUR
            elif tab_dashboard_summary_dropdown_strategy.value == 'perday':
                strategy = SummaryStrategies.PER_DAY
            elif tab_dashboard_summary_dropdown_strategy.value == 'permonth':
                strategy = SummaryStrategies.PER_MONTH
            elif tab_dashboard_summary_dropdown_strategy.value == 'peryear':
                strategy = SummaryStrategies.PER_YEAR
                
            # Verifying features
            features = {
                'min': False, 'max': False, 'sum': False, 'avg': False,
                'median': False, 'mode': False, 'stddev': False, 'spread': False
            }
            for feature in features:
                if feature in tab_dashboard_summary_select_multiple_features.value:
                    features[feature] = True
            
            params = { 'from': fromTimestamp, 'to': toTimestamp, 'precision': 'ms', **features }
            
            df = portiaApi.device(item['edgeid']).port(item['port']).sensor(item['sensor']).dimension(item['dimension']).summary(strategy, tab_dashboard_summary_int_slider_interval.value, params)
            
            dfs.append(df)
        except Exception as e: 
            print(e)
    utils.plotSummariesFromDataframes(dfs)

# Configuring buttons
tab_dashboard_summary_button_load_data.on_click(on_tab_dashboard_summary_button_load_data_click)

# Configuring labels
tab_dashboard_summary_interactive_update = widgets.interactive(executeSummary, x = tab_dashboard_summary_label_update)

# Building tab summary
tab_dashboard_summary_hbox_widgets = widgets.HBox([tab_dashboard_summary_int_slider_interval, tab_dashboard_summary_dropdown_strategy, tab_dashboard_summary_select_multiple_features, tab_dashboard_summary_button_load_data])
tab_dashboard_summary_vbox         = widgets.VBox([tab_dashboard_body_hbox_date_controls, tab_dashboard_summary_hbox_widgets, tab_dashboard_summary_interactive_update])
                                       
########################### TABS ##########################

# Building tab dashboard
tab_dashboard_tab_features = widgets.Tab(children=[tab_dashboard_select_vbox, tab_dashboard_summary_vbox])
tab_dashboard_tab_features.set_title(0, 'Select')
tab_dashboard_tab_features.set_title(1, 'Summary')
tab_dashboard              = widgets.VBox([tab_dashboard_header_vbox, getBlankspace(), tab_dashboard_tab_features, getBlankspace()])

###########################################################


######################### CLIENTS #########################

# Creating widgets
tab_clients_label_client_info = widgets.Label( value='Client Information:', layout=widgets.Layout(width='99%') )

tab_clients_label_new_client  = widgets.Label( value='New Client:        ', layout=widgets.Layout(width='99%') )
tab_clients_text_client_name  = widgets.Text( description='Name:  ',  placeholder='Fulano da Silva',  layout=widgets.Layout(width='33%') )
tab_clients_text_client_email = widgets.Text( description='Email: ',  placeholder='fulano@gmail.com', layout=widgets.Layout(width='33%') )
tab_clients_button_insert     = widgets.Button( description='Insert', layout=widgets.Layout(width='20%') )
tab_clients_label_insert      = getBlankspace(5)

# On click functions
def on_tab_clients_button_insert_click(x):
    global dashDatabase
    
    if dashDatabase.insertClient(tab_clients_text_client_name.value, tab_clients_text_client_email.value) == True:
        tab_clients_label_insert.value      = 'OK'
        
        # Updating clients
        dropdown_clients.options = utils.mapClientsToWidget( dashDatabase.getClients() )
        
        tab_clients_text_client_name.value  = ''
        tab_clients_text_client_email.value = ''
    else:
        tab_clients_label_insert.value      = 'Error'
        
    time.sleep(3)
    tab_clients_label_insert.value = ''
    
# Configuring buttons
tab_clients_button_insert.on_click(on_tab_clients_button_insert_click)

# Building tab clients
tab_clients_hbox_client_info = widgets.HBox([dropdown_clients, text_client_email])
tab_clients_hbox_new_client  = widgets.HBox([tab_clients_text_client_name, tab_clients_text_client_email, getBlankspace(1.5), tab_clients_button_insert, getBlankspace(1.5), tab_clients_label_insert])
tab_clients                  = widgets.VBox([tab_clients_label_client_info, tab_clients_hbox_client_info, tab_clients_label_new_client, tab_clients_hbox_new_client])

###########################################################


########################## AREAS ##########################

# Creating widgets
tab_areas_label_farm_info       = widgets.Label( value='Farm Information:', layout=widgets.Layout(width='99%') )

tab_areas_label_new_farm        = widgets.Label( value='New Farm:        ', layout=widgets.Layout(width='99%') )
tab_areas_text_farm_name        = widgets.Text( description='Name:        ', placeholder='Fazenda 17 de Fevereiro', layout=widgets.Layout(width='33%') )
tab_areas_text_farm_description = widgets.Text( description='Description: ', placeholder='Criação de suínos', layout=widgets.Layout(width='33%') )
tab_areas_button_insert_farm    = widgets.Button( description='Insert', layout=widgets.Layout(width='20%') )
tab_areas_label_insert_farm     = getBlankspace(5)

tab_areas_separator             = widgets.HTML( value="<hr>" )

tab_areas_label_area_info       = widgets.Label( value='Area Information:', layout=widgets.Layout(width='99%') )

tab_areas_label_new_area        = widgets.Label( value='New Area:', layout=widgets.Layout(width='99%') )
tab_areas_text_area_label       = widgets.Text( description='Label: ', placeholder='Aviário 1', layout=widgets.Layout(width='33%') )
tab_areas_button_insert_area    = widgets.Button( description='Insert', layout=widgets.Layout(width='20%') )
tab_areas_label_insert_area     = getBlankspace(5)

# On click functions
def on_tab_areas_button_insert_farm_click(x):
    global dashDatabase
    
    if dashDatabase.insertFarm(tab_areas_text_farm_name.value, tab_areas_text_farm_description.value, dropdown_clients.value) == True:
        tab_areas_label_insert_farm.value     = 'OK'
        
        # Updating farms
        farmList = dashDatabase.getClientFarms(dropdown_clients.value)
        dropdown_farms.options = utils.mapFarmsToWidget(farmList)
        
        tab_areas_text_farm_name.value        = ''
        tab_areas_text_farm_description.value = ''
    else:
        tab_areas_label_insert_farm.value     = 'Error'
        
    time.sleep(3)
    tab_areas_label_insert_farm.value = ''
    
def on_tab_areas_button_insert_area_click(x):
    global dashDatabase
    
    if dashDatabase.insertSpot(tab_areas_text_area_label.value, dropdown_farms.value) == True:
        tab_areas_label_insert_area.value = 'OK'
        
        # Updating spots
        spotList = dashDatabase.getFarmSpots(dropdown_farms.value)
        dropdown_spots.options = utils.mapSpotsToWidget(spotList)
        
        tab_areas_text_area_label.value   = ''
    else:
        tab_areas_label_insert_area.value = 'Error'
        
    time.sleep(3)
    tab_areas_label_insert_area.value = ''
    
# Configuring buttons
tab_areas_button_insert_farm.on_click(on_tab_areas_button_insert_farm_click)
tab_areas_button_insert_area.on_click(on_tab_areas_button_insert_area_click)

# Building tab areas
tab_areas_hbox_farm_info = widgets.HBox([dropdown_farms, text_farm_description])
tab_areas_hbox_new_farm  = widgets.HBox([tab_areas_text_farm_name, tab_areas_text_farm_description, getBlankspace(1.5), tab_areas_button_insert_farm, getBlankspace(1.5), tab_areas_label_insert_farm])

tab_areas_hbox_area_info = widgets.HBox([dropdown_spots])
tab_areas_hbox_new_area  = widgets.HBox([tab_areas_text_area_label, getBlankspace(1.5), tab_areas_button_insert_area, getBlankspace(1.5), tab_areas_label_insert_area])

tab_areas                = widgets.VBox([
    tab_areas_label_farm_info, tab_areas_hbox_farm_info, tab_areas_label_new_farm, tab_areas_hbox_new_farm,
    tab_areas_separator,
    tab_areas_label_area_info, tab_areas_hbox_area_info, tab_areas_label_new_area, tab_areas_hbox_new_area
])

###########################################################


######################### DEVICES #########################

# Creating widgets
tab_devices_label_device_info   = widgets.Label( value='Device Information:', layout=widgets.Layout(width='99%') )

tab_devices_label_new_device    = widgets.Label( value='New Device        :', layout=widgets.Layout(width='99%') )
tab_devices_text_device_qrcode  = widgets.Text( description='QRCode: ', placeholder='{"Edgeid":["AAAABBBBCCCC","BBBBCCCCAAAA"]}', layout=widgets.Layout(width='66.6%') )
tab_devices_button_insert       = widgets.Button( description='Insert', layout=widgets.Layout(width='15%') )
tab_devices_label_insert        = getBlankspace(10)

# On click functions
def on_tab_devices_button_insert_click(x):
    global dashDatabase
    
    # Parsing QRCode text field
    try:
        qrCodeValue = json.loads(tab_devices_text_device_qrcode.value)
        
        # For each device
        for i, edgeId in enumerate(qrCodeValue['Edgeid']):
            
            try:
                profile = portiaApi.device(edgeId).profile()
                thingCode = int(profile['thing_code'])
                
                if dashDatabase.insertDevice(edgeId, int(dropdown_clients.value), int(dropdown_farms.value), thingCode) == True:
                    
                    for port in portiaApi.device(edgeId).ports():
                        for sensor in portiaApi.device(edgeId).port(port).sensors():
                            for index, dimension in portiaApi.device(edgeId).port(port).sensor(sensor).dimensions(last=True).iterrows( ):

                                if dashDatabase.insertDimension(edgeId, port, sensor, dimension['dimension_code'], dropdown_spots.value, 0, None, dimension['dimension_value'], dimension['header_timestamp']) == True:
                                    tab_devices_label_insert.value = 'OK ({})'.format(i + 1)
                                else:
                                    tab_devices_label_insert.value = 'Database Error ({})'.format(i + 1)
                    
                else:
                    tab_devices_label_insert.value = 'Database Error ({})'.format(i + 1)
                    
                time.sleep(1)
                
            except Exception as e:
                print(e)
                tab_devices_label_insert.value = 'Device Not Found'
                time.sleep(1)
                
        ## end for
                
        tab_devices_text_device_qrcode.value = ''
                
        # Updating devices
        deviceList = dashDatabase.getFarmDevices(dropdown_farms.value)
        dropdown_devices.options = utils.mapDevicesToWidget(deviceList)
        
        time.sleep(2)
                
    except Exception as e2:
        print(e2)
        tab_devices_label_insert.value = 'Parsing Error'
        time.sleep(3)
        
    tab_devices_label_insert.value = ''

# Configuring buttons
tab_devices_button_insert.on_click(on_tab_devices_button_insert_click)
    
# Building tab devices
tab_devices_hbox_device_info = widgets.HBox([dropdown_farms, dropdown_devices, text_device_type])
tab_areas_hbox_new_device    = widgets.HBox([tab_devices_text_device_qrcode, getBlankspace(1.5), tab_devices_button_insert, getBlankspace(1.5), tab_devices_label_insert])
tab_devices                  = widgets.VBox([tab_devices_label_device_info, tab_devices_hbox_device_info, tab_devices_label_new_device, tab_areas_hbox_new_device])

###########################################################


######################### METRICS #########################
tab_dimensions = widgets.VBox()
###########################################################


###################### CONFIGURATION ######################

# Creating widgets
tab_configuration_text_api_url   = widgets.Text( description='API URL:   ', placeholder='API URL', value='http://edge-portia-api.sa-east-1.elasticbeanstalk.com/v3', layout=widgets.Layout(width='99%') )
tab_configuration_text_api_token = widgets.Text( description='API Token: ', placeholder='Your API Token here', layout=widgets.Layout(width='99%') )

tab_configuration_button_save_configuration = widgets.Button( description='Save Configuration',     layout=widgets.Layout(width='30%') )
tab_configuration_label_save_configuration  = getBlankspace(4)
tab_configuration_button_upload_database    = widgets.Button( description='Upload Database',        layout=widgets.Layout(width='30%') )
tab_configuration_label_upload_database     = getBlankspace(4)
tab_configuration_button_download_database  = widgets.HTML( '<a href="./database/sample.sqlite" style="width: 100%;"><button class="p-Widget jupyter-widgets jupyter-button widget-button" title="" style="width: 100%;">Donwload Database</button></a>', layout=widgets.Layout(width='30%') )

# tab_configuration_button_upload_database    = widgets.HTML( '<form class="p-Widget jupyter-widgets jupyter-button widget-button" action="/action_page.php" style="width: 100%;"><input type="file" name="sample" accept=".sqlite" style="width: 100%;" value="Upload Database"></form>', layout=widgets.Layout(width='30%') )

# On click functions
def on_tab_configuration_button_save_configuration_click(x):    
    portiaConfig['baseurl']       = tab_configuration_text_api_url.value
    portiaConfig['authorization'] = tab_configuration_text_api_token.value
    
    portiaApi = PortiaApi(portiaConfig)
    
    tab_configuration_label_save_configuration.value = 'OK'
    time.sleep(3)
    tab_configuration_label_save_configuration.value = ''

def on_tab_configuration_button_upload_database_click(x):
    tab_configuration_label_upload_database.value = 'OK'
    time.sleep(3)
    tab_configuration_label_upload_database.value = ''
    
# Configuring buttons
tab_configuration_button_save_configuration.on_click(on_tab_configuration_button_save_configuration_click)
# tab_configuration_button_upload_database.on_click(on_tab_configuration_button_upload_database_click)

# Building tab configuration
tab_configuration_hbox_buttons = widgets.HBox([tab_configuration_button_save_configuration, tab_configuration_label_save_configuration, tab_configuration_button_upload_database, tab_configuration_label_upload_database, tab_configuration_button_download_database])
tab_configuration              = widgets.VBox([tab_configuration_text_api_url, tab_configuration_text_api_token, tab_configuration_hbox_buttons])

###########################################################


########################### VIEW ##########################
            
# tab_s4 = widgets.VBox([header_vbox,w_blankspace,hbox2,w_blankspace])
tab = widgets.Tab(children=[tab_dashboard, tab_clients, tab_areas, tab_devices, tab_dimensions, tab_configuration])
tab.set_title(0, 'Dashboard')
tab.set_title(1, 'My Clients')
tab.set_title(2, 'My Areas')
tab.set_title(3, 'My Devices')
tab.set_title(4, 'My Metrics')
tab.set_title(5, 'Configuration')
                                       
def start(database):
    global dashDatabase
    dashDatabase = database

    # Starts loading clients
    dropdown_clients.options = utils.mapClientsToWidget( dashDatabase.getClients() )
    
    return tab
###########################################################
