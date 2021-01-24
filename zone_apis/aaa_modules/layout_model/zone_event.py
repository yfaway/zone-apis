from enum import unique, Enum


@unique
class ZoneEvent(Enum):
    """ An enum of triggering zone events. """

    UNDEFINED = -1  # Undefined
    MOTION = 1  # A motion triggered event
    SWITCH_TURNED_ON = 2  # A switch turned-on event
    SWITCH_TURNED_OFF = 3  # A switch turned-on event
    CONTACT_OPEN = 4  # A contact (doors/windows) is open
    CONTACT_CLOSED = 5  # A contact (doors/windows) is close
    PARTITION_ARMED_AWAY = 6  # Changed to armed away
    PARTITION_ARMED_STAY = 7  # Changed to armed stay
    PARTITION_DISARMED_FROM_AWAY = 8  # Changed from armed away to disarm
    PARTITION_DISARMED_FROM_STAY = 9  # Changed from armed stay to disarm
    HUMIDITY_CHANGED = 10  # The humidity percentage changed
    TEMPERATURE_CHANGED = 11  # The temperature changed
    GAS_TRIGGER_STATE_CHANGED = 12  # The gas sensor triggering boolean changed
    GAS_VALUE_CHANGED = 13  # The gas sensor value changed

    TIMER = 98  # A timer event is triggered.
    STARTUP = 99  # action startup event
    DESTROY = 100  # action destroy event
