from zone_api.alert import Alert
from zone_api.core.immutable_zone_manager import ImmutableZoneManager


class RangeViolationAlert:
    """
    Given a valid value range, track the state of the value, and send an warning
    alert when the value is out of range. Send another info alert when the
    value is back to the normal range.
    """

    def __init__(self, min_value, max_value, notification_step_value=3,
                 label="value", unit="", module=None,
                 interval_between_alerts_in_minutes=-1, admin_alert=False):
        """
        Ctor
        :param int min_value: the minimum good value
        :param int max_value: the maximum good value
        :param int notification_step_value: the value at which point a 
            notification email will be sent. E.g. with the default maxValue
            of 50 and the step value of 3, the first notification is at 53,
            and the next one is 56.
        :param str label: the name of the value
        :param str unit: the unit of the value
        :raise ValueError: if any parameter is invalid
        """
        if max_value <= min_value:
            raise ValueError('maxValue must be greater than minValue')

        if notification_step_value <= 0:
            raise ValueError('notificationStepValue must be positive')

        self.min_value = min_value
        self.max_value = max_value
        self.notification_step_value = notification_step_value
        self.label = label
        self.unit = unit
        self.module = module
        self.interval_between_alerts_in_minutes = interval_between_alerts_in_minutes
        self.adminAlert = admin_alert
        self.sent_alert = False
        self.next_max_notification_threshold = None
        self.next_min_notification_threshold = None

        self.reset_states()

    def update_state(self, value, zone, zone_manager: ImmutableZoneManager):
        """
        Update this object with the latest value.
        If the value is outside the range, an warning alert will be sent.
        If the value is back to the normal range, an info alert will be sent.
        """
        if self.min_value <= value <= self.max_value:
            if self.sent_alert:  # send an info alert that the value is back to normal
                self.reset_states()

                msg = f'The {zone.get_name()} {self.label} at {value}{self.unit} is back to the normal range ' \
                      f'({self.min_value}% - {self.max_value}%).'
                alert = Alert.create_info_alert(msg)

                if self.adminAlert:
                    zone_manager.get_alert_manager().process_admin_alert(alert)
                else:
                    zone_manager.get_alert_manager().process_alert(alert)

        else:
            alert_message = ''
            if value <= self.next_min_notification_threshold:
                alert_message = f'The {zone.get_name()} {self.label} at {value}{self.unit} is below the ' \
                                f'threshold of {self.min_value}%.'
                self.next_min_notification_threshold -= self.notification_step_value
            elif value >= self.next_max_notification_threshold:
                alert_message = f'The {zone.get_name()} {self.label} at {value}{self.unit} is above the ' \
                                f'threshold of {self.max_value}%.'
                self.next_max_notification_threshold += self.notification_step_value

            if alert_message != '':
                alert = Alert.create_warning_alert(alert_message, None, [],
                                                   self.module, self.interval_between_alerts_in_minutes)
                if self.adminAlert:
                    zone_manager.get_alert_manager().process_admin_alert(alert)
                else:
                    zone_manager.get_alert_manager().process_alert(alert)

                self.sent_alert = True

    def reset_states(self):
        """
        Resets the internal states including the next min/max notification
        thresholds.
        """

        self.next_max_notification_threshold = self.max_value + self.notification_step_value
        self.next_min_notification_threshold = self.min_value - self.notification_step_value

        self.sent_alert = False
