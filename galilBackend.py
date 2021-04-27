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
        self.jogSpeed['x'] = 20000                        # YAML FILE
        self.jogSpeed['y'] = 20000
        self.jogSpeed['z'] = 20000


        self.speed = {}
        self.speed['x'] = 20000                           # YAML FILE
        self.speed['y'] = 20000
        self.speed['z'] = 20000

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
        # Try commands moved to GUI application
        if axe == 'x':
            self.handle.GCommand('JG %d' % self.jogSpeed['x'])  # yaml file value
        elif axe == 'y':
            self.handle.GCommand('JG ,%d' % self.jogSpeed['y'])  # yaml file value
        elif axe == 'z':
            self.handle.GCommand('JG , ,%d' % self.jogSpeed['z'])  # yaml file value
        else:
            raise Exception('Incompatible axis')

    def begin_motion(self, axis=None):
        try:
            self.handle.GCommand('BG {0}'.format(axis))
        except gclib.GclibError as e:
            print("Cannot begin motion, {0}".format(e))

    def stop_motion(self):
        try:
            self.handle.GCommand('ST')
            print('Motion Stopped!')
        except gclib.GclibError as e:
            print("Cannot stop motion, {0}".format(e))

    def set_origin(self):
        try:
            self.handle.GCommand('ST')
            self.handle.GCommand('DP 0,0,0')
            print('origin set')
        except gclib.GclibError as e:
            print("Something went wrong: {0}".format(e))
            raise gclib.GclibError(e)

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

    def limit_poll(self):

        # array of keys to hold boolean values regarding limit status
        switches = np.array(['A Forward', 'A Reverse', 'B Forward', 'B Reverse', 'C Forward', 'C Reverse'])

        # poll status of each limit switch and compile everyting into an array

        # Test Code
        stat_a_fwd = '1.0000'
        stat_a_rev = '0.0000'

        stat_b_fwd = '0.0000'
        stat_b_rev = '0.0000'

        stat_c_fwd = '0.0000'
        stat_c_rev = '0.0000'


        # Galil Code
        # stat_a_fwd = self.handle.GCommand('MG_LFA')
        # stat_a_rev = self.handle.GCommand('MG_LRA')
        #
        # stat_b_fwd = self.handle.GCommand('MG_LFB')
        # stat_b_rev = self.handle.GCommand('MG_LRB')
        #
        # stat_c_fwd = self.handle.GCommand('MG_LFC')
        # stat_c_rev = self.handle.GCommand('MG_LRC')

        poll_value = np.array([stat_a_fwd, stat_a_rev, stat_b_fwd, stat_b_rev, stat_c_fwd, stat_c_rev], dtype=float)
        poll_value = np.not_equal(poll_value, 1)

        limit_status = np.rec.fromarrays((switches, poll_value), names=['switch', 'status'])

        # # create an empty array to hold all of the active switches and sort through each switch
        # message = np.array([])
        #
        # for limit in np.nditer(limit_status):
        #     if limit['status']:
        #         message = np.append(message, limit['switch'])
        #
        # # if message is empty, no limits are hit, return none
        # # else, return the switches that have been tripped
        if len(limit_status) > 0:
            return limit_status
        else:
            return None

    def limit_analysis(self, status_array=None):

        for status in np.nditer(status_array):
            if status['status']:
                message = str(status['switch']) + ' has been pressed'
                raise Exception(message)

    def get_position(self):
        a = self.handle.GCommand('PA ?')
        b = self.handle.GCommand('PA ,?')
        c = self.handle.GCommand('PA ,,?')

        return a, b, c

    def clean_up(self):

        if self.has_handle():
            self.handle.GCommand('ST')
            self.handle.GCommand('MO')
            self.handle.GClose()
        return
