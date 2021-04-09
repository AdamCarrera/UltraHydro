import gclib
import numpy as np
import time


class Galil:
    # Galil class used to communicate with the motion controller
    def __init__(self):
        self.handle = gclib.py()                         # Initialize the library object

        self.axes = ['x', 'y', 'z']

        self.jogging = False
        self.jogSpeed = {}
        self.jogSpeed['x'] = 50000                        # YAML FILE
        self.jogSpeed['y'] = 50000
        self.jogSpeed['z'] = 50000


        self.speed = {}
        self.speed['x'] = 100000                           # YAML FILE
        self.speed['y'] = 100000
        self.speed['z'] = 100000

        self.xCal = 10                                   # YAML FILE

    def toggle_handle(self):

        if self.has_handle():
            self.handle.GCommand('ST')
            self.handle.GCommand('MO')
            self.handle.GClose()
            print('Connection terminated')

        else:
            port_list = self.handle.GAddresses()
            print("pre-connection handle status: {0}".format(self.handle))
            _bConnected = False

            for port in port_list.keys():
                print("port: {0} , handle status: {1}".format(port, self.handle))
                try:
                    self.handle.GOpen('192.168.42.100 --direct -s ALL')
                    print(self.handle.GInfo())
                    _bConnected = True
                except gclib.GclibError as e:
                    print("Something went wrong: {0}".format(e))

                if _bConnected:
                    break
            print("post connection handle status: {0}".format(self.handle))

            # Electronic Gearing
            self.handle.GCommand('GAD = CA')
            self.handle.GCommand('GRD = 1')
            self.handle.GCommand('GM 1,1,1,1')

            try:
                self.handle.GCommand('ST')
                self.handle.GCommand('SP %d' % self.speed['x'])  # yaml file value
                self.handle.GCommand('SH')
            except gclib.GclibError as e:
                print("Connection error: {0}".format(e))

    def has_handle(self):
        try:
            self.handle.GCommand('WH')
            print("Handle is OK")
            return True
        except gclib.GclibError as e:
            print("No handle available: {0}".format(e))
            return False

    def abort(self):
        self.handle.GCommand('AB')
        print('Motion Aborted')

    def jog(self, axe):
        # Try sending jog command to Galil, except an error if that fails
        if axe == 'x':
            try:
                self.handle.GCommand('JG %d' % self.jogSpeed['x'])  # yaml file value
            except gclib.GclibError as e:
                print("Cannot jog: {0}".format(e))
        elif axe == 'y':
            try:
                self.handle.GCommand('JG ,%d' % self.jogSpeed['y'])  # yaml file value
            except gclib.GclibError as e:
                print("Cannot jog: {0}".format(e))
        elif axe == 'z':
            try:
                self.handle.GCommand('JG , ,%d' % self.jogSpeed['z'])  # yaml file value
            except gclib.GclibError as e:
                print("Cannot jog: {0}".format(e))
        else:
            raise Exception('Incompatible axis')

    def begin_motion(self, axis=None):
        try:
            self.handle.GCommand('BG {0}'.format(axis))
        except gclib.GclibError as e:
            print("Cannot begin motion, {0}".format(e))

    def stop_motion(self):
        self.handle.GCommand('ST')
        print('Motion Stopped!')

    def set_origin(self):
        try:
            self.handle.GCommand('ST')
            self.handle.GCommand('DP 0,0,0')
            print('origin set')
        except gclib.GclibError as e:
            print("Something went wrong: {0}".format(e))

    def steps_to_mm(self, steps):
        result = steps[0] / (self.xCal * 1.0)

        return result

    def mm_to_steps(self, mm):
        result = mm * self.xCal

        return result

    def scan(self, x_arr, y_arr, z_arr):
        for i in np.nditer(x_arr):
            for j in np.nditer(y_arr):
                for k in np.nditer(z_arr):
                    self.handle.GCommand('PA {0},{1},{2}'.format(i, j, k))
                    self.handle.GCommand('BG ABC')

                    while self.isMoving():
                        time.sleep(0.1)

    def isMoving(self):

        stat_a = self.handle.GCommand('MG_BGA')
        stat_b = self.handle.GCommand('MG_BGB')
        stat_c = self.handle.GCommand('MG_BGC')

        # print("statA: %s, statB %s, statC %s" % (statA, statB, statC))
        if stat_a == '0.0000' and stat_b == '0.0000' and stat_c == '0.0000':
            return False
        else:
            return True

    def clean_up(self):

        if self.has_handle():
            self.handle.GCommand('ST')
            self.handle.GCommand('MO')
            self.handle.GClose()
        return
