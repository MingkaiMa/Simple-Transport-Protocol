import sys
import struct
import os
from socket import *
from random import *
from Segment import *
import time

if len(sys.argv) != 9:
    print('Usage {}:<receiver_host_ip> <receiver_port>'\
          ' <file.txt> <MWS> <MSS> <timeout> <pdrop> <seed>'.format(sys.argv[0]))
    sys.exit()


senderPort = 12000
receiverName = sys.argv[1]
receiverPort = int(sys.argv[2])
file_name = sys.argv[3]
MAX_WINDON_SIZE_original = int(sys.argv[4])
MAX_SEGMENT_SIZE = int(sys.argv[5])
MAX_WINDON_SIZE = MAX_WINDON_SIZE_original // MAX_SEGMENT_SIZE
timeout = float(sys.argv[6])
pdrop = float(sys.argv[7])
arg_for_seed = int(sys.argv[8])
base = 0
nextSeqNb = 0
timer = Timer(timeout)
received_ack = {}
send_sequence = []
clientSocket = socket(AF_INET, SOCK_DGRAM)

file_log = 'Sender_log.txt'
all_start_time = time.time()
amount_of_data = 0
amount_of_data_segment = 0
amount_of_drop = 0
amount_of_retransmitted = 0
amount_of_duplicate = 0
list_of_resent = []
expectedSeqNb = 0
seed(arg_for_seed)

TCP_connection_establish_sender_side(senderPort, receiverPort,receiverName, clientSocket, all_start_time)

L = []
with open(file_name, 'rb') as f:
    n = 0
    while True:
        piece = f.read(MAX_SEGMENT_SIZE)
        if not piece:
            break
        L.append(piece.decode('utf-8'))
        send_segment = createSegment(senderPort, receiverPort, n, 0, MAX_SEGMENT_SIZE, '', piece.decode('utf-8'))
        send_pack = pack(send_segment)
        send_sequence.append(send_pack)
        n += 1


while True:
    while(nextSeqNb < min(base + MAX_WINDON_SIZE, len(send_sequence))):
        p = random()
        print(f'p: {p}, pdrop: {pdrop}')
        if p > pdrop:
            print('sent: ', nextSeqNb)
            print(unpack(send_sequence[nextSeqNb]))
            write_log(file_log, 'snd {:5.3f} D  {} {} 0\n'.format(1000 * (time.time() - all_start_time),
                                                               nextSeqNb * MAX_SEGMENT_SIZE,
                                                               len(unpack(send_sequence[nextSeqNb]).data)))
            amount_of_data += len(unpack(send_sequence[nextSeqNb]).data)
            amount_of_data_segment += 1
            clientSocket.sendto(send_sequence[nextSeqNb], (receiverName, receiverPort))
            nextSeqNb += 1
        else:
            print('drop: ', nextSeqNb)
            write_log(file_log, 'drop {:5.3f} D  {} {} 0\n'.format(1000 * (time.time() - all_start_time),
                                                                 nextSeqNb * MAX_SEGMENT_SIZE,
                                                                 len(unpack(send_sequence[nextSeqNb]).data)))
            amount_of_drop += 1
            nextSeqNb += 1

    while True:
        clientSocket.settimeout(timeout)
        try:
            message, receiverAddress = clientSocket.recvfrom(2048)
            ack_segment = unpack(message)
            expectedSeqNb = ack_segment.header.ackNb
            print('received ACK: ', ack_segment)
            write_log(file_log, 'rcv {:5.3f} A  {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                              ack_segment.header.seqNb * MAX_SEGMENT_SIZE,
                                                              ack_segment.header.ackNb * MAX_SEGMENT_SIZE))
        except:
            if base not in list_of_resent:
                print('timeout_resent: ', base)
                write_log(file_log, 'snd {:5.3f} D  {} {} 0\n'.format(1000 * (time.time() - all_start_time),
                                                                    base,
                                                                    len(unpack(send_sequence[base]).data)))
            
                amount_of_data += len(unpack(send_sequence[base]).data)
                amount_of_retransmitted += 1
                clientSocket.sendto(send_sequence[base], (receiverName, receiverPort))
                list_of_resent.append(base)
            else:
                pass
        if expectedSeqNb == 0:
            continue
            
        if expectedSeqNb == len(send_sequence):
            TCP_connection_termination_sender_side(senderPort, receiverPort, receiverName, clientSocket, all_start_time)
            write_log(file_log, 'Amount of (original) Data Transferred (in bytes) : {}\n'.format(amount_of_data))
            write_log(file_log, 'Number of Data Segments Sent (excluding retransmissions) : {}\n'.format(amount_of_data_segment))
            write_log(file_log, 'Number of (all) Packets Dropped (by the PLD module) : {}\n'.format(amount_of_drop))
            write_log(file_log, 'Number of Retransmitted Segments : {}\n'.format(amount_of_retransmitted))
            write_log(file_log, 'Number of Duplicate Acknowledgements received : {}\n'.format(amount_of_duplicate))
            
            sys.exit()
        if expectedSeqNb > base:
            base = expectedSeqNb
            print('base:', base)
            break
    
        else:
            if expectedSeqNb not in received_ack:
                received_ack[expectedSeqNb] = 1
            elif received_ack[expectedSeqNb] == 2 and expectedSeqNb not in list_of_resent:
                clientSocket.sendto(send_sequence[expectedSeqNb], (receiverName, receiverPort))
                print('fast_resent: ', expectedSeqNb)
                write_log(file_log, 'snd  {:5.3f} D   {} {}  0\n'.format(time.time() - all_start_time,
                                                                  expectedSeqNb * MAX_SEGMENT_SIZE,
                                                                  len(unpack(send_sequence[expectedSeqNb]).data)))
                amount_of_data += len(unpack(send_sequence[expectedSeqNb]).data)
                amount_of_retransmitted += 1
                amount_of_duplicate += 1
                list_of_resent.append(expectedSeqNb)
                
            else:                
                received_ack[expectedSeqNb] += 1
                




