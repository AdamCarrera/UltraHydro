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
        self.jogSpeed['x'] = 100000                        # YAML FILE
        self.jogSpeed['y'] = 100000
        self.jogSpeed['z'] = 100000


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
                    self.handle.GOpen('%s --direct -s ALL' % port)
                    print(self.handle.GInfo())
                    _bConnected = True
                except gclib.GclibError as e:
                    print("Something went wrong: {0}".format(e))

                if _bConnected:
                    break
            print("post connection handle status: {0}".format(self.handle))

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

    def begin_motion(self):
        try:
            self.handle.GCommand('BG A')
        except gclib.GclibError as e:
            print("Cannot begin motion, {0}".format(e))

    def stop_motion(self):
        self.handle.GCommand('ST')
        print('Motion Stopped!')

    def set_origin(self):
        try:
            self.handle.GCommand('ST')
            self.handle.GCommand('DP 0,0,0')
        except gclib.GclibError as e:
            print("Something went wrong: {0}".format(e))

    def steps_to_mm(self, steps):
        result = steps[0] / (self.xCal * 1.0)

        return result

    def mm_to_steps(self, mm):
        result = mm * self.xCal

        return result

    def scan(self, scan_size, step_size):
        boundary1 = scan_size / 2
        boundary2 = -1 * scan_size / 2

        NN = (scan_size // step_size) + 1

        pointCloud = np.linspace(boundary1, boundary2, NN, endpoint=True)
        it = np.nditer(pointCloud, flags=['f_index'])

        for n in it:
            self.handle.GCommand('PA %d' % n)
            self.begin_motion()
            time.sleep(1)
            # self.handle.GCommand('WT 1000')
            print("moving to point #{0} out of {1}, at location: {2}".format(it.index, NN - 1, n))

    def clean_up(self):

        if self.has_handle():
            self.handle.GCommand('ST')
            self.handle.GCommand('MO')
            self.handle.GClose()
        return
