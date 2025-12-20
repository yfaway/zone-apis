
<!-- vim-markdown-toc GFM -->

* [Quick intro and setup instructions](#quick-intro-and-setup-instructions)
    * [1. Install the libraries](#1-install-the-libraries)
    * [2. Configure HABapp](#2-configure-habapp)
    * [3. Create the zone-api configuration file.](#3-create-the-zone-api-configuration-file)
    * [4. Create a HABapp rule to integrate with ZoneApi.](#4-create-a-habapp-rule-to-integrate-with-zoneapi)
    * [5. Change OpenHab item names to patterns recognized by the default Zone API parser](#5-change-openhab-item-names-to-patterns-recognized-by-the-default-zone-api-parser)
    * [6. Start HABapp and observe the action via the log file](#6-start-habapp-and-observe-the-action-via-the-log-file)
* [Zone API - an alternative approach to writing rules](#zone-api---an-alternative-approach-to-writing-rules)
* [Core concepts and API](#core-concepts-and-api)
    * [ZoneManager](#zonemanager)
    * [Zone](#zone)
    * [Devices](#devices)
    * [Events](#events)
    * [Actions](#actions)
    * [ZoneParser and the default OpenHab item naming conventions](#zoneparser-and-the-default-openhab-item-naming-conventions)
        * [OpenHab zone items](#openhab-zone-items)
        * [OpenHab device items](#openhab-device-items)
            * [Astro sensor](#astro-sensor)
            * [Computer](#computer)
            * [Ecobee thermostat](#ecobee-thermostat)
            * [Light switches](#light-switches)
            * [Fan switches](#fan-switches)
            * [Motion sensors](#motion-sensors)
            * [Light sensors](#light-sensors)
            * [Plugs](#plugs)
            * [Security alarm](#security-alarm)
            * [Doors](#doors)
            * [Windows](#windows)
            * [Humidity sensors](#humidity-sensors)
            * [Temperature sensors](#temperature-sensors)
            * [Natural gas sensors](#natural-gas-sensors)
            * [CO2 sensors](#co2-sensors)
            * [Smoke sensors](#smoke-sensors)
            * [Google Chromecasts](#google-chromecasts)
            * [Network presences](#network-presences)
            * [Televisions](#televisions)
            * [Water leak sensors](#water-leak-sensors)
            * [Weather](#weather)
* [Common services](#common-services)
    * [Alert](#alert)

<!-- vim-markdown-toc -->

# Quick intro and setup instructions
This framework contains a set of reusable rules for OpenHab. It contains the following components:
1. The item definitions and bindings in OpenHab.
2. The [HABApp](https://habapp.readthedocs.io/en/latest/installation.html) process that communicates with OpenHab via
   the REST API. 
3. This Zone API Python library, integrated with HABapp via a single HABApp rule.

It is a more complicated architecture compared to having everything running within OpenHab process,
but on the other hand, we can use Python 3 libraries. See [here](https://community.openhab.org/t/habapp-vs-jsr223-jython/112914)
for the comparison between HABApp and JSR223 Jython.

## 1. Install the libraries
```bash
  sudo apt-get install python3-venv # to install python3-venv library
  python3 -m venv my-home # this will create 'my-home' folder
  cd my-home
  source bin/activate
  python3 -m pip install zone-api # this will install zone-api and its dependencies including HABapp
```

Refer to the instructions on the [official HABApp website](https://habapp.readthedocs.io/en/latest/installation.html).
for additional clarifications.

## 2. Configure HABapp
First run the following commands within the `my-home` folder to start HABapp and to generate the HABapp configuration
files.
```bash
  mkdir habapp
  ./bin/habapp --config habapp/ # HABapp will create the config.yml and logging.yml files.
```

Now that the config files have been created, press Ctrl-C to kill HABapp. We will change the following 4 values in
`config.yml` file to specify the OpenHab server.
```
  host: localhost  # the OpenHab server IP address
  port: 8080                                                                  
  user: ''         # the OpenHab3 username
  password: ''     # the OpenHab3 password
```

Next, add a new logger for Zone API to the file `logging.xml` under the section "**loggers:**".
```
  ZoneApis:                                                                     
    level: INFO                                                                 
    handlers:                                                                   
      - HABApp_default                                                          
    propagate: False 
```

See [the HABApp website](https://habapp.readthedocs.io) for additional detail.

## 3. Create the zone-api configuration file.
Create the file `my-home/habapp/zone-api-config.yml` with the content below:
```yaml
system:
  activity-times:
    wakeup: '6:35 - 9'
    lunch: '12:00 - 13:30'
    quiet: '20:00 - 22:59'
    dinner: '17:50 - 20:00'
    sleep: '23:00 - 7:00'
    auto-arm-stay: '20:00 - 2:00'
    turn-off-plugs: '23:00 - 2:00'

  email-service:
    smtp-server: smtp.gmail.com
    port: 465
    sender-email: sender@gmail.com
    sender-password: password

  alerts:
    email:
      owner-email-addresses:
        - recipient@gmail.com
      admin-email-addresses:
        - recipient@gmail.com

# Contains the parameters for each named actions.
action-parameters:
  AlertOnBadComputerStates:
    maxCpuTemperatureInDegree: 60
```
The latest version of this file can be found [here](https://github.com/yfaway/zone-apis/blob/master/habapp/zone-api-config.yml).

All actions support the following parameters:
- disabled: true | false
- notificationAudiences: "administrators" or "owners"

## 4. Create a HABapp rule to integrate with ZoneApi.
Next create the file `configure_zone_manager.py` under `my-home/habapp/rules` (HABapp created this folder earlier). Copy
the following content into that file.
```python
import HABApp
import os
import yaml

from zone_api import zone_parser as zp
from zone_api import platform_encapsulator as pe


class ConfigureZoneManagerRule(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.run.soon(self.configure_zone_manager)

    # noinspection PyMethodMayBeStatic
    def configure_zone_manager(self):
        config_file = './habapp/zone-api-config.yml'
        if not os.path.exists(config_file):
            raise ValueError("Missing zone-api-config.yml file.")

        pe.log_info(f"Reading zone-api configuration from '{config_file}'")

        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

        zm = zp.parse(config)
        pe.add_zone_manager_to_context(zm)

        pe.log_info(str(pe.get_zone_manager_from_context()))


ConfigureZoneManagerRule()
```
This is the only rule that is needed to bootstrap the framework. It reads the configuration from the yaml file in the
section above.
The latest version of this file can be found [here](https://github.com/yfaway/zone-apis/blob/master/habapp/rules/configure_zone_manager.py).

## 5. Change OpenHab item names to patterns recognized by the default Zone API parser
Let's adjust the OpenHab items files to something like this:
```
String Zone_Office { level="FF" }
Switch FF_Office_LightSwitch "Office Light"
  { channel="zwave:device:9e4ce05e:node8:switch_binary",                                            
    durationInMinutes="15" }                                                                        
Switch FF_Office_LightSwitch_MotionSensor "Office Motion Sensor"                                    
  { channel="mqtt:topic:myBroker:xiaomiMotionSensors:OfficeMotionSensor"}
```
Zone API groups items into devices and organizes devices into zones. The items above define a zone names `Office` on the
first floor (`FF` abbreviation). The next two items define a [Light](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/devices/switch.py)
device and a [MotionSensor](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/devices/motion_sensor.py)
in the `Office` zone (via the convention `FF_Office` prefix).

## 6. Start HABapp and observe the action via the log file
Restart HABapp with `./bin/habapp --config habapp/` and then monitor the HABapp activity via `tail -F habapp/log/HABApp.log`.
You should see something like this:
```
[2021-06-20 22:42:06,155] [             HABApp.Rules]     INFO | Added rule "ConfigureZoneManagerRule" from rules/configure_zone_manager.py
Zone: Office, floor: FIRST_FLOOR, internal, 2 devices
  Light: FF_Office_LightSwitch, duration: 15 minutes, illuminance: 8
  MotionSensor: FF_Office_LightSwitch_MotionSensor, battery powered

  Action: MOTION -> TurnOnSwitch
  Action: SWITCH_TURNED_ON -> TurnOffAdjacentZones
```

Based on the zone attributes, and the devices available, certain actions will be enabled. In this case, the action
`TurnOnSwitch` and `TurnOffAdjacentZones` are triggered on the `MOTION` and `SWITCH_TURNED_ON` events. At this point
you have light management including turning on the light when the motion sensor triggers, and a timer to turn off the
light after 15 minutes of idle. You have just re-used a rule!

See [here](https://github.com/yfaway/zone-apis/tree/master/src/zone_api/core/devices) for the full list of supported
devices, and [here](https://github.com/yfaway/zone-apis/tree/master/src/zone_api/core/actions) for the list of built-in
actions.

The rest of this document goes into the rationale and design of the library.

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

The actions operate on the abstract devices and do not concern about the specific naming of the items or
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


**Running on top of HABApp:**
> [The original Zone API modules](https://github.com/yfaway/openhab-rules/tree/master/legacy-jython-code)
> were written in Jython. It was then migrated over to the [HABApp](https://habapp.readthedocs.io/en/latest/installation.html)
> framework with minimal changes needed to the core code. See [here](https://community.openhab.org/t/habapp-vs-jsr223-jython/112914)
> for the comparison between HABApp and JSR223 Jython.
> 
> There are several peripheral modules that are tightly coupled to the HABApp API. The rest of the modules
> is framework neutral. It is possible to migrate Zone API to another framework running on top of GravVM when it is
> available. Zone API is now written in Python 3 and thus is not compatible with Jython (equivalent to Python 2.8).

# Core concepts and API
## ZoneManager
Contains a set of zones and is responsible for dispatching the events to the zones.

## Zone
Contains a set of devices, actions, and is responsible for dispatching the events to the actions.

A zone is aware of its neighbors. Certain rules such as the [turning on/off of the lights](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/actions/turn_on_switch.py)
is highly dependent on the layout of the zones. The following [neighbor](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/neighbor.py)
types are available.
1. ```CLOSED_SPACE```
2. ```OPEN_SPACE```
3. ```OPEN_SPACE_MASTER```
4. ```OPEN_SPACE_SLAVE```

## Devices
The [devices](https://github.com/yfaway/zone-apis/tree/master/src/zone_api/core/devices)
contains one or more underlying OpenHab items. Rather than operating on a SwitchItem or on a
NumberItem, the device represents meaningful concrete things such as a [MotionSensor](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/devices/motion_sensor.py),
or a [Light](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/devices/switch.py).
Devices contain both attributes (e.g. 'is the door open') and behaviors (e.g. 'arm the security
system').

## Events
Similar to the abstraction for the devices, the events are also more concrete. Zone API maps the
OpenHab items events to the event enums in [ZoneEvent](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/zone_event.py)
such as ```ZoneEvent.HUMIDITY_CHANGED``` or ```ZoneEvent.PARTITION_ARMED_AWAY```.
There is also the special event ```ZoneEvent.TIMER``` that represents triggering from a scheduler.

The event is dispatched to the appropriate zones which then invokes the actions registered for that
event. See [EventInfo](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/event_info.py)
for more info.

## Actions
All the [actions](https://github.com/yfaway/zone-apis/tree/master/src/zone_api/core/actions) implement the [Action](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/core/action.py) interface.
The action's life cycle is represented by the three functions: 
1. ```on_startup()``` - invoked after the ZoneManager has been fully populated, via the event
   ```ZoneEvent.STARTUP```.
2. ```on_action()``` - invoked where the device generates an event or when a timer event is
   triggered (via ```ZoneEvent.TIMER```).
3. ```on_destroy()``` - currently not invoked.

The ```@action``` decorator provides execution rules for the action as well as basic validations.
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
10. *activity_types* - the list of ActivityType that the action can trigger. If the current time is not in the
time range of one of these activities, the action won't trigger.
11. *excluded_activity_types* - the list of ActivityType that the action won't trigger. If the current time is in
    the time range of one of these activities, the action won't trigger.

These parameters are also available to the action and can be used as a filtering mechanism
to ensure that the action is only added to the applicable zones. See [ZoneParser::add_actions](https://github.com/yfaway/zone-apis/blob/dc3894780a1715b8845460be87ffff5c0c219afa/src/zone_api/zone_parser.py#L176).

Here is a simple action to disarm the security system when a motion sensor is triggered:

```python
from zone_api import security_manager as sm
from zone_api.core.devices.activity_times import ActivityTimes
from zone_api.core.devices.motion_sensor import MotionSensor
from zone_api.core.zone_event import ZoneEvent
from zone_api.core.action import action, Action
from zone_api.core.devices.alarm_partition import AlarmPartition


@action(events=[ZoneEvent.MOTION], devices=[AlarmPartition, MotionSensor])
class DisarmOnInternalMotion(Action):
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

Actions can read parameters from the ```zone-api-config.yml``` file (see section 3 above).

Parameters available to all actions:
 - disabled (optional boolean; default: false): if set to true, the action is excluded from all zones. This parameter
   is useful to disable certain actions, either temporarily or permanently when importing a large number of external actions from a library.
 - notificationAudiences (optional string; default: 'users'): configure whether the notification (if any) should go to
   regular users or the administrators. To take advantage of this parameter, actions need to use
  ```Action::send_notification(zone_manager, alert)```. Possible values: 'users', or 'administrators'.
  
Each actions might also have their own parameters; see the method ```supported_parameters``` in each action.

## ZoneParser and the default OpenHab item naming conventions
This is the default parser that retrieves items from OpenHab and creates the appropriate zones and 
devices based on specific naming conventions. Note that this is just a default parser, it is 
possible to create zones and devices using a different naming convention, or even manually. The
Zone API is not dependent on any specific naming pattern.

See [sample.items](https://github.com/yfaway/openhab-rules/blob/master/items/) files that is
parsable by ZoneParser.

### OpenHab zone items
The zones are defined as a String items with this pattern Zone_{name}:
```    
String Zone_GreatRoom                                                           
    { level="FF", displayIcon="player", displayOrder="1", openSpaceSlaveNeighbors="FF_Kitchen" } 
```
The levels are the reversed mapping of the enums in Zone::Level.

Here are the list of supported attributes:
* level: reversed mapping of the enums in Zone::Level. 'FF', 'SF', 'TF', 'BM' for first floor,
  second floor, third floor, basement.
* external: 'true' or 'false'
* openSpaceNeighbors: a list of open space adjacent zone ids such as 'FF_Kitchen', where 'FF' is
  the level and 'Kitchen' is the zone name.
* openSpaceMasterNeighbors: a list of adjacent master zone ids. When a master zone's light is
  turned on, all the slave zones' light will be turned off.
* openSpaceSlaveNeighbors: a list of adjacent slave zone ids.
* displayIcon: an OpenHab icon name.
* displayOrder: an integer; the lower the value the higher the order.
       
### OpenHab device items
The individual OpenHab items are named after this convention: ```{zone_id}_{device_type}_{device_name}```.

For the full list of supported devices, see [ZoneParser](https://github.com/yfaway/zone-apis/blob/master/src/zone_api/zone_parser.py#L57).

To see the functions supported by each device, view the [device classes](https://github.com/yfaway/zone-apis/tree/master/src/zone_api/core/devices).

#### Astro sensor
Pattern: `[^g].*_TimeOfDay$`

This is a virtual device that rely on the Time of Day rule and the Astro binding.

Example:
```
String FF_Virtual_TimeOfDay "Current Time of Day [%s]""]"
```

#### Computer
Pattern: `.*_Computer_[^_]+$`

Supported attributes:
* name: the computer name.
* alwaysOn: a 'true' or 'false' value that indicates if the computer is ON all the time.

Additional items are derived from the primary item name with the following additional suffix:
"_CpuTemperature", "_GpuTemperature", "_GpuFanSpeed".

Example:
```
String FF_Office_Computer_Dell
  { name="Dell G5", alwaysOn="true" }
Number FF_Office_Computer_Dell_GpuFanSpeed "Dell GPU Fan Speed [%d %%]"
  { channel="mqtt:topic:myBroker:office:dellG5GfxFanSpeed", autoReport="true" }
Number FF_Office_Computer_Dell_GpuTemperature "Dell GPU Temperature [%d °C]"
  { channel="mqtt:topic:myBroker:office:dellG5GfxTemperature", autoReport="true" }
DateTime FF_Office_Computer_Dell_UpdatedTimestamp "Dell Last Updated [%1tb %1$td %1$tY %1$tH:%1$tM]"
  { channel="mqtt:topic:myBroker:office:dellUpdatedTimestamp", autoReport="true" }
```

#### Ecobee thermostat
Pattern: `.*_Thermostat_EcobeeName$`

Example:
```
```

#### Light switches
Pattern: `[^g].*LightSwitch.*`

Additional firstEvent item is retrieved by replacing the word "EcobeeName" by "FirstEvent_Type"
in the primary item name.

Example:
```
String FF_GreatRoom_Thermostat_EcobeeName "Name [%s]"                                               
  { channel="ecobee:thermostat:account:411222197263:info#name" }
String FF_GreatRoom_Thermostat_FirstEvent_Type "First Event Type [%s]"                              
  { channel="ecobee:thermostat:account:411222197263:events#type" }
```

Supported attributes:
* durationInMinutes: numeric value.
* disableTriggeringFromMotionSensor: 'true' or 'false'; false if not present. 
* noPrematureTurnOffTimeRange: time range string such as '7-9' or 7 AM to 9AM; don't turn of the
  light on timer expires during these period.
* dimmable: complex structure to map the lux with a time ranges.
  E.g.: `dimmable="true" [level=2, timeRanges="20-8"]`

Example:
```    
Switch FF_Office_LightSwitch "Office Light" (gWallSwitch, gLightSwitch, gFirstFloorLightSwitch)
  [shared-motion-sensor]                                                        
  { channel="zwave:device:9e4ce05e:node8:switch_binary",                        
  durationInMinutes="15" }                                                    
```

#### Fan switches
Pattern: `.*FanSwitch.*`

Supported attributes: same as with the light switches.

#### Motion sensors
Pattern: `[^g].*MotionSensor$`

Example:
```
Switch SF_Lobby_LightSwitch_MotionSensor "Second Floor Lobby Motion Sensor"                         
  { channel="mqtt:topic:myBroker:xiaomiMotionSensors:SecondFloorLobbyMotionSensor"}
```

#### Light sensors
Pattern: `[^g].*_Illuminance.*`

Example: `Number SF_Lobby_LightSwitch_Illuminance { channel="..." }`

#### Plugs
Pattern: `[^g].*_Plug$`

Additional optional power reading item with the primary item name + "_Power".

Example:
```
Switch FF_Office_Plug "Office Plug"                                                                 
  { alwaysOn="true", channel="tplinksmarthome:hs110:office:switch"}                                 
Number FF_Office_Plug_Power "Office Plug Power [%d Watts]" (gPlugPower)                             
  { channel="tplinksmarthome:hs110:office:power"}
```

#### Security alarm
Pattern: `.*AlarmPartition$`

Additional arm mode item: via the primary item name + the suffix '_ArmMode'.

Example:
```
Switch FF_Foyer_AlarmPartition                                                                      
  {channel="dscalarm:partition:706cd89d:partition1:partition_in_alarm"}                             
Number FF_Foyer_AlarmPartition_ArmMode                                                              
  {channel="dscalarm:partition:706cd89d:partition1:partition_arm_mode"}
```
#### Doors
Pattern: `.*Door$`

Examples:
```
Switch FF_Porch_Door {channel="dscalarm:zone:706cd89d:zone1:zone_tripped"}
```

#### Windows
Pattern: `[^g].*_Window$`

#### Humidity sensors
Pattern: `[^g](?!.*Weather).*Humidity$`

Example:
```
Number SF_Bedroom2_Humidity "Bedroom2 Humidity [%d %%]"                                             
  { channel="mqtt:topic:myBroker:bedroom2:humidity", wifi="true", autoReport="true" }  
```

#### Temperature sensors
Pattern: `[^g](?!.*Computer)(?!.*Weather).*Temperature$`

Example:
```
Number SF_Bedroom2_Temperature "Bedroom2 Temperature [%.1f °C]"                                     
  { channel="mqtt:topic:myBroker:bedroom2:temperature", wifi="true", autoReport="true" }
```

#### Natural gas sensors
Pattern: `[^g].*_NaturalGas$`

Additional state item using the primary name + "State" suffix.

Example:
```
Number BM_Utility_NaturalGas "Natural Gas Value [%d]"                                               
  { channel="mqtt:topic:myBroker:utilityRoom:naturalGasValue", wifi="true", autoReport="true" }                                                                
                                                                                                    
Switch BM_Utility_NaturalGasState "Natural Gas Detected [%s]"                                       
  { channel="mqtt:topic:myBroker:utilityRoom:naturalGasState", wifi="true", autoReport="true" }
```

#### CO2 sensors
Pattern: `[^g].*_Co2$`

Otherwise similar to Natural Gas Sensors.

#### Smoke sensors
Pattern: `[^g].*_Smoke$`

Otherwise similar to Natural Gas Sensors.

#### Google Chromecasts
Pattern: `.*_ChromeCast$`

Supported attributes:
* sinkName: string value; additional items are retrieved via this name.

Examples:
```
String FF_GreatRoom_ChromeCast { sinkName = "chromecast:audio:greatRoom" }                          
                                                                                                    
String FF_GreatRoom_ChromeCastStreamTitle "Stream [%s]"                                             
Player FF_GreatRoom_ChromeCastPlayer "Player" (gCastPlayer)                                         
  { channel="chromecast:audio:greatRoom:control" }                                                  
Dimmer FF_GreatRoom_ChromeCastVolume "Volume" (gCastVolume)                                         
  { channel="chromecast:audio:greatRoom:volume" }                                                   
String FF_GreatRoom_ChromeCastPlayUri "Play URI [%s]"                                               
  { channel="chromecast:audio:greatRoom:playuri" }                                                  
Switch FF_GreatRoom_ChromeCastIdling "Idling"                                                       
  { channel="chromecast:audio:greatRoom:idling" }     
```



#### Network presences
Pattern: `[^g].*_NetworkPresence.*`

Example:
```
Switch FF_Virtual_NetworkPresenceOwner1Phone "Owner1's Phone"
  { channel="network:pingdevice:192_168_0_100:online" } 
```

#### Televisions
Pattern: `.*_Tv$`

Only support determining if the TV is on.

Example:
```
Switch FF_GreatRoom_Tv "TV" {channel="sony:scalar:15611113d7d2:system#powerstatus"}
```

#### Water leak sensors
Pattern: `[^g].*WaterLeakState$`

Example:
```
Switch BM_Utility_WaterLeakState "Water Leak Detected [%s]"
  { channel="mqtt:topic:myBroker:utilityRoom:leakSensorState" }
```

#### Weather

Pattern: `.*_Weather_Temperature$`

Additional items are retrieved using the various suffixes.

Example:
```
Number:Temperature FF_Virtual_Weather_Temperature "Temperature [%.1f %unit%]" (gWeather)            
  { channel="ecobee:thermostat:account:411222197263:forecast0#temperature" }                        
String FF_Virtual_Weather_Condition "Condition [%s]" (gWeather)                                     
  { channel="ecobee:thermostat:account:411222197263:forecast0#condition" }                          
Number FF_Virtual_Weather_Humidity "Relative Humidity [%d %%]" (gWeather)                           
  { channel="ecobee:thermostat:account:411222197263:forecast0#relativeHumidity" }                   
DateTime FF_Virtual_Weather_LastUpdate "Last update [%1$tA, %1$tm/%1$td/%1$tY %1$tl:%1$tM %1$tp]"
  { channel="ecobee:thermostat:account:411222197263:weather#timestamp" }
Number:Temperature FF_Virtual_Weather_ForecastTempMin "Forecast Min Temperature [%.1f %unit%]"      
  { channel="ecobee:thermostat:account:411222197263:forecast0#tempLow" }                            
Number:Temperature FF_Virtual_Weather_ForecastTempMax "Forecast Max Temperature [%.1f %unit%]"      
  { channel="ecobee:thermostat:account:411222197263:forecast0#tempHigh" }
String FF_Virtual_Weather_Alert_Title "Alert [%s]"                                                
  {channel="feed:feed:envCanada:latest-title"}
```
# Common services
## Alert
This is a common service to send various notifications such as security violation or temperature / humidity getting too
high. The actions just need to classify whether an alert is info, warning, or critical. The service will provide
appropriate implementation.

Currently three mechanisms are supported:
1. Email: send an email notification to either the owners or the administrators.
   See [zone-api-config.yml](https://github.com/yfaway/zone-apis/blob/master/habapp/zone-api-config.yml) for more info.

2. Audio: send a text-to-speed (TTS) to one or more connected audio devices. The volume is set based on the criticality
   of the alert.

3. Light: if a critical alert occurs during the night, the internal lights are turned on.
