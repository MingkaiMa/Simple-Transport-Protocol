import sys
import struct
from socket import *
from random import *
from Segment import *

expectedSeqNb = 0
dic = {}
out_of_order_seq_nb = []
receive_log = 'Receiver_log.txt'
all_start_time = time.time()
amoung_of_data_received = 0
number_of_data_segment_received = 0

file_to_write = sys.argv[1]
receiverPort = 12000
receiverSocket = socket(AF_INET, SOCK_DGRAM)
receiverSocket.bind(('', receiverPort))
TCP_connection_establish_receiver_side(receiverSocket, all_start_time)
while 1:
    message, senderAddress = receiverSocket.recvfrom(2048)
    received_segment = unpack(message)
    if received_segment.header.flag == 'FIN':
        TCP_connection_termination_receiver_side(receiverSocket, received_segment, senderAddress, all_start_time)
        write_log(receive_log, 'Amount of (original) Data Received (in bytes): {}\n'.format(amoung_of_data_received))
        write_log(receive_log, 'Number of (original) Data Segments Received: {}\n'.format(number_of_data_segment_received))
        with open(file_to_write, 'wb') as f:
            for key in sorted(dic):
                f.write(dic[key].data.encode('utf-8'))

        break
    
    received_seqNb = received_segment.header.seqNb
    dic[received_seqNb] = received_segment
    amoung_of_data_received += len(received_segment.data)
    number_of_data_segment_received += 1
    write_log(receive_log, 'rcv {:5.3f} D {} {} {}\n'.format(1000 * (time.time() - all_start_time),
                                                             received_segment.header.seqNb * received_segment.header.mss,
                                                             len(received_segment.data),
                                                             received_segment.header.ackNb * received_segment.header.mss))

    
    if received_seqNb == expectedSeqNb:
        expectedSeqNb = expectedSeqNb + 1
        while True:
            if (expectedSeqNb in dic):
                expectedSeqNb += 1
                continue
            else:
                ack_segment = createSegment(received_segment.header.sourcePort, received_segment.header.destPort,
                                            0, expectedSeqNb, received_segment.header.mss,
                                            'ACK', '')
                ack_pack = pack(ack_segment)
                receiverSocket.sendto(ack_pack, senderAddress)
                print('ACK sent:', ack_segment)
                write_log(receive_log, 'snd {:5.3f} A {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                                        ack_segment.header.seqNb * ack_segment.header.mss,
                                                                        ack_segment.header.ackNb * ack_segment.header.mss))
                break
        


    else:
        ack_segment = createSegment(received_segment.header.sourcePort, received_segment.header.destPort,
                                    0, expectedSeqNb, received_segment.header.mss,
                                    'ACK', '')
        ack_pack = pack(ack_segment)
        receiverSocket.sendto(ack_pack, senderAddress)
        print('ACK sent:', ack_segment)
        write_log(receive_log, 'snd {:5.3f} A {} 0 {}\n'.format(1000 * (time.time() - all_start_time),
                                                                ack_segment.header.seqNb * ack_segment.header.mss,
                                                                ack_segment.header.ackNb * ack_segment.header.mss))
    
        

