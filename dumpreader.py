import serial

THRES = 0.94
EPSILON = 0.25

def to_msec(value):
    return round((value * 21.3333) / 1000, 4) 

def to_value(s):
    return (ord(s[0]) << 8) + ord(s[1])

def stream_data_from_file(filename):
    with open(filename, "rb") as f:
        while True:
            pulse = f.read(2)
            blank = f.read(2)
            if pulse and blank:
                #yield to_msec(pulse), to_msec(blank)
                yield to_value(pulse), to_value(blank)
            else:
                break

def stream_data_from_serial(device):
    s = serial.Serial(device, 19200)
    s.write(bytearray([0, 0, 0, 0, 0]))
    s.write("S")
    result = s.read(3)
    if result != "S01":
        raise IOError
    while True:
        pulse = s.read(2)
        blank = s.read(2)
        if pulse and blank:
            yield to_value(pulse), to_value(blank)
        else:
            break
    s.close()

class StreamSyncError(Exception):
    def __init__(self, pulse):
        self.pulse = pulse
        pass
    
    def __str__(self):
        return "Stream out of synch: " + self.pulse.__str__()    

class State(object):
    def __init__(self, parser):
        self.parser = parser

    def near_one(self, value):
        return (1.0 + EPSILON) >= value >= (1.0 - EPSILON)
    
    def is_zero(self, pulse):
        return self.near_one(pulse[0] / 16.0) #and near_one(pulse[1] / 16.0)
    
    def is_one(self, pulse):
        return self.near_one(pulse[0] / 32.0) #and near_one(pulse[1] / 16.0)

    def is_preamble(self, pulse):
        return self.near_one(pulse[0] / 140.0) and self.near_one(pulse[1] / 48.0)
    
    def parse(self, pulse, packet_listener):
        pass
    
class PreambleState(State):
    def __init__(self, parser):
        super(PreambleState, self).__init__(parser)
        self.wait_preamble = False 
        self.wait_one = False
        
    def parse(self, pulse, packet_listener):
        if self.is_zero(pulse):
            if self.wait_preamble:
                raise StreamSyncError(pulse)
            else:
                self.wait_preamble = True
        elif self.is_preamble(pulse):
            if not self.wait_preamble:
                raise StreamSyncError(pulse)
            else:
                self.wait_preamble = False
                self.wait_one = True
        elif self.is_one(pulse):
            if not self.wait_one:
                raise StreamSyncError(pulse)
            else:
                self.wait_one = False
                self.parser.set_state(PayloadState(self.parser))
            
        
class PayloadState(State):
    def __init__(self, parser):
        super(PayloadState, self).__init__(parser)
        self.packet = ""
        
    def parse(self, pulse, packet_listener):
        if self.is_zero(pulse):
            self.packet += "0"
        elif self.is_one(pulse):
            self.packet += "1"
        else:
            raise StreamSyncError(pulse)
        
        if len(self.packet) == 32:
            packet_listener(self.packet)
            self.parser.set_state(PreambleState(self.parser))
    
class PulseParser(object):
    def __init__(self, data_source):
        self.data_source = data_source
        self.set_state(PreambleState(self))
        
    def set_state(self, new_state):
        self.state = new_state
    
    def parse(self, new_packet_listener=None):
        for p in self.data_source:
            try:
                self.state.parse(p, new_packet_listener)
            except StreamSyncError as e:
                print e, " state=", self.state
                self.set_state(PreambleState(self))
           
def on_new_packet(packet):
    print "Packet: ", packet, " == ", hex(int(packet, 2))
 
 
#pp = PulseParser(stream_data_from_file('/Users/yildiz/test_000.bin'))
pp = PulseParser(stream_data_from_serial("/dev/cu.usbmodem00000001"))
eof = pp.parse(on_new_packet)
