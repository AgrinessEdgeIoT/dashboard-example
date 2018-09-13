######################### IMPORTS #########################

from sqlalchemy             import create_engine # The Python SQL toolkit and object relational mapper
from sqlalchemy.orm         import Session
from sqlalchemy.ext.automap import automap_base

######################### CLASSES #########################

class DashDatabase:
    
    def __init__(self, dbUri):
        # Creates engine
        engine = create_engine(dbUri, echo=False)

        # Produces a declarative automap base
        Base = automap_base()
        Base.prepare(engine, reflect=True) # Reflects the tables

        # Mapped classes are now created with names by default
        # matching that of the table name
        self.Client    = Base.classes.clients
        self.Farm      = Base.classes.farms
        self.Spot      = Base.classes.spots
        self.Device    = Base.classes.devices
        self.Dimension = Base.classes.dimensions

        # Creating session
        self.session = Session(engine)
    
    # Client Functions
    def getClient(self, clientId):
        return self.session.query( self.Client ).filter( self.Client.id == clientId ).one()
    
    def getClients(self):
        return self.session.query( self.Client ).all()
    
    def getClientFarms(self, clientId):
        client = self.session.query( self.Client ).filter( self.Client.id == clientId ).one()
        return client.farms_collection
    
    def getClientDevices(self, clientId):
        client = self.session.query( self.Client ).filter( self.Client.id == clientId ).one()
        return client.devices_collection
    
    def insertClient(self, clientName, clientEmail):
        try:
            newClient = self.Client(name = clientName, email = clientEmail)
            self.session.add(newClient)
            self.session.commit()
            return True
        except:
            self.session.rollback()
            return False
    
    # Farm Functions
    def getFarm(self, farmId):
        return self.session.query( self.Farm ).filter( self.Farm.id == farmId ).one()
    
    def getFarmSpots(self, farmId):
        farm = self.session.query( self.Farm ).filter( self.Farm.id == farmId ).one()
        return farm.spots_collection
    
    def getFarmDevices(self, farmId):
        farm = self.session.query( self.Farm ).filter( self.Farm.id == farmId ).one()
        return farm.devices_collection
    
    def insertFarm(self, farmName, farmDescription, ownerId):
        try:
            newFarm = self.Farm(name = farmName, description = farmDescription, owner_id = ownerId)
            self.session.add(newFarm)
            self.session.commit()
            return True
        except:
            self.session.rollback()
            return False
    
    # Spot Functions
    def getSpot(self, spotId):
        return self.session.query( self.Spot ).filter( self.Spot.id == spotId ).one()
    
    def getSpotDimensions(self, spotId):
        spot = self.session.query( self.Spot ).filter( self.Spot.id == spotId ).one()
        return spot.dimensions_collection
    
    def insertSpot(self, spotLabel, farmId):
        try:
            newSpot = self.Spot(label = spotLabel, farm_id = farmId)
            self.session.add(newSpot)
            self.session.commit()
            return True
        except:
            self.session.rollback()
            return False
    
    # Device Functions
    def getDevice(self, edgeId, clientId):
        return self.session.query( self.Device ).filter( self.Device.edgeid == edgeId ).filter( self.Device.client_id == clientId ).one()
    
    def getDeviceDimensions(self, edgeId):
        device = self.session.query( self.Device ).filter( self.Device.edgeid == edgeId ).one()
        return device.dimensions_collection
    
    def insertDevice(self, edgeId, clientId, farmId, thingCode):
        try:
            newDevice = self.Device(edgeid = edgeId, client_id = clientId, farm_id = farmId, thing_code = thingCode)
            self.session.add(newDevice)
            self.session.commit()
            return True
        except:
            self.session.rollback()
            return False

    # Dimension Functions
    def insertDimension(self, edgeId, port, sensor, dimension, spotId, tsFrom, tsTo, lastValue, lastValueTs):
        try:
            newDimension = self.Dimension(edgeid = edgeId, port = port, sensor = sensor, dimension = dimension, spot_id = spotId, ts_from = tsFrom, ts_to = tsTo, last_value = lastValue, last_value_ts = lastValueTs)
            self.session.add(newDimension)
            self.session.commit()
            return True
        except:
            self.session.rollback()
            return False