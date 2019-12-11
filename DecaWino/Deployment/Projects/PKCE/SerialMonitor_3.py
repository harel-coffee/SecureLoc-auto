from serial import *
import json

PORT1 = 'COM17'
PORT2 = 'COM19'
PORT3 = 'COM21'

out_file = 'skew.json'
out_txt = 'skew_'
signature_file = "signature_"
sample = {}


try:
    port1 = Serial(PORT1)
    port2 = Serial(PORT2)
    #port3 = Serial(PORT3)

except:
    print("One of the serial devices is missing")

exit_flag = False

#ports = [port1, port2, port3]
ports = [port1, port2]
f_txt = {}
for port in ports:
    f_txt[port.name] = open(out_txt + port.name + '.txt', 'w+')


with open(out_file,'w+') as f:
    ctr = {}
    skew = {}
    temperature = {}
    last_temp = {}
    sk = 0

    for port in ports:
        last_temp[port] = 24

    for port in ports:
        temperature[port] = 0
        skew[port] = 0
        ctr[port] = 0

    for port in ports:
        # msg = "250"
        # port.write(msg.encode())
        msg = "11"
        port.write(msg.encode())


    while not(exit_flag):
        try:
            for port in ports:
                if (port.in_waiting > 0):
                    line = port.readline().decode('utf_8')
                    if (line[0] != '$'):
                        print(line)
                        data = line.split('|')
                        if (len(data) == 4):
                            f_txt[port.name].write(data[1])
                            f_txt[port.name].write(' ')
                            f_txt[port.name].write(data[0])
                            f_txt[port.name].write(' ')
                            f_txt[port.name].write(data[2])
                            f_txt[port.name].write(' ')
                            f_txt[port.name].write(data[3])

                        elif (line[0] == '#'):
                            signature = line[1:]
                            with open(signature_file + port.name + '.txt', 'a') as sig:
                                sig.write('\n')
                                sig.write(signature)



        except KeyboardInterrupt:
            print("Ctrl + C receveid, quitting")
            exit_flag = True
            for port in ports:
                f_txt[port.name].close()

        # except:
        #     print("Serial port disconnected")
        #     exit_flag = True
