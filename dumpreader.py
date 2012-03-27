THRES = 0.94
EPSILON = 0.25

def to_msec(value):
    return round((value * 21.3333) / 1000, 4) 

def to_value(s):
    return (ord(s[0]) << 8) + ord(s[1])

def read_pulse(filename):
    with open(filename, "rb") as f:
        while True:
            pulse = f.read(2)
            blank = f.read(2)
            if pulse and blank:
                #yield to_msec(pulse), to_msec(blank)
                yield to_value(pulse), to_value(blank)
            else:
                break

def near_one(value):
    return (1.0 + EPSILON) >= value >= (1.0 - EPSILON)

def is_zero(pulse):
    return near_one(pulse[0] / 16.0) #and near_one(pulse[1] / 16.0)
    
def is_one(pulse):
    return near_one(pulse[0] / 32.0) #and near_one(pulse[1] / 16.0)

def is_preamble(pulse):
    return near_one(pulse[0] / 140.0) and near_one(pulse[1] / 48.0)
            
groups = []
    
packet = ""
is_payload = False
wait_preamble = False
for p in read_pulse('/Users/yildiz/test_000.bin'):
    if is_zero(p):
        print p, "-> ZERO"
        
        if is_payload:
            packet += "0"
        elif not wait_preamble:
            wait_preamble = True
        else:
            print "Byte stream out of synch"
            break            
    elif is_preamble(p):
        print p, "-> PREAMBLE"
        
        if wait_preamble:
            wait_preamble = False
            is_payload = True
        else:
            print "Byte stream out of synch"
            break
    elif is_one(p):
        print p, "-> ONE"
        
        if is_payload:
            packet += "1"
        else:
            print "Byte stream out of synch"
            break
    else:
        print "Unable to interpret pulse ", p
        break

    if len(packet) == 32:
        print "Last Packet = ", packet
        print "-------------------------------"
        
        is_payload = False
        wait_preamble = False
        packet = ""

print "Last Packet = ", packet, " (", len(packet), ")"
print "-------------------------------"
