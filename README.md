# Zone API - an alternative approach to access devices / sensors       
In OpenHab, items are defined in a flat manner in .items files under the /etc/openhab2/items folder.
They are typically linked to a channel exposed by the underlying hardware (virtual items do not link
to any).
                                                                                
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
rule is highly coupled to the naming patern.
                                                                                
The [Zone API](https://github.com/yfaway/zone-apis) provides another approach. It provides a layer
above the devices / sensors. Each [ZoneManager](https://github.com/yfaway/zone-apis/blob/master/zone_apis/aaa_modules/layout_model/immutable_zone_manager.py)
(i.e. a house) contains multiple [zones](https://github.com/yfaway/zone-apis/blob/master/zone_apis/aaa_modules/layout_model/zone.py)
(i.e. rooms), and each zone contains multiple [devices](https://github.com/yfaway/zone-apis/tree/master/zone_apis/aaa_modules/layout_model/devices).
Each zone is associated with a set of [actions](https://github.com/yfaway/zone-apis/tree/master/zone_apis/aaa_modules/layout_model/actions) 
that are triggered by certain [events](https://github.com/yfaway/zone-apis/blob/master/zone_apis/aaa_modules/layout_model/zone_event.py).
The usual OpenHab events are routed in this manner:

`OpenHab events --> ZoneManager --> Zones --> Actions`

It provides a level of abstraction on top of the raw items. The actions can operate on the abstract
devices and do not concern about the naming of the items or the underlying hardware. The actions
replace the traditional OpenHab rules. Actions can be unit-tested with various levels of mocking.

**Most importantly, it enables reusing of action logics.** Why would everyone have to re-write the
same set of logic for turning on/off lights again and again. All ones need to do is to populate
the zones and devices / sensors, and the applicable actions will be added and processed
automatically.

# Running on top of HABApp but with minimal dependency
[The original Zone API modules](https://github.com/yfaway/openhab-rules/tree/master/legacy-jython-code)
were written in Jython. It was recently migrated over to the HABApp framework with minimal changes
needed to the core code. See [here](https://community.openhab.org/t/habapp-vs-jsr223-jython/112914) for the comparison between HABApp and JSR223 Jython.

There are 3 peripheral modules that are tightly coupled to the HABApp API. The rest of the modules
is framework neutral. It is possible to migrate Zone API to another framework such as GravVM when 
it is available. Zone API is written in Python 3 and thus is not compatible with Jython (equivalent
to Python 2.8).

# The bootstrap rule for the framework
Here is [an example](https://github.com/yfaway/zone-apis/blob/master/habapp/rules/configure_zone_manager.py) of the only HABApp rule needed to initialize the system.
```python
import HABApp

from aaa_modules import zone_parser as zp
from aaa_modules.layout_model.devices.activity_times import ActivityType, ActivityTimes

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
to the [zone_parser](https://github.com/yfaway/zone-apis/blob/master/zone_apis/aaa_modules/zone_parser.py)
module. The zone_parser parses the OpenHab items following a specific naming pattern, and construct
the zones and the devices / sensors. It then registers the handlers for the events associated with
the devices / sensors. Finally, it loads all the actions and add them to the zones based on the
pre-declared rules associated with each action (more on this later). That's it; from this point
forward, events generated by the devices / sensors will trigger the associated actions.

It is important to note that the zone_parser is just a default mechanism to build the ZoneManager.
Another module can be used to parser from a different OpenHab naming pattern, or the ZoneManager can
be constructed manually. The role of the parser is no longer needed once the ZoneManager has been
built.

# Zone

# Devices
The [devices](https://github.com/yfaway/zone-apis/tree/master/zone_apis/aaa_modules/layout_model/devices)
contains one or more underlying OpenHab items. Rather than operating on a SwitchItem or on on
NumberItem, the device represents meaningful concrete things such as a [MotionSensor](https://github.com/yfaway/zone-apis/blob/master/zone_apis/aaa_modules/layout_model/devices/motion_sensor.py),
or a [Light](https://github.com/yfaway/zone-apis/blob/master/zone_apis/aaa_modules/layout_model/devices/switch.py).
Devices contain both attributes (such as 'is the door open') and behaviors (such as 'arm the security
system').

# Actions

# Events