import pyvisa
import time as t
rm = pyvisa.ResourceManager()
rm.list_resources()

class FunctionGenerator():
    Type = 'Siglent'
    def __init__(self,frequency,amplitude, period, cycles,output):
        self.inst = rm.open_resource('USB0::0xF4EC::0x1103::SDG1XCAD3R4276::INSTR')
        self.inst.write("C1:BSWV STATE,ON")
        t.sleep(.01)
        self.inst.write("C1:BSWV STPS,0")
        t.sleep(.005)
        self.inst.write("C1:BTWV INT")
        t.sleep(.005)
        self.inst.write("C1:BTWV TRMD,RISE")
        t.sleep(.005)
        self.inst.write("C1:BTWV DLAY, 2.4e-07S")
        t.sleep(.005)
        self.inst.write("C1:BTWV GATE_NCYC,NCYC")
        t.sleep(.005)
        self.inst.write("C1:BTWV CARR,OFST,0")
        t.sleep(.005)
        self.inst.write("C1:BTWV CARR,WVTP,SINE")
        t.sleep(.005)
        self.inst.write("C1:BTWV CARR,PHSE,0")
        t.sleep(.005)
        self.SetFrequency(frequency)
        self.SetAmplitude(amplitude)
        self.SetPeriod(period)
        self.SetCycles(cycles)
        self.SetOutput(output)

    def SetFrequency(self, frequency):
        self.Frequency = frequency
        Frq = "C1:BSWV FRQ,{}".format(self.Frequency)
        self.inst.write(Frq)
        t.sleep(.03)

    def SetAmplitude(self, amplitude):
        self.Amplitude = amplitude
        Amp = "C1:BSWV AMP,{}".format(self.Amplitude)
        self.inst.write(Amp)
        t.sleep(.03)
    def SetPeriod(self, period):
        self.Period = period
        Peri = "C1:BTWV PRD,{}".format(self.Period)
        self.inst.write(Peri)
        t.sleep(.03)
    def SetCycles(self, cycle):
        self.Cycle = cycle
        Cycl = "C1:BTWV TIME,"+self.Cycle
        self.inst.write(Cycl)
        t.sleep(.03)
    def SetOutput(self, output):
        self.Output = output
        OutPut = "C1:OUTP {},LOAD,50".format(self.Output)
        self.inst.write(OutPut)
        t.sleep(.03)

#my_FunctionGenerator = FunctionGenerator(frequency = '1000000',amplitude = '10', period = '.0001', cycles = '2', output = 'ON')


