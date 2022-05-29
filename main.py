from kivy.app import App
from kivy.uix.settings import SettingsWithTabbedPanel
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.properties import NumericProperty,StringProperty,ReferenceListProperty,ObjectProperty

import http.client as httplib
import paho.mqtt.client as mqtt

from random import sample, randint,choice
from string import ascii_lowercase
from datetime import datetime

import RPi.GPIO as GPIO
import time
import requests
import json
import uuid
import sys
#



def on_disconnect(client, userdata, rc=0):
    print("DisConnected flags"+"result code "+str(rc)+"client_id  ")
    client.connected_flag=False

def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("connected OK Returned code=", rc)
        client.connected_flag=True #Flag to indicate success
    else:
        print("Bad connection Returned code=", rc)
        #client.bad_connection_flag=True
        client.connected_flag=False
        sys.exit(1) #quit

def on_log(client, userdata, level, buf):
    print("log: ",buf)
    
def on_message(client, userdata, message):
    print("message received  "  ,str(message.payload.decode("utf-8")))


QOS1=1
QOS2=0
CLEAN_SESSION=False

broker_port=1883
broker_address="teksmartsolutions.com"

print("creating new instance")
client = mqtt.Client(str(uuid.uuid1()), False, None, mqtt.MQTTv311, transport="tcp")
#client = mqtt.Client(str(uuid.uuid1()), True, None, mqtt.MQTTv311, transport="tcp")
client.username_pw_set(username="iotsystem",password="iotsystem@123")
client.on_log=on_log
mqtt.Client.connected_flag=False 
mqtt.Client.bad_connection_flag=False 
mqtt.Client.retry_count=0 
client.on_connect=on_connect
client.on_disconnect=on_disconnect
client.on_message = on_message

retry=0
retry_limit=99999
retry_delay_fixed=2
connected_once=False
count=0


#client.connect(broker_address)
#client.on_disconnect = client.reconnect()


FireSensor = 21
FaultSensor = 20

