# Welcome to the Interactive Python Tutorial.
# Start by choosing a chapter and
# write your code in this window.

#print ("Hello, World!")
import time
import serial


# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
    port='COM5',
    baudrate=115200,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)

if ser.isOpen():
    print(ser.name + ' is open...') 

cmdIn=1
while 1 :
    # get keyboard input
    #input = raw_input (">> ")
        # Python 3 users
    cmdIn  = input()
    if cmdIn == 'exit':
        ser.close()
        exit()
    else:
        # send the character to the device
        # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
       # ser.write(input + '\r\n')
        out = ''
        # let's wait one second before reading output (let's give device time to answer)
       # time.sleep(1)
        #while ser.inWaiting() > 0:
        print  (ser.read(1))

        #if out != '':
           # print (">>" + out)   
