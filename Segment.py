import struct
from random import *
import time
file_log = 'Sender_log.txt'
receive_log = 'Receiver_log.txt'

class Header:
    def __init__(self, sourcePort, destPort, seqNb, ackNb, MSS, flag):
        self.sourcePort = sourcePort
        self.destPort = destPort
        self.seqNb = seqNb
        self.ackNb = ackNb
        self.mss = MSS
        self.flag = flag


class Segment:
    def __init__(self, header, data):
        self.header = header
        self.data = data

    def __str__(self):
        s = ''
        s = s + str(self.header.sourcePort) + ',' + str(self.header.destPort) + ','
        s = s + str(self.header.seqNb) + ',' + str(self.header.ackNb) + ',' + \
            str(self.header.mss) + ',' + self.header.flag + ',' + self.data
        return s

    

def createSegment(sourcePort, destPort, seqNb, ackNb, MMS, flag, data):
    header = Header(sourcePort, destPort, seqNb, ackNb, MMS, flag)
    data = data
    segment = Segment(header, data)
    return segment


def pack(segment):
    send_pack = struct.pack('7I{}s{}s'.format(len(segment.header.flag), len(segment.data)),
                            segment.header.sourcePort, segment.header.destPort,
                            segment.header.seqNb, segment.header.ackNb, segment.header.mss,
                            len(segment.header.flag), len(segment.data),
                            segment.header.flag.encode('utf-8'), segment.data.encode('utf-8'))
    return send_pack


def unpack(pack):
    size = struct.calcsize('7I')
    nb_part = struct.unpack('7I', pack[:size])
    sourcePort = nb_part[0]
    destPort = nb_part[1]
    seqNb = nb_part[2]
    ackNb = nb_part[3]
    MMS = nb_part[4]
    flag_length = nb_part[5]
    data_length = nb_part[6]
    flag_and_data = struct.unpack('{}s{}s'.format(flag_length, data_length),
                                  pack[size:])
    flag = flag_and_data[0].decode('utf-8')
    data = flag_and_data[1].decode('utf-8')
    segment = createSegment(sourcePort, destPort, seqNb, ackNb, MMS, flag, data)
    return segment
    
def write_log(file_log, data):
    with open(file_log, 'a') as file:
        file.write(data)


def TCP_connection_establish_sender_side(senderPort, receiverPort, receiverName, clientSocket, all_start_time):
    client_isn = randint(0,1000)
    SYN_segment = createSegment(senderPort, receiverPort, client_isn, 0, 0, 'SYN', '')
    send_SYN = pack(SYN_segment)
    clientSocket.sendto(send_SYN, (receiverName, receiverPort))
    write_log(file_log, 'snd {:5.3f} S  {} 0 0\n'.format(1000 * (time.time()-all_start_time), client_isn))
    print('SYN sent.', SYN_segment)
    message, receiverAddress = clientSocket.recvfrom(2048)
    SYNACK_segment = unpack(message)
    print('SYNACK received.', SYNACK_segment)
    write_log(file_log, 'rcv {:5.3f} SA  {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                        SYNACK_segment.header.seqNb, SYNACK_segment.header.ackNb))
    
    third_segment = createSegment(SYNACK_segment.header.sourcePort, SYNACK_segment.header.destPort,
                                  client_isn, SYNACK_segment.header.seqNb + 1, SYNACK_segment.header.mss,
                                  '','')
    send_third = pack(third_segment)
    clientSocket.sendto(send_third, (receiverName, receiverPort))
    print('Third segment sent.', third_segment)
    write_log(file_log, 'snd {:5.3f} A  {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                       third_segment.header.seqNb, third_segment.header.ackNb))
    

def TCP_connection_establish_receiver_side(receiverSocket, all_start_time):
    print('---')
    message, senderAddress = receiverSocket.recvfrom(2048)
    SYN_segment = unpack(message)
    print('SYN received.', SYN_segment)
    write_log(receive_log, 'rcv {:5.3f} S  {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                         SYN_segment.header.seqNb,
                                                         SYN_segment.header.ackNb))
    server_isn = randint(0,1000)
    SYNACK_segment = createSegment(SYN_segment.header.sourcePort, SYN_segment.header.destPort,
                                   server_isn, SYN_segment.header.seqNb + 1, SYN_segment.header.mss,
                                   'SYN', '')
    send_SYNACK = pack(SYNACK_segment)
    receiverSocket.sendto(send_SYNACK, senderAddress)
    print('SYNACK sent', SYNACK_segment)
    write_log(receive_log, 'snd {:5.3f} SA {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                             SYNACK_segment.header.seqNb,
                                                             SYNACK_segment.header.ackNb))

    message, senderAddress = receiverSocket.recvfrom(2048)
    third_segment = unpack(message)
    print('third_segment received ', third_segment)
    write_log(receive_log, 'rcv {:5.3f} A {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                            third_segment.header.seqNb,
                                                            third_segment.header.ackNb))
    print('Connection established, get ready now.')
    
    

