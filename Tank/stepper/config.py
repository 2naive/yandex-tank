from module_exceptions import StepperConfigurationError
import load_plan as lp
import instance_plan as ip
import missile
from mark import get_marker
import info
import logging


class ComponentFactory():

    def __init__(
        self,
        rps_schedule=None,
        http_ver='1.1',
        ammo_file=None,
        instances_schedule=None,
        instances=1000,
        loop_limit=None,
        ammo_limit=None,
        uris=None,
        headers=None,
        autocases=None,
        ammo_type='phantom',
    ):
        self.log = logging.getLogger(__name__)
        self.ammo_file = ammo_file
        self.ammo_type = ammo_type
        self.rps_schedule = rps_schedule
        self.http_ver = http_ver
        self.instances_schedule = instances_schedule
        loop_limit = int(loop_limit)
        if loop_limit == -1:  # -1 means infinite
            loop_limit = None
        ammo_limit = int(ammo_limit)
        if ammo_limit == -1:  # -1 means infinite
            ammo_limit = None
        if loop_limit is None and ammo_limit is None and not rps_schedule:
            # we should have only one loop if we have instance_schedule
            loop_limit = 1
        info.status.loop_limit = loop_limit
        info.status.ammo_limit = ammo_limit
        info.status.publish("instances", instances)
        self.uris = uris
        if self.uris and loop_limit:
            info.status.ammo_limit = len(self.uris) * loop_limit
        self.headers = headers
        self.marker = get_marker(autocases)

    def get_load_plan(self):
        """
        return load plan (timestamps generator)
        """
        if self.rps_schedule and self.instances_schedule:
            raise StepperConfigurationError(
                'Both rps and instances schedules specified. You must specify only one of them')
        elif self.rps_schedule:
            info.status.publish('loadscheme', self.rps_schedule)
            return lp.create(self.rps_schedule)
        elif self.instances_schedule:
            info.status.publish('loadscheme', self.instances_schedule)
            return ip.create(self.instances_schedule)
        else:
            self.instances_schedule = []
            info.status.publish('loadscheme', self.instances_schedule)
            return ip.create(self.instances_schedule)

    def get_ammo_generator(self):
        """
        return ammo generator
        """
        af_readers = {
            'phantom': missile.AmmoFileReader,
            'slowlog': missile.SlowLogReader,
            'line': missile.LineReader,
            'uri': missile.UriReader,
            'uripost': missile.UriPostReader,
        }
        if self.uris and self.ammo_file:
            raise StepperConfigurationError(
                'Both uris and ammo file specified. You must specify only one of them')
        elif self.uris:
            ammo_gen = missile.UriStyleGenerator(
                self.uris,
                self.headers,
                http_ver=self.http_ver
            )
        elif self.ammo_file:
            
            if self.ammo_type in af_readers:
                if self.ammo_type is 'phantom':
                    with open(self.ammo_file) as ammo:
                        if not ammo.next()[0].isdigit():
                            self.ammo_type = 'uri'
                            self.log.info(
                                "Setting ammo_type 'uri' because ammo is not started with digit and you did non specify ammo format.")
                        else:
                            self.log.info(
                                "I believe ammo_type is 'phantom' cause you did not specify it.")
            else:
                raise NotImplementedError(
                    'No such ammo type implemented: "%s"' % self.ammo_type)
            ammo_gen = af_readers[self.ammo_type](
                self.ammo_file,
                headers=self.headers,
                http_ver=self.http_ver
            )
        else:
            raise StepperConfigurationError(
                'Ammo not found. Specify uris or ammo file')
        return ammo_gen

    def get_marker(self):
        return self.marker
