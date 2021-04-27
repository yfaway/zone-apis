# Zone API - an alternative approach to writing rules
In OpenHab, items are defined in a flat manner in the *.items* files under the */etc/openhab/items folder*.
They are typically linked to a channel exposed by the underlying hardware.
This flat structure has an impact on how rules (whether in Xtend or Jython) are organized. As there
is no higher level abstraction, rules tend to listen to changes from the specific devices. When the
rules need to interact with multiple devices of the same type, they can utilize the 
[group concept](https://www.openhab.org/docs/configuration/items.html#groups). An example of good
usage of group is to turn off all lights. By linking all smart lights to a group switch, turning off
all the lights can be done by changing the state of the group switch to OFF.
                                                                                
What is more tricky is when rules need to interact with different devices within the same area. The
typical solution is to group unrelated items that belong to the same zone either by using a naming
pattern, or by dedicated groups. For example, the light switch and motion sensor in the Foyer area
can be named like this: "FF_Foyer_Light", and "FF_Foyer_MotionSensor". When a sensor is triggered,
the zone can be derived from the name of the triggering item, and other devices/sensors can be
retrieved using that naming convention. This works but as there is not sufficient abstraction, the
rules are highly coupled to the naming pattern.
                                                                                
The [Zone API](https://github.com/yfaway/zone-apis) provides another approach. It is a layer
above the devices / sensors. Each [ZoneManager](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/immutable_zone_manager.py)
(i.e. a house) contains multiple [zones](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/zone.py)
(i.e. rooms), and each zone contains multiple [devices](https://github.com/yfaway/zone-apis/tree/master/src/zone_api/core/devices).
Each zone is associated with a set of [actions](https://github.com/yfaway/zone-apis/tree/master/src/zone_api/core/actions) 
that are triggered by certain [events](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/zone_event.py).
The usual OpenHab events are routed in this manner:

```
OpenHab events --> ZoneManager --> Zones --> Actions
```

The actions operate on the abstract devices and do not concern about the naming of the items or
the underlying hardware. They replace the traditional OpenHab rules. Actions can be unit-tested with
various levels of mocking.

**Most importantly, it enables reusing of action logics.** There is no need to reinvent the wheels for 
common rules such as turning on/off the lights. All ones need to do is to populate the zones and
devices / sensors, and the applicable actions will be added and processed automatically.

ZoneApi comes with a set of built-in [actions](https://github.com/yfaway/zone-apis/tree/master/src/zone_api/core/actions).
There is no need to determine what action to add to a system. Instead, they are added automatically based on the
zones structure and based on the type of devices available in each zone.

Here is a sample info log that illustrate the structure of the managed objects.
```text
Zone: Kitchen, floor: FIRST_FLOOR, internal, displayIcon: kitchen, displayOrder: 3, 7 devices
  AstroSensor: VT_Time_Of_Day                                                   
  HumiditySensor: FF_Kitchen_Humidity                                           
  IlluminanceSensor: FF_Kitchen_LightSwitch_Illuminance                         
  Light: FF_Kitchen_LightSwitch, duration: 5 mins, illuminance: 8               
  MotionSensor: FF_Kitchen_SecurityMotionSensor, battery powered                
  MotionSensor: FF_Kitchen_LightSwitch_PantryMotionSensor, battery powered      
  TemperatureSensor: FF_Kitchen_Temperature                                     
                                                                                
  Action: HUMIDITY_CHANGED -> AlertOnHumidityOutOfRange                         
  Action: MOTION -> TurnOnSwitch                                                
  Action: MOTION -> AnnounceMorningWeatherAndPlayMusic                          
  Action: MOTION -> PlayMusicAtDinnerTime                                       
  Action: SWITCH_TURNED_ON -> TurnOffAdjacentZones                              
  Action: TEMPERATURE_CHANGED -> AlertOnTemperatureOutOfRange                   
  Action: TIMER -> TellKidsToGoToBed                                            
                                                                                
  Neighbor: FF_Foyer, OPEN_SPACE                                                
  Neighbor: FF_GreatRoom, OPEN_SPACE_MASTER
Zone: Foyer, floor: FIRST_FLOOR, internal, displayIcon: groundfloor, displayOrder: 4, 6 devices
  AlarmPartition: FF_Foyer_AlarmPartition, armMode: ARM_STAY                    
  AstroSensor: VT_Time_Of_Day                                                   
  Door: FF_Foyer_Door                                                           
  Light: FF_Foyer_LightSwitch, duration: 5 mins, illuminance: 8, no premature turn-off time range: 0-23:59
  MotionSensor: FF_Foyer_LightSwitch_ClosetMotionSensor, battery powered        
  MotionSensor: FF_Foyer_LightSwitch_MotionSensor, battery powered              
                                                                                
  Action: MOTION -> TurnOnSwitch                                                
  Action: MOTION -> DisarmOnInternalMotion                                      
  Action: MOTION -> ManagePlugs                                                 
  Action: PARTITION_ARMED_AWAY -> ChangeThermostatBasedOnSecurityArmMode        
  Action: PARTITION_ARMED_AWAY -> ManagePlugs                                   
  Action: PARTITION_ARMED_AWAY -> TurnOffDevicesOnAlarmModeChange               
  Action: PARTITION_DISARMED_FROM_AWAY -> ChangeThermostatBasedOnSecurityArmMode
  Action: PARTITION_DISARMED_FROM_AWAY -> ManagePlugs                           
  Action: PARTITION_DISARMED_FROM_AWAY -> TurnOffDevicesOnAlarmModeChange       
  Action: SWITCH_TURNED_ON -> TurnOffAdjacentZones                              
  Action: TIMER -> ArmStayIfNoMovement                                          
  Action: TIMER -> ArmStayInTheNight                                            
  Action: TIMER -> ManagePlugs                                                  
                                                                                
  Neighbor: SF_Lobby, OPEN_SPACE                                                
  Neighbor: FF_Office, OPEN_SPACE_MASTER 
```


**Running on top of HABApp but with minimal dependency:**
> [The original Zone API modules](https://github.com/yfaway/openhab-rules/tree/master/legacy-jython-code)
> were written in Jython. It was recently migrated over to the [HABApp](https://habapp.readthedocs.io/en/latest/installation.html)
> framework with minimal changes needed to the core code. See [here](https://community.openhab.org/t/habapp-vs-jsr223-jython/112914)
> for the comparison between HABApp and JSR223 Jython.
> 
> There are 3 peripheral modules that are tightly coupled to the HABApp API. The rest of the modules
> is framework neutral. It is possible to migrate Zone API to another framework running on top of GravVM when 
> it is available. Zone API is now written in Python 3 and thus is not compatible with Jython
> (equivalent to Python 2.8).

# Set up your home automation system with zone_api

## 1. Name the OpenHab items using the default naming convention
```Zone_api``` comes with a default parser that builds the zone manager using a pre-defined naming convention. See the
ZoneParser section at the end of this page for details.

Here are a few sample .items files. Note that the file organization doesn't matter; all items can be defined in a single 
file if desired.

**zones.items**: defines two zones and their relationship.
```csv
String Zone_Office                                                                                  
  { level="FF", displayIcon="office", displayOrder="2",                                             
    openSpaceSlaveNeighbors="FF_Foyer" }
    
String Zone_Foyer                                                                                   
  { level="FF", displayIcon="groundfloor", displayOrder="4",                                        
    openSpaceMasterNeighbors="FF_Office",                                                           
    openSpaceNeighbors="SF_Lobby" }
```

**foyer.items**: defines the items in the Foyer zone.
```csv
Switch FF_Foyer_LightSwitch "Foyer Light" (gWallSwitch, gLightSwitch, gFirstFloorLightSwitch)       
  { channel="zwave:device:9e4ce05e:node2:switch_binary",                                            
    disableMotionTriggeringIfOtherLightIsOn="FF_Office_LightSwitch",                                
    durationInMinutes="5"}                                                                          
Switch FF_Foyer_LightSwitch_ClosetMotionSensor "Foyer Closet Motion Sensor"                         
  (gWallSwitchMotionSensor)                                                                         
  { channel="mqtt:topic:myBroker:xiaomiMotionSensors:FoyerMotionSensor"}                            
```

**office.items**: defines the items in the Office zone.
```csv
Switch FF_Office_LightSwitch "Office Light" (gWallSwitch, gLightSwitch, gFirstFloorLightSwitch)     
  [shared-motion-sensor]                                                                            
  { channel="zwave:device:9e4ce05e:node8:switch_binary",                                            
    durationInMinutes="15" }                                                                        
Switch FF_Office_LightSwitch_MotionSensor "Office Motion Sensor"                                    
  (gWallSwitchMotionSensor, gFirstFloorMotionSensors)                                               
  { channel="mqtt:topic:myBroker:xiaomiMotionSensors:OfficeMotionSensor"} 
```

That's it. Once the system is fully set up, ZoneApi's default actions will be registered automatically depending on
the available devices.

In the example above, the two zones have light switches and motion sensor. Thus the light rule is applicable and will
automatically turn on the light when a motion sensor is triggered, and turn it off if there is no activity for the
pre-defined duration. It will also turn off lights in the dependent zones.

## 2. Clone this repository
```git clone git@github.com:yfaway/zone-apis.git```

## 3. Install, configure, and run HABapp

Refer to the instructions on the [official HABApp website](https://habapp.readthedocs.io/en/latest/installation.html). The instruction below is specifically for the zone_api.
```bash
  sudo apt-get install python3-venv # to install python3-venv library
  cd zone_api # the cloned project in the section above
  python3 -m venv .
  source bin/activate # to get into our virtual environment
  python3 -m pip install --upgrade pip # to upgrade the pip library.
  python3 -m pip install habapp request schedule # request and schedule are required by zone_api
```

To manually run HABApp, execute this command within the ```zone_api``` folder:
```bash
  ./bin/habapp --config ./habapp/config.yml
```

The ```./habapp/rules``` folder contains the bootstrap [rule](https://github.com/yfaway/zone-apis/blob/master/habapp/rules/configure_zone_manager.py) to initialize the ```zone_api``` framework.
The rule is pretty simple with its entire content below.

```python
import HABApp

from zone_api import zone_parser as zp
from zone_api.core.devices.activity_times import ActivityType, ActivityTimes

class ConfigureZoneManagerRule(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.run_soon(self.configure_zone_manager)

    # noinspection PyMethodMayBeStatic
    def configure_zone_manager(self):
        time_map = {
            ActivityType.WAKE_UP: '6 - 9',
            ActivityType.LUNCH: '12:00 - 13:30',
            ActivityType.QUIET: '14:00 - 16:00, 20:00 - 22:59',
            ActivityType.DINNER: '17:50 - 20:00',
            ActivityType.SLEEP: '23:00 - 7:00',
            ActivityType.AUTO_ARM_STAY: '20:00 - 2:00',
            ActivityType.TURN_OFF_PLUGS: '23:00 - 2:00',
        }
        zone_manager = zp.parse(ActivityTimes(time_map))

ConfigureZoneManagerRule()
```
The code above defines an ActivityTimes object with various activity time periods and pass it over
to the [zone_parser](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/zone_parser.py)
module. The zone_parser parses the OpenHab items following a specific naming pattern, and construct
the zones and the devices / sensors. It then registers the handlers for the events associated with
the devices / sensors. Finally, it loads all the actions and add them to the zones based on the
pre-declared execution rules associated with each action (more on this later). That's it; from this point
forward, events generated by the devices / sensors will trigger the associated actions.

It is important to note that the zone_parser is just a default mechanism to build the ZoneManager.
A custom module can be used to parse from a different naming pattern for the OpenHab items, or the ZoneManager can
be constructed manually. The role of the parser is no longer needed once the ZoneManager has been
built.

# ZoneManager
Contains a set of zones and is responsible for dispatching the events to the zones.

# Zone
Contains a set of devices, actions, and is responsible for dispatching the events to the actions.

A zone is aware of its neighbors. Certain rules such as the [turning on/off of the lights](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/actions/turn_on_switch.py)
is highly dependent on the layout of the zones. The following [neighbor](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/neighbor.py)
types are available.
1. ```CLOSED_SPACE```
2. ```OPEN_SPACE```
3. ```OPEN_SPACE_MASTER```
4. ```OPEN_SPACE_SLAVE```

# Devices
The [devices](https://github.com/yfaway/zone-apis/tree/master/src/zone_api/core/devices)
contains one or more underlying OpenHab items. Rather than operating on a SwitchItem or on a
NumberItem, the device represents meaningful concrete things such as a [MotionSensor](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/devices/motion_sensor.py),
or a [Light](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/devices/switch.py).
Devices contain both attributes (e.g. 'is the door open') and behaviors (e.g. 'arm the security
system').

# Events
Similar to the abstraction for the devices, the events are also more concrete. Zone API maps the
OpenHab items events to the event enums in [ZoneEvent](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/zone_event.py)
such as ```ZoneEvent.HUMIDITY_CHANGED``` or ```ZoneEvent.PARTITION_ARMED_AWAY```.
There is also the special event ```ZoneEvent.TIMER``` that represents triggering from a scheduler.

The event is dispatched to the appropriate zones which then invokes the actions registered for that
event. See [EventInfo](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/event_info.py)
for more info.

# Actions
All the [actions](https://github.com/yfaway/zone-apis/tree/master/src/zone_api/core/actions) implement the [Action](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/action.py) interface.
The action's life cycle is represented by the three functions: 
1. ```on_startup()``` - invoked after the ZoneManager has been fully populated, via the event
   ```ZoneEvent.STARTUP```.
2. ```on_action()``` - invoked where the device generates an event or when a timer event is
   triggered (via ```ZoneEvent.TIMER```).
3. ```on_destroy()``` - currently not invoked.

The ```@action``` decorator provides execution rules for the action as well as basic validation.
If the condition (based on the execution rules) does not match, the action won't be executed.
Below are the currently supported decorator parameters:
1. *devices* - the list of devices the zone must have in order to invoke the action.
2. *events* - the list of events for which the action will response to.
3. *internal* - if set, this action is only applicable for internal zone
4. *external* - if set, this action is only applicable for external zone
5. *levels* - the zone levels that this action is applicable to. the empty list default value indicates that the action is applicable to all zone levels.
6. *unique_instance* - if set, do not share the same action instance across zones. This is the case when the action is stateful.
7. *zone_name_pattern* - if set, the zone name regular expression that is applicable to this action.
8. *external_events* - the list of events from other zones that this action processes. These events won't be filtered using the same mechanism as the internal events as they come from other zones.
9. *priority* - the action priority with respect to other actions within the same zone. Actions with lower priority values are executed first.

These parameters are also available to the action and can be used as a filtering mechanism
to make sure that the action is only added to the applicable zones.

Here is a simple action to disarm the security system when a motion sensor is triggered:

```python
from zone_api import security_manager as sm
from zone_api.core.devices.activity_times import ActivityTimes
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action
from zone_api.core.devices.alarm_partition import AlarmPartition


@action(events=[ZoneEvent.MOTION], devices=[AlarmPartition, MotionSensor])
class DisarmOnInternalMotion:
    """
    Automatically disarm the security system when the motion sensor in the zone containing the
    security panel is triggered and the current time is not in the auto-arm-stay or sleep
    time periods.
    """

    def on_action(self, event_info):
        events = event_info.get_event_dispatcher()
        zone_manager = event_info.get_zone_manager()

        if not sm.is_armed_stay(zone_manager):
            return False

        activity = zone_manager.get_first_device_by_type(ActivityTimes)
        if activity is None:
            self.log_warning("Missing activities time; can't determine wake-up time.")
            return False

        if activity.is_auto_arm_stay_time() or (activity.is_sleep_time() and not activity.is_wakeup_time()):
            return False

        sm.disarm(zone_manager, events)
        return True
```

The decorator for the action above indicates that it is triggered by the motion event, and should
only be added to a zone that contains both the AlarmPartition and the Motion devices.

# ZoneParser
The default parser uses this naming pattern for the OpenHab items.

 1. The zones are defined as a String item with this pattern Zone_{name}:
    
        String Zone_GreatRoom                                                           
            { level="FF", displayIcon="player", displayOrder="1",                         
              openSpaceSlaveNeighbors="FF_Kitchen" } 
      - The levels are the reversed mapping of the enums in Zone::Level.
      - Here are the list of supported attributes: level, external, openSpaceNeighbors,
        openSpaceMasterNeighbors, openSpaceSlaveNeighbors, displayIcon, displayOrder.
       
 2. The individual OpenHab items are named after this convention: ```{zone_id}_{device_type}_{device_name}```.
    
    Here's an example:
    
        Switch FF_Office_LightSwitch "Office Light" (gWallSwitch, gLightSwitch, gFirstFloorLightSwitch)
            [shared-motion-sensor]                                                        
            { channel="zwave:device:9e4ce05e:node8:switch_binary",                        
              durationInMinutes="15" }                                                    

See here for a [sample .items](https://github.com/yfaway/openhab-rules/blob/master/items/switch-and-plug.items)
file that is parsable by ZoneParser.