Buzzer = 24

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(FireSensor,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(FaultSensor,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(Buzzer,GPIO.OUT)

kv = """
<Test>:
    background_color: 1, 0, 0, 1
    Image:
        pos: 0,410
        size_hint: None, None
        size: 160, 60
        source: "data/logo.png"
    Label:
        id : timestatus
        pos: 650,420
        size_hint: None, None
        font_size: self.width/5
        size: 150, 60
        text: '14:18'
    
    Label:
        id : datestatus
        pos: 650,400
        size_hint: None, None
        size: 150, 60
        text: '23 Mar, Wed'
    Label:
        id : netstatus
        pos: 90,30
        size_hint: None, None
        font_size: self.width/3
        size: 65, 40
        halign : 'left'
        text: 'Active'
    Label:
        pos: 130,100
        size_hint: None, None
        size: 150, 60
        text: 'Fire Detection'
    Label:
        pos: 530,100
        size_hint: None, None
        size: 150, 60
        text: 'Fault Detection'
    Button:
        id:setting
        pos: 380,30
        size_hint: None, None
        size: 40, 40
        background_normal: "data/setting.png"
        background_down: "data/setting.png"
        on_press: app.open_settings()
    Image:
        id : firestatus
        pos: 0,0
        size_hint: None, None
        size: 400, 480
        source: "data/no_fire.png"
    Image:
        id : faultstatus
        pos: 400,0
        size_hint: None, None
        size: 400, 480
        source: "data/no_fault.png" 
    Button:
        id:buzzerbutton
        pos: 700,0
        size_hint: None, None
        size: 100, 100
        background_normal: "data/no_buzzer.png" 
        background_down: "data/no_buzzer.png" 
        on_press: root.stopbuzzer()
    Image:
        id : netstatusimg
        pos: 0,0
        size_hint: None, None
        size: 100, 100
        source: "data/active.png" 
"""



jsonx = '''
[
    {
        "type": "bool",
        "title": "Fire Connection",
        "desc": "Choose the NO or NC (OFF = NO)",
        "section": "Configuration",
        "key": "fireconn"
    },
    {
        "type": "bool",
        "title": "Fault Connection",
        "desc": "Choose the NO or NC (OFF = NO)",
        "section": "Configuration",
        "key": "faultconn"
    },
    {
        "type": "string",
        "title": "Device No.",
        "desc": "Choose the No. to map on IoT Platform",
        "section": "Configuration",
        "key": "deviceID"
    },
    {
        "type": "string",
        "title": "Device Name",
        "desc": "Choose the name that appears in the Platform",
        "section": "Configuration",
        "key": "deviceName"
    },
    {
        "type": "string",
        "title": "Contact No.",
        "desc": "Phone No. of Contact Person",
        "section": "Configuration",
        "key": "contactNo"
    },
    {
        "type": "string",
        "title": "Contact Name.",
        "desc": "Name of Contact Person ",
        "section": "Configuration",
        "key": "contactName"
    },
    {
        "type": "string",
        "title": "Device Location",
        "desc": "Location of the device",
        "section": "Configuration",
        "key": "deviceLoc"
    },
    {
        "type": "string",
        "title": "Building No.",
        "desc": "Building No.",
        "section": "Configuration",
        "key": "buildingNo"
    },
    {
        "type": "string",
        "title": "Building Name",
        "desc": "Building Name",
        "section": "Configuration",
        "key": "buildingName"
    },
    {
        "type": "string",
        "title": "Building Category",
        "desc": "Category of Building (Hotel, Government etc.)",
        "section": "Configuration",
        "key": "buildingCategory"
    },
    {
        "type": "string",
        "title": "Street Address",
        "desc": "Street Address",
        "section": "Configuration",
        "key": "streetAdd"
    },
    {
        "type": "string",
        "title": "City",
        "desc": "City",
        "section": "Configuration",
        "key": "city"
    },
    {
        "type": "string",
        "title": "City Zone",
        "desc": "Zone is Part of of the City (S, W, E, N etc.)",
        "section": "Configuration",
        "key": "cityZone"
    },
    {
        "type": "string",
        "title": "Country",
        "desc": "Country",
        "section": "Configuration",
        "key": "contry"
    },
    {
        "type": "string",
        "title": "Device Longitude",
        "desc": "Longitude (55.05356 etc.)",
        "section": "Configuration",
        "key": "deviceLng"
    },
    {
        "type": "string",
        "title": "Device Lattitude",
        "desc": "Lattitude (25.05356 etc.)",
        "section": "Configuration",
        "key": "deviceLat"
    }
]
'''

def have_connection():
    global retry,connected_once#broker,port
    if not client.connected_flag:
        try:
            retry+=1
            if connected_once:
                print("Reconnecting attempt Number=",retry)
            else:
                print("Connecting attempt Number=",retry )
            client.connect(broker_address,broker_port)#,keepalive=5
            while not client.connected_flag:
                client.loop(0.5)
            connected_once=True
            retry=0
            return True, 0
        except Exception as e:
            print("Connect failed : ",e)
            if(retry > 9):
                sys.exit(1)
            else:
                return False, retry
    else:
        return True , 0
'''
    conn = httplib.HTTPSConnection("teksmartsolutions.com", timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except Exception:
        return False
    finally:
        conn.close()
'''        

class Test(RelativeLayout):
    ATEFireStatus = 0
    ATEFaultStatus = 0
    def __init__(self, **kwargs):
        super(Test, self).__init__(**kwargs)
        self.configurationVariable = {
            "id":"",
            "deviceName":"",
            "updatedTime":None,
            "firestatus":False,
            "faultstatus":False,
            "alarm":None,
            "contactNo":"",
            "contactName":"",
            "deviceLoc":"",
            "buildingNo":"",
            "buildingName":"",
            "buildingCategory":"",
            "streetAdd":"",
            "city":"",
            "cityZone":"",
            "contry":"",
            "lon":"",
            "lat":"",
            "timestamp":None,
            "fireconn":False,
            "faultconn":False
        } #if Required change these parameter with relative calling for mapping directly to Local or Elm Server
        self.flag_connected = 0


    def startstop(self):
        self.ids.datestatus.text = str(datetime.now().strftime("%d %b, %a"))
        self.ids.timestatus.text = str(datetime.now().strftime("%H:%M"))
        self.configurationVariable['updatedTime'] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.configurationVariable['timestamp'] = int(time.time())
        Clock.schedule_interval(self.checkalert, 1)
        Clock.schedule_interval(self.updatetime, 60)
        Clock.schedule_interval(self.checkconn, 2)
        Clock.schedule_once(self.SentInitialmsg,5)
        return
    
    
    def SentInitialmsg(self,dt):
        if client.connected_flag:
            ret = client.publish("/ate/tektron/"+self.configurationVariable['id'],json.dumps(self.configurationVariable),qos=0)
            print("publish Inital Message",ret)
    
    def checkconn(self,dt):
        CurrentState, noretries = have_connection()
        self.flag_connected = client.connected_flag
        print(self.flag_connected)
        #if client.connected_flag:
        ret = client.publish("/ate/tektron/HeartBeats","",qos=0)
        print("publish Heartbeat Message",ret)
            
        if(CurrentState == True):
            if(self.flag_connected == True):
                self.ids.netstatusimg.source = "data/active.png"
                self.ids.netstatus.text = "Active"
                self.ids.netstatus.halign = "left"
            else:
                self.ids.netstatusimg.source = "data/deactive.png"
                self.ids.netstatus.text = "Deactive.." + str(noretries)
                self.ids.netstatus.halign = "left"
        else:
            if(self.flag_connected == True):
                self.ids.netstatusimg.source = "data/active.png"
                self.ids.netstatus.text = "Active"
                self.ids.netstatus.halign = "left"
            else:
                self.ids.netstatusimg.source = "data/deactive.png"
                self.ids.netstatus.text = "Deactive.." + str(noretries)
                self.ids.netstatus.halign = "left"
        pass
        #print(self.configurationVariable)
        return
    

    def updatetime(self,dt):
        self.ids.datestatus.text = str(datetime.now().strftime("%d %b, %a"))
        self.ids.timestatus.text = str(datetime.now().strftime("%H:%M"))
        self.configurationVariable['updatedTime'] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.configurationVariable['timestamp'] = int(time.time())
        client.loop(0.5)
        #if client.connected_flag:
        print("/ate/tektron/"+self.configurationVariable['id'])
        ret = client.publish("/ate/tektron/"+self.configurationVariable['id'],json.dumps(self.configurationVariable),qos=0)
        print("publish",ret)
        return

    def checkalert(self,dt):
        #self.ids.netstatus.text = str(self.ATEFireStatus) + " " + str(GPIO.input(FireSensor)) + " " + str(self.configurationVariable['fireconn'])
        
        if(self.ATEFaultStatus == 0): 
            if(GPIO.input(FaultSensor)==int(self.configurationVariable['faultconn'])):
                self.configurationVariable['alarm'] = "fault"
                self.configurationVariable['faultstatus'] = True
                self.ids.faultstatus.source = "data/fault.png"
                GPIO.output(Buzzer, 1)
                self.ids.buzzerbutton.background_normal = "data/buzzer.png"
                client.loop(0.5)
                #if client.connected_flag:
                ret = client.publish("/ate/tektron/"+self.configurationVariable['id'],json.dumps(self.configurationVariable),qos=0)
                print("publish",ret)
                self.ATEFaultStatus = 1
                pass
            else:
                self.configurationVariable['alarm'] = None
                self.ids.faultstatus.source = "data/no_fault.png"
                self.configurationVariable['faultstatus'] = False
                pass
        
        if(GPIO.input(FaultSensor) != int(self.configurationVariable['faultconn'])):
            self.configurationVariable['alarm'] = None
            self.configurationVariable['faultstatus'] = False
            self.ids.faultstatus.source = "data/no_fault.png"
            self.ATEFaultStatus = 0
            
        if(self.ATEFireStatus == 0):
            if(GPIO.input(FireSensor)==int(self.configurationVariable['fireconn'])):
                self.configurationVariable['alarm'] = "sos"
                self.configurationVariable['firestatus'] = True
                self.ids.firestatus.source = "data/fire.png"
                GPIO.output(Buzzer, 1)
                self.ids.buzzerbutton.background_normal = "data/buzzer.png"
                client.loop(0.5)
                #if client.connected_flag:
                ret = client.publish("/ate/tektron/"+self.configurationVariable['id'],json.dumps(self.configurationVariable),qos=0)
                print("publish",ret)
                self.ATEFireStatus = 1
                pass
            else:
                self.configurationVariable['alarm'] = None
                self.ids.firestatus.source = "data/no_fire.png"
                self.configurationVariable['firestatus'] = False
                pass

        if(GPIO.input(FireSensor) != int(self.configurationVariable['fireconn'])):
            self.configurationVariable['alarm'] = None
            self.configurationVariable['firestatus'] = False
            self.ids.firestatus.source = "data/no_fire.png"
            self.ATEFireStatus = 0
            
        
            
        if(GPIO.input(FaultSensor) != int(self.configurationVariable['faultconn']) and GPIO.input(FireSensor) != int(self.configurationVariable['fireconn'])):
            self.configurationVariable['alarm'] = None
            self.configurationVariable['firestatus'] = False
            self.configurationVariable['faultstatus'] = False
            GPIO.output(Buzzer, 0)
            self.ids.buzzerbutton.background_normal = "data/no_buzzer.png"
            self.ids.firestatus.source = "data/no_fire.png"
            self.ids.faultstatus.source = "data/no_fault.png"
            self.ATEFaultStatus = 0
            self.ATEFireStatus = 0
        
        return # change
    
    def stopbuzzer(self):
        self.ids.buzzerbutton.background_normal = "data/no_buzzer.png"
        print("Buzzer Off")
        GPIO.output(Buzzer, 0)
        return   



class MySettingsWithTabbedPanel(SettingsWithTabbedPanel):
    def on_close(self):
        Logger.info("main.py: MySettingsWithTabbedPanel.on_close")

    def on_config_change(self, config, section, key, value):
        Logger.info( "main.py: MySettingsWithTabbedPanel.on_config_change: ""{0}, {1}, {2}, {3}".format(config, section, key, value))

class TestApp(App):
    def on_start(self):
        self.widget.startstop()
        #self.widget.startMQTT()
        print(self.config.get('Configuration', 'deviceID'))
        pass
        
    def build(self):
        Builder.load_string(kv)
        root = self.settings_cls = MySettingsWithTabbedPanel
        self.widget = Test()
        self.widget.configurationVariable["fireconn"] = self.config.get('Configuration', 'fireconn')
        self.widget.configurationVariable["faultconn"] = self.config.get('Configuration', 'faultconn')
        self.widget.configurationVariable["id"] = str(self.config.get('Configuration', 'deviceID'))
        self.widget.configurationVariable["deviceName"] = str(self.config.get('Configuration', 'deviceName'))
        self.widget.configurationVariable["contactNo"] = str(self.config.get('Configuration', 'contactNo'))
        self.widget.configurationVariable["contactName"] = str(self.config.get('Configuration', 'contactName'))
        self.widget.configurationVariable["deviceLoc"] = str(self.config.get('Configuration', 'deviceLoc'))
        self.widget.configurationVariable["buildingNo"] = str(self.config.get('Configuration', 'buildingNo'))
        self.widget.configurationVariable["buildingName"] = str(self.config.get('Configuration', 'buildingName'))
        self.widget.configurationVariable["buildingCategory"] = str(int(self.config.get('Configuration', 'buildingCategory')))
        self.widget.configurationVariable["streetAdd"] = str(self.config.get('Configuration', 'streetAdd'))
        self.widget.configurationVariable["city"] = str(self.config.get('Configuration', 'city'))
        self.widget.configurationVariable["cityZone"] = str(int(self.config.get('Configuration', 'cityZone')))
        self.widget.configurationVariable["contry"]= str(self.config.get('Configuration', 'contry'))
        self.widget.configurationVariable["lon"] = str(self.config.get('Configuration', 'deviceLng'))
        self.widget.configurationVariable["lat"] = str(self.config.get('Configuration', 'deviceLat'))
        return self.widget

    def build_config(self, config):
        pass
        config.setdefaults('Configuration', {})
        
    def build_settings(self, settings):
        settings.add_json_panel('Configuration', self.config, data=jsonx)
        pass

    def on_config_change(self, config, section, key, value):
        Logger.info("main.py: App.on_config_change: {0}, {1}, {2}, {3}".format(config, section, key, value))
        if section == "Configuration":
            if key == "fireconn":
                self.widget.configurationVariable["fireconn"] = value
            elif key == "faultconn":
                self.widget.configurationVariable["faultconn"] = value
            elif key == "deviceID":
                self.widget.configurationVariable["id"] = str(value)
            elif key == 'deviceName':
                 self.widget.configurationVariable["deviceName"] = str(value)
            elif key == 'contactNo':
                 self.widget.configurationVariable["contactNo"] = str(value)
            elif key == 'contactName':
                 self.widget.configurationVariable["contactName"] = str(value)
            elif key == 'deviceLoc': ######
                 self.widget.configurationVariable["deviceLoc"] = str(value)
            elif key == 'buildingNo': ######
                 self.widget.configurationVariable["buildingNo"] = str(value)
            elif key == 'buildingName': ######
                 self.widget.configurationVariable["buildingName"] = str(value)
            elif key == 'buildingCategory':
                 self.widget.configurationVariable["buildingCategory"] = int(value)
            elif key == 'streetAdd':
                 self.widget.configurationVariable["streetAdd"] = str(value)
            elif key == 'city':
                 self.widget.configurationVariable["city"] = str(value)
            elif key == 'cityZone':
                 self.widget.configurationVariable["cityZone"] = int(value)
            elif key == 'contry':
                 self.widget.configurationVariable["contry"]= str(value)
            elif key == 'deviceLng':
                 self.widget.configurationVariable["lon"] = str(value)
            elif key == 'deviceLat':
                 self.widget.configurationVariable["lat"] = str(value)

    def close_settings(self, settings=None):
        Logger.info("main.py: App.close_settings: {0}".format(settings))
        super(TestApp, self).close_settings(settings)


if __name__ == '__main__':
    TestApp().run()

