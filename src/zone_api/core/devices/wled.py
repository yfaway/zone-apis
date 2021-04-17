import random
from threading import Timer
from typing import Dict

from zone_api import platform_encapsulator as pe
from zone_api.core.devices.switch import Light


class Wled(Light):
    """
    Represents a WLED strip.

    @see https://github.com/Skinah/wled
    @see https://github.com/Aircoookie/WLED
    """

    def __init__(self, master_control_item, effect_item, primary_color_item,
                 secondary_color_item, duration_in_minutes):
        """
        Constructs a new object.

        :raise ValueError: if any parameter is invalid
        """
        Light.__init__(self, master_control_item, duration_in_minutes,
                       0, True)

        self.effect_item = effect_item
        self.primary_color_item = primary_color_item
        self.secondary_color_item = secondary_color_item
        self.effect_timer = None

    def on_switch_turned_on(self, events, item_name):
        """
        @override to turn on the effect timer
        """
        if super(Wled, self).on_switch_turned_on(events, item_name):
            self._start_effect_timer(events)

    def on_switch_turned_off(self, events, item_name):
        """
        @override to turn off the effect timer
        """
        if super(Wled, self).on_switch_turned_off(events, item_name):
            self._cancel_effect_timer()

    def _start_effect_timer(self, events):
        """
        Creates and returns the timer to change to a random effect
        """

        def change_effect():
            # Randomize the primary and secondary HSB colours
            # Focus on bright colours (randomize over all Hue range, with
            # Saturation between 50 and 100%, and full Brightness.
            primary_color = "{},{},100".format(
                random.choice(range(0, 360)), random.choice(range(50, 100)))
            events.send_command(pe.get_item_name(self.primary_color_item), primary_color)

            secondary_color = "{},{},100".format(
                random.choice(range(0, 360)), random.choice(range(50, 100)))
            events.send_command(pe.get_item_name(self.secondary_color_item), secondary_color)

            # now randomize the effect
            # noinspection PyTypeChecker
            effect_id = random.choice(list(get_effects().keys()))
            events.send_command(pe.get_item_name(self.effect_item), str(effect_id))

            # start the next timer
            next_duration_in_minute = random.choice(range(2, 7))
            self.effect_timer = Timer(next_duration_in_minute * 60, change_effect)
            self.effect_timer.start()

        self._cancel_timer()  # cancel the previous timer, if any.

        self.effect_timer = Timer(3, change_effect)  # start timer in 3 secs
        self.effect_timer.start()

    def _cancel_effect_timer(self):
        """
        Cancel the random effect switch timer.
        """
        if self.effect_timer is not None and self.effect_timer.is_alive():
            self.effect_timer.cancel()
            self.effect_timer = None

    def __str__(self):
        """
        @override
        """
        return u"{}, effectItem: {}, primaryColorItem: {}, secondaryColorItem: {}".format(
            super(Wled, self).__str__(), pe.get_item_name(self.effect_item),
            pe.get_item_name(self.primary_color_item), pe.get_item_name(self.secondary_color_item))


def get_effects() -> Dict:
    return {0: 'Solid',
            102: 'Candle Multi',
            52: 'Circus',
            34: 'Colorful',
            8: 'Colorloop',
            74: 'Colortwinkle',
            7: 'Dynamic',
            69: 'Fill Noise',
            45: 'Fire Flicker',
            89: 'Fireworks Starbust',
            110: 'Flow',
            87: 'Glitter',
            53: 'Halloween',
            75: 'Lake',
            44: 'Merry Christmas',
            107: 'Noise Pal',
            105: 'Phased',
            11: 'Rainbow',
            5: 'Random Colors',
            79: 'Ripple',
            99: 'Ripple Rainbow',
            15: 'Running',
            108: 'Sine',
            39: 'Stream',
            13: 'Theater'
            }