def TCP_connection_termination_sender_side(senderPort, receiverPort, receiverName, clientSocket, all_start_time):
    print('sender initiate shutdown---')
    client_isn = randint(0,1000)
    FIN_segment = createSegment(senderPort, receiverPort, client_isn, 0, 0, 'FIN', '')
    send_FIN = pack(FIN_segment)
    clientSocket.sendto(send_FIN, (receiverName, receiverPort))
    print('FIN sent.', FIN_segment)
    write_log(file_log, 'snd {:5.3f} F {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                    FIN_segment.header.seqNb,
                                                    FIN_segment.header.ackNb))
    message, receiverAddress = clientSocket.recvfrom(2048)
    FINACK_segment = unpack(message)
    print('FINACK received.', FINACK_segment)
    write_log(file_log, 'rcv {:5.3f} FA {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                          FINACK_segment.header.seqNb,
                                                          FINACK_segment.header.ackNb))

    message, receiverAddress = clientSocket.recvfrom(2048)
    FIN_2_segment = unpack(message)
    print('2FIN received.', FIN_2_segment)
    write_log(file_log, 'rcv {:5.3f} F {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                         FIN_2_segment.header.seqNb,
                                                         FIN_2_segment.header.ackNb))


    FINACK_2_segment = createSegment(FIN_2_segment.header.sourcePort, FIN_2_segment.header.destPort,
                                  client_isn, FIN_2_segment.header.seqNb + 1, FIN_2_segment.header.mss,
                                  'FIN','')
    
    send_2FINACK = pack(FINACK_2_segment)
    clientSocket.sendto(send_2FINACK, (receiverName, receiverPort))
    print('FINACK_2_segment sent.', FINACK_2_segment)
    write_log(file_log, 'snd {:5.3f} FA {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                          FINACK_2_segment.header.seqNb,
                                                          FINACK_2_segment.header.ackNb))
    clientSocket.close()
    
    
    
def TCP_connection_termination_receiver_side(receiverSocket, FIN_segment, senderAddress, all_start_time):
    print('shutdown---')
##    message, senderAddress = receiverSocket.recvfrom(2048)
##    FIN_segment = unpack(message)
    print('FIN received.', FIN_segment)
    write_log(receive_log, 'rcv {:5.3f} F {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                       FIN_segment.header.seqNb,
                                                       FIN_segment.header.ackNb))
    server_isn = randint(0,1000)
    FINACK_segment = createSegment(FIN_segment.header.sourcePort, FIN_segment.header.destPort,
                                   server_isn, FIN_segment.header.seqNb + 1, FIN_segment.header.mss,
                                   'FIN', '')
    send_FINACK = pack(FINACK_segment)
    receiverSocket.sendto(send_FINACK, senderAddress)
    print('FINACK sent', FINACK_segment)
    write_log(receive_log, 'snd {:5.3f} FA {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                             FINACK_segment.header.seqNb,
                                                             FINACK_segment.header.ackNb))

    FIN_2_segment = createSegment(FIN_segment.header.sourcePort, FIN_segment.header.destPort,
                                   server_isn, 0, FIN_segment.header.mss,
                                   'FIN', '')

    send_2FIN = pack(FIN_2_segment)
    receiverSocket.sendto(send_2FIN, senderAddress)
    print('2FIN sent', FIN_2_segment)
    write_log(receive_log, 'snd {:5.3f} F {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                            FIN_2_segment.header.seqNb,
                                                            FIN_2_segment.header.ackNb))
    
    

    message, senderAddress = receiverSocket.recvfrom(2048)
    FINACK_2_segment = unpack(message)
    print('FINACK_2_segment received ', FINACK_2_segment)
    write_log(receive_log, 'rcv {:5.3f} FA {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                             FINACK_2_segment.header.seqNb,
                                                             FINACK_2_segment.header.ackNb))
    print('Connection shutdown.')
    receiverSocket.close()
    
    
class Timer():
    def __init__(self, interval):
        self.start_time = 0
        self.interval = interval

    def start(self):
        if self.start_time == 0:
            self.start_time = time.time()

    def stop(self):
        if self.start_time != 0:
            self.start_time = 0

    def is_running(self):
        return self.start_time != 0

    def is_timeout(self):
        if not self.is_running():
            return False
        return (time.time() - self.start_time) >= self.interval








