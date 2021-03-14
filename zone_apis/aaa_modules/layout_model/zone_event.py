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
    DOOR_OPEN = 6  # A door is open
    DOOR_CLOSED = 7  # A door is close
    WINDOW_OPEN = 8  # A window is open
    WINDOW_CLOSED = 9  # A window is close
    PARTITION_ARMED_AWAY = 10  # Changed to armed away
    PARTITION_ARMED_STAY = 11  # Changed to armed stay
    PARTITION_RECEIVE_ARM_AWAY = 12  # Changed to armed away
    PARTITION_RECEIVE_ARM_STAY = 13  # Changed to armed stay
    PARTITION_DISARMED_FROM_AWAY = 14  # Changed from armed away to disarm
    PARTITION_DISARMED_FROM_STAY = 15  # Changed from armed stay to disarm
    HUMIDITY_CHANGED = 16  # The humidity percentage changed
    TEMPERATURE_CHANGED = 17  # The temperature changed
    GAS_TRIGGER_STATE_CHANGED = 18  # The gas sensor triggering boolean changed
    GAS_VALUE_CHANGED = 19  # The gas sensor value changed
    WATER_LEAK_STATE_CHANGED = 20  # The water leak sensor state changed

    TIMER = 98  # A timer event is triggered.
    STARTUP = 99  # action startup event
    DESTROY = 100  # action destroy event
