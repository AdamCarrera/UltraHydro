import ctypes
import numpy as np
import pyqtgraph as pg
import time as t

try:
    from picosdk.ps5000a import ps5000a as ps
    from picosdk.functions import adc2mV, assert_pico_ok, mV2adc
except ImportError:
    print('Picotech libries not installed')

global startTime
startTime = t.time()

class Picoscope(object):
    possibleRanges_mV = {
        10: "PS5000A_10MV",
        20: "PS5000A_20MV",
        50: "PS5000A_50MV",
        100: "PS5000A_100MV",
        200: "PS5000A_200MV",
        500: "PS5000A_500MV",
        1000: "PS5000A_1V",
        2000: "PS5000A_2V",
        5000: "PS5000A_5V",
        10000: "PS5000A_10V",
        20000: "PS5000A_20V"
    }

    possibleResValues = {
        "8-bit": "PS5000A_DR_8BIT",
        "12-bit": "PS5000A_DR_12BIT",
        "14-bit": "PS5000A_DR_14BIT",
        "15-bit": "PS5000A_DR_15BIT",
        "16-bit": "PS5000A_DR_16BIT"}

    range_mV = 0
    threshold = 0
    external = False

    ready = ctypes.c_int16(0)
    check = ctypes.c_int16(0)
    powerStatus = 0
    channel = 0
    coupling_type = 0
    chARange = 0
    preTriggerSamples = 0
    postTriggerSamples = 0
    maxsamples = 1
    timebase = 2
    timeIntervalns = ctypes.c_float()
    returnedMaxSamples = ctypes.c_int16()

    # function generator parameters
    wavetype = ctypes.c_int32(0)
    sweepType = ctypes.c_int32(0)
    triggertype = ctypes.c_int32(0)
    triggerSource = ctypes.c_int32(0)

    blocks = 1

    overflow = ctypes.c_int16()
    cmaxSamples = ctypes.c_int32()

    bufferMaxRay = {}
    bufferMinRay = {}
    data_mVRay = []
    averagedData = {}

    time = {}  # Time axis for graphing

    # streaming mode variables
    sampleInterval = ctypes.c_int32(16)
    channel_range = ""

    def __init__(self):

        self.status = {}  # Exmpty dictionary
        self.status['running'] = False
        self.status['status'] = {}  # Empty dictionary to hold status results
        self.chandle = ctypes.c_int16()  # Stores handle for the Picotech HW
        self.maxADC = ctypes.c_int16()  # Stores a reference to the max ADC
        self.resolution = None
        self.resolutionString = ''
        self.possibleResValues = {
            "8-bit": "PS5000A_DR_8BIT",
            "12-bit": "PS5000A_DR_12BIT",
            "14-bit": "PS5000A_DR_14BIT",
            "15-bit": "PS5000A_DR_15BIT",
            "16-bit": "PS5000A_DR_16BIT"}
        # MS (2020.10.22): set the possible sampling modes
        self.samplingMode = None
        self.possibleSamplingModes = {'Rapid Block Mode': 'rapid_block'}
        # MS (2020.10.22): set the possible voltage scale
        self.rangeScale = None
        self.possibleRanges = {
            '10 mV': {'psRANGE': 'PS5000A_10MV', 'intRange': 10},
            '20 mV': {'psRANGE': 'PS5000A_20MV', 'intRange': 20},
            '50 mV': {'psRANGE': 'PS5000A_50MV', 'intRange': 50},
            '100 mV': {'psRANGE': 'PS5000A_100MV', 'intRange': 100},
            '200 mV': {'psRANGE': 'PS5000A_200MV', 'intRange': 200},
            '500 mV': {'psRANGE': 'PS5000A_500MV', 'intRange': 500},
            '1 V': {'psRANGE': 'PS5000A_1V', 'intRange': 1000},
            '2 V': {'psRANGE': 'PS5000A_2V', 'intRange': 2000},
            '5 V': {'psRANGE': 'PS5000A_5V', 'intRange': 5000},
            '10 V': {'psRANGE': 'PS5000A_10V', 'intRange': 10000},
            '20 V': {'psRANGE': 'PS5000A_20V', 'intRange': 20000},
        }
        self.possibleWaveforms = {
            '1': 1,
            '2': 2,
            '3': 3,
            '10': 10,
            '30': 30,
        }
        # channelInputRanges = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000]
        self.downsampling = False
        self.downsamplingRatio = 1

        # Create chandle and status ready for use

        self.status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(self.chandle), None, 1)

        try:
            assert_pico_ok(self.status["openunit"])
        except:  # PicoNotOkError:

            powerStatus = self.status["openunit"]

            if self.powerStatus == 286:
                self.status["changePowerSource"] = ps.ps5000aChangePowerSource(self.chandle, powerStatus)
            elif self.powerStatus == 282:
                self.status["changePowerSource"] = ps.ps5000aChangePowerSource(self.chandle, powerStatus)
            else:
                raise

            assert_pico_ok(self.status["changePowerSource"])

        # Displays the serial number and handle
        print(self.chandle.value)

    def setup(self, range_mV, blocks, timebase, external, triggermV, preSamples, postSamples):
        # Set up channel A
        # handle = chandle
        self.channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
        # enabled = 1
        self.coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]

        self.setRange(range_mV)
        # Finds the max ADC count
        # Handle = chandle
        # Value = ctype.byref(maxADC)
        self.status["maximumValue"] = ps.ps5000aMaximumValue(self.chandle, ctypes.byref(self.maxADC))


        self.timebase = timebase


        self.setTrigger(triggermV, external)

        self.setWindow(preSamples, postSamples)
        self.getTimebase()
        self.setBlocks(blocks)

    def setTimebase(self, timebase):
        self.timebase = timebase
        self.getTimebase()
        self.configMemory()
        self.createBuffers()
        self.data_mVRay.clear()

    def setBlocks(self, blocks):
        self.blocks = blocks
        self.configMemory()
        self.createBuffers()
        self.data_mVRay.clear()

    def close(self):
        # Stop the scope
        # handle = chandle
        self.status["stop"] = ps.ps5000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])
    def max(self):
        return np.max(self.data_mVRay)

    def average(self):
        self.average = np.mean(self.data_mVRay[0])
        return average

    def setTrigger(self, triggermV, external):
        self.threshold = triggermV
        self.external = external
        # Set up single trigger
        # handle = chandle
        # enabled = 1
        if external:
            source = ps.PS5000A_CHANNEL["PS5000A_EXTERNAL"]
        else:
            source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
        threshold = int(mV2adc(self.threshold, self.chARange, self.maxADC))
        # direction = PS5000A_RISING = 2
        # delay = 0 s
        # auto Trigger = 1000 ms
        self.status["trigger"] = ps.ps5000aSetSimpleTrigger(self.chandle, 1, source, threshold, 2, 0, 18)
        assert_pico_ok(self.status["trigger"])

    def setWindow(self, pre, post):
        self.preTriggerSamples = pre
        self.postTriggerSamples = post
        self.maxsamples = self.preTriggerSamples + self.postTriggerSamples

    def getTimebase(self):
        self.status["GetTimebase"] = ps.ps5000aGetTimebase2(self.chandle, self.timebase, self.maxsamples,
                                                            ctypes.byref(self.timeIntervalns),
                                                            ctypes.byref(self.returnedMaxSamples), 0)
        assert_pico_ok(self.status["GetTimebase"])
        print("Time interval:" + str(self.timeIntervalns.value))

    def setRange(self, range_mV):
        if range_mV in self.possibleRanges_mV:
            try:
                self.range_mV = range_mV
                res = self.possibleRanges_mV[range_mV]

                self.chARange = ps.PS5000A_RANGE[res]
                # analogue offset = 0 V
                self.status["setChA"] = ps.ps5000aSetChannel(self.chandle, self.channel, 1, self.coupling_type,
                                                             self.chARange,
                                                             0)
                assert_pico_ok(self.status["setChA"])
                self.channel_range = ps.PS5000A_RANGE[res]
            except:
                print("Invalid range")
        else:
            raise ValueError('Invalid range')

    def increaseRange(self):
        if self.range_mV == 10000:
            self.setRange(20000)
        elif self.range_mV == 5000:
            self.setRange(10000)
        elif self.range_mV == 2000:
            self.setRange(5000)
        elif self.range_mV == 1000:
            self.setRange(2000)
        elif self.range_mV == 500:
            self.setRange(1000)
        elif self.range_mV == 200:
            self.setRange(500)
        elif self.range_mV == 100:
            self.setRange(200)
        elif self.range_mV == 50:
            self.setRange(100)
        elif self.range_mV == 20:
            self.setRange(50)
        elif self.range_mV == 10:
            self.setRange(20)

    def autoRange(self, maxRange, cushion):
        #This temporary variable remembers the current blocks setting to restore it after autoranging
        blocksTemp = self.blocks
        if not blocksTemp == 1 :
            self.setBlocks(1)

        self.setRange(maxRange)
        self.block()
        max_pk2_pk = max(self.data_mVRay[0][:])

        if max_pk2_pk * (1 + cushion) > 10000:
            print("maximum range")
        elif max_pk2_pk * (1 + cushion) > 5000:
            self.setRange(10000)
        elif max_pk2_pk * (1 + cushion) > 2000:
            self.setRange(5000)
        elif max_pk2_pk * (1 + cushion) > 1000:
            self.setRange(2000)
        elif max_pk2_pk * (1 + cushion) > 500:
            self.setRange(1000)
        elif max_pk2_pk * (1 + cushion) > 200:
            self.setRange(500)
        elif max_pk2_pk * (1 + cushion) > 100:
            self.setRange(200)
        elif max_pk2_pk * (1 + cushion) > 50:
            self.setRange(100)
        elif max_pk2_pk * (1 + cushion) > 20:
            self.setRange(50)
        elif max_pk2_pk * (1 + cushion) > 10:
            self.setRange(20)
        else:
            self.setRange(10)

        if not blocksTemp == 1:
            self.setBlocks(blocksTemp)
        return

    def isClipping(self):
        if max(self.data_mVRay[0]) >= self.range_mV:
            return True
        return False

    def autoRangeUp(self):
        #This temporary variable remembers the current blocks setting to restore it after autoranging
        blocksTemp = self.blocks
        if not blocksTemp == 1 :
            self.setBlocks(1)
        if len(self.data_mVRay) == 0:
            self.block()
        while self.isClipping() and self.range_mV < max(self.possibleRanges_mV) :
            pico.increaseRange()
            self.block()
        if not blocksTemp == 1 :
            self.setBlocks(blocksTemp)

    def setSigGen(self, pkToPk_uV, frequencyHz):
        # Output a sine wave
        # handle = chandle
        # offsetVoltage = 0
        # waveType = ctypes.c_int16(0) = PS5000A_SINE
        # increment = 0
        # dwellTime = 1
        # sweepType = ctypes.c_int16(1) = PS5000A_UP
        # operation = 0
        # shots = 0
        # sweeps = 0
        # triggerType = ctypes.c_int16(0) = PS5000a_SIGGEN_RISING
        # triggerSource = ctypes.c_int16(0) = P5000a_SIGGEN_NONE
        # extInThreshold = 1
        self.status["setSigGenBuiltInV2"] = ps.ps5000aSetSigGenBuiltInV2(self.chandle, 0, pkToPk_uV, self.wavetype,
                                                                         frequencyHz, frequencyHz, 0, 1, self.sweepType,
                                                                         0, 0, 0, self.triggertype, self.triggerSource,
                                                                         0)
        assert_pico_ok(self.status["setSigGenBuiltInV2"])

    def configMemory(self):
        # Creates a overflow location for data
        self.overflow = ctypes.c_int16()
        # Creates converted types maxsamples
        self.cmaxSamples = ctypes.c_int32(self.maxsamples)

        # Handle = Chandle
        # nMaxSamples = ctypes.byref(cmaxSamples)
        self.status["MemorySegments"] = ps.ps5000aMemorySegments(self.chandle, self.blocks,
                                                                 ctypes.byref(self.cmaxSamples))
        assert_pico_ok(self.status["MemorySegments"])

        # sets number of captures
        self.status["SetNoOfCaptures"] = ps.ps5000aSetNoOfCaptures(self.chandle, self.blocks)
        assert_pico_ok(self.status["SetNoOfCaptures"])

    def createBuffers(self):

        for i in range(self.blocks):
            # Create buffers ready for assigning pointers for data collection
            self.bufferMaxRay[i] = (ctypes.c_int16 * self.maxsamples)()
            self.bufferMinRay[i] = (ctypes.c_int16 * self.maxsamples)()
            self.bufferAMax = (ctypes.c_int16 * self.maxsamples)()
            self.bufferAMin = (ctypes.c_int16 * self.maxsamples)()

            # Setting the data buffer location for data collection from channel A
            # Handle = Chandle
            self.source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
            # Buffer max = ctypes.byref(bufferMaxRay[i])
            # Buffer min = ctypes.byref(bufferMinRay[i])
            # Buffer length = maxsamples
            # Segment index = i
            # Ratio mode = ps5000a_Ratio_Mode_None = 0
            self.status["SetDataBuffers"] = ps.ps5000aSetDataBuffers(self.chandle, self.source,
                                                                     ctypes.byref(self.bufferMaxRay[i]),
                                                                     ctypes.byref(self.bufferMinRay[i]),
                                                                     self.maxsamples, i, 0)

            assert_pico_ok(self.status["SetDataBuffers"])

        # Creates a overflow location for data
        self.overflow = (ctypes.c_int16 * self.blocks)()
        # Creates converted types maxsamples
        self.cmaxSamples = ctypes.c_int32(self.maxsamples)

    def createTimeAxis(self):
        self.time = np.linspace(0, (self.cmaxSamples.value) * self.timeIntervalns.value, self.cmaxSamples.value)

    def block(self):
        self.data_mVRay.clear()
        self.time = {}
        self.status["runblock"] = ps.ps5000aRunBlock(self.chandle, self.preTriggerSamples, self.postTriggerSamples,
                                                     self.timebase, None, 0, None, None)
        assert_pico_ok(self.status["runblock"])

        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            self.status["isReady"] = ps.ps5000aIsReady(self.chandle, ctypes.byref(ready))

        self.status["GetValuesBulk"] = ps.ps5000aGetValuesBulk(self.chandle, ctypes.byref(self.cmaxSamples), 0,
                                                               self.blocks - 1, 0, 0,

                                                               ctypes.byref(self.overflow))
        assert_pico_ok(self.status["GetValuesBulk"])
        for i in range(self.blocks):
            self.data_mVRay.append(adc2mV(self.bufferMaxRay[i], self.chARange, self.maxADC))
            #self.data_mVRay.append(np.asarray(self.bufferMaxRay[i], dtype=int) * self.chARange / self.maxADC.value)
        self.createTimeAxis()

    def setupStreaming(self, sizeOfOneBuffer, numBuffersToCapture, sampleInterval):
        # Size of capture

        self.sampleInterval = ctypes.c_int32(sampleInterval)

        totalSamples = sizeOfOneBuffer * numBuffersToCapture

        # Create buffers ready for assigning pointers for data collection

        bufferAMax = np.zeros(shape=sizeOfOneBuffer, dtype=np.int16)

        memory_segment = 0

        # Set data buffer location for data collection from channel A
        # handle = chandle
        # source = PS5000A_CHANNEL_A = 0
        # pointer to buffer max = ctypes.byref(bufferAMax)
        # pointer to buffer min = ctypes.byref(bufferAMin)
        # buffer length = maxSamples
        # segment index = 0
        # ratio mode = PS5000A_RATIO_MODE_NONE = 0
        self.status["setDataBuffersA"] = ps.ps5000aSetDataBuffers(self.chandle,
                                                                  ps.PS5000A_CHANNEL['PS5000A_CHANNEL_A'],
                                                                  bufferAMax.ctypes.data_as(
                                                                      ctypes.POINTER(ctypes.c_int16)),
                                                                  None,
                                                                  sizeOfOneBuffer,
                                                                  memory_segment,
                                                                  ps.PS5000A_RATIO_MODE['PS5000A_RATIO_MODE_AVERAGE'])
        assert_pico_ok(self.status["setDataBuffersA"])

        # Set data buffer location for data collection from channel B
        # handle = chandle
        # source = PS5000A_CHANNEL_B = 1
        # pointer to buffer max = ctypes.byref(bufferBMax)
        # pointer to buffer min = ctypes.byref(bufferBMin)
        # buffer length = maxSamples
        # segment index = 0
        # ratio mode = PS5000A_RATIO_MODE_NONE = 0

        # Begin streaming mode:
        self.sampleInterval = ctypes.c_int32(sampleInterval)
        self.sampleUnits = ps.PS5000A_TIME_UNITS['PS5000A_NS']

        # We are not triggering:
        self.maxPreTriggerSamples = 0
        self.autoStopOn = 1

        # No downsampling:
        self.downsampleRatio = 1

        # Find maximum ADC count value
        # handle = chandle
        # pointer to value = ctypes.byref(maxADC)
        self.status["maximumValue"] = ps.ps5000aMaximumValue(self.chandle, ctypes.byref(self.maxADC))
        assert_pico_ok(self.status["maximumValue"])

        self.status["runStreaming"] = ps.ps5000aRunStreaming(self.chandle,
                                                             ctypes.byref(self.sampleInterval),
                                                             self.sampleUnits,
                                                             self.maxPreTriggerSamples,
                                                             totalSamples,
                                                             self.autoStopOn,
                                                             self.downsampleRatio,
                                                             ps.PS5000A_RATIO_MODE['PS5000A_RATIO_MODE_AVERAGE'],
                                                             sizeOfOneBuffer)
        assert_pico_ok(self.status["runStreaming"])

        actualSampleInterval = self.sampleInterval.value

        print("Capturing at sample interval %s ns" % actualSampleInterval)

        # We need a big buffer, not registered with the driver, to keep our complete capture in.
        time = np.linspace(0, sizeOfOneBuffer * actualSampleInterval, sizeOfOneBuffer)
        buffer = np.zeros(shape=sizeOfOneBuffer, dtype=np.int16)
        bufferCompleteA = np.zeros(shape=totalSamples, dtype=np.int16)
        global nextSample
        nextSample = 0
        autoStopOuter = False
        wasCalledBack = False

        def streaming_callback(handle, noOfSamples, startIndex, overflow, triggerAt, triggered, autoStop, param):
            print(t.time())
            global nextSample, autoStopOuter, wasCalledBack, startTime
            wasCalledBack = True
            destEnd = nextSample + noOfSamples
            sourceEnd = startIndex + noOfSamples
            buffer = bufferAMax[startIndex:sourceEnd]

            bufferCompleteA[nextSample:destEnd] = buffer
            time = np.linspace(0, len(buffer) * actualSampleInterval, len(buffer))

            # Convert ADC counts data to mV
            adc2mVChAMax = np.asarray(buffer, dtype=int) * self.channel_range / self.maxADC.value

            if t.time() - startTime > .016:
                plt.plot(time, adc2mVChAMax, clear=True)
                pg.QtGui.QApplication.processEvents()
                startTime = t.time()

            # print(noOfSamples)
            nextSample += noOfSamples
            if autoStop:
                autoStopOuter = True

        # Convert the python function into a C function pointer.
        cFuncPtr = ps.StreamingReadyType(streaming_callback)

        # Fetch data from the driver in a loop, copying it out of the registered buffers and into our complete one.

        startTime = t.time()
        while nextSample < totalSamples and not autoStopOuter:
            wasCalledBack = False
            self.status["getStreamingLastestValues"] = ps.ps5000aGetStreamingLatestValues(self.chandle, cFuncPtr,
                                                                                          None)
if __name__ == '__main__':
    import sys

    if sys.flags.interactive != 1 or not hasattr(pg.QtCore, 'PYQT_VERSION'):
        pg.QtGui.QApplication.exec_()

    plt = pg.plot()
    pg.QtGui.QApplication.processEvents()

    plt.setXRange(0, 10000, padding=.01)  # nanoseconds
    plt.setYRange(-10000, 10000, padding=.1)  # millivolts

    pico = Picoscope()

    pico.setup(range_mV=10000, blocks=100, timebase=2, external=True, triggermV=5000, preSamples=0, postSamples=2500)
    pico.setSigGen(1500000, 1000000)

    pico.block()

    average = []

    maximum = 0
    blockTime = 0

    for i in range(10000):
        startTime = t.time()
        print(len(pico.data_mVRay))
        if pico.overflow[0]:
            pico.increaseRange()
            print(pico.range_mV)
        pico.block()
        blockTime = blockTime + t.time() - startTime

        average = np.mean(pico.data_mVRay, axis=0)
        plt.plot(pico.time, average, clear=True)
        maximum = maximum + max(average)
        pg.QtGui.QApplication.processEvents()

    maximum = maximum / 100
    print(maximum)

    print("average block time")
    print(blockTime / 100)

    pico.close()


