from aaa_modules.layout_model.zone import Zone
from aaa_modules.layout_model.device import Device


class ImmutableZoneManager:
    """
    Similar to ZoneManager, but this class contains read-only methods. 
    Instances of this class is passed to the method Action#onAction.
    """

    def __init__(self, get_zones_fcn, get_zone_by_id_fcn,
                 get_devices_by_type_fcn):
        self.get_zones_fcn = get_zones_fcn
        self.get_zone_by_id_fcn = get_zone_by_id_fcn
        self.get_devices_by_type_fcn = get_devices_by_type_fcn

    def getContainingZone(self, device):
        """
        Returns the first zone containing the device or None if the device
        does not belong to a zone.

        :param Device device: the device
        :rtype: Zone or None
        """
        if device is None:
            raise ValueError('device must not be None')

        for zone in self.getZones():
            if zone.hasDevice(device):
                return zone

        return None

    def getZones(self):
        """
        Returns a new list contains all zone.

        :rtype: list(Zone)
        """
        return self.get_zones_fcn()

    def getZoneById(self, zoneId):
        """
        Returns the zone associated with the given zoneId.

        :param string zoneId: the value returned by Zone::getId()
        :return: the associated zone or None if the zoneId is not found
        :rtype: Zone
        """
        return self.get_zone_by_id_fcn(zoneId)

    def getDevicesByType(self, cls):
        """
        Returns a list of devices in all zones matching the given type.

        :param Device cls: the device type
        :rtype: list(Device)
        """
        return self.get_devices_by_type_fcn(cls)

    def __str__(self):
        value = u""
        for z in self.getZones():
            value = f"{value}\n{str(z)}"

        return value
