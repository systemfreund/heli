import serial

s = serial.Serial('/dev/cu.usbmodem00000001', 19200, timeout=1)

tosend = bytearray(0)

print "Sending: ", tosend

s.write(tosend)
x = s.read(4)

print "Read: ", x

s.close()
