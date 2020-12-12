#!/usr/bin/python

from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import Station, OVSKernelAP
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from subprocess import call

import time
import config
import os

from utils import cal_ack_rate,cal_pack_rate

def get_test_cmd(send_rate,ack_rate,test_time,wifi_mode,test_mode):
    """
    :param send_rate:
    :param ack_rate:
    :param test_time:
    :param wifi_mode:
    :return: test command
    """
    sender_data_ip = config.sender_data_ip
    receiver_data_ip = config.receiver_data_ip
    file_name_tail = wifi_mode + '_' + test_mode + '_' + \
                     time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time())) + '.txt'
    data_recv_log = 'data_receiver_' + file_name_tail
    data_send_log = 'data_sender_' + file_name_tail
    ack_recv_log = 'ack_receiver_' + file_name_tail
    ack_send_log = 'ack_sender_' + file_name_tail

    # print data_recv_log
    cmd_dict = {}
    cmd_dict['data_receiver_cmd'] = "iperf3 -s -i 1 -d -1 > %s &" % (data_recv_log)
    cmd_dict['data_sender_cmd'] = "iperf3 -c %s -i 1 -b %sK -l 1472 -u -t %s -d > %s &" % \
                      (receiver_data_ip, send_rate, test_time, data_send_log)
    cmd_dict['ack_reveiver_cmd'] = 'iperf3 -s -i 1 -d -1> %s &' % (ack_recv_log)
    cmd_dict['ack_sender_cmd'] = 'iperf3 -c %s -i 1 -b %sK -l 52 -u -t %s -d > %s &' % \
                     (sender_data_ip, ack_rate, test_time, ack_send_log)
    cmd_dict['kill_iperf3'] = 'pkill -9 iperf3'
    print "%s test command dict" % test_mode
    print cmd_dict
    return cmd_dict

def run_test(sta1, sta2, cmd_dict, test_time):
    """
    test schedule of single test
    :return: one pack or ack test done
    """
    #kill iperf if iperf running  before testing
    sta1.cmd(cmd_dict["kill_iperf3"])
    sta2.cmd(cmd_dict["kill_iperf3"])

    # receiver exec iperf cmd as iperf server to receive data
    print "==========iperf recv data!==========="
    sta1.cmd(cmd_dict['data_receiver_cmd'])
    print "==========iperf recv data server open!==========="

    #sender exec iperf cmd as iperf server to receive ack
    print "==========iperf recv ack!==========="
    sta2.cmd(cmd_dict['ack_reveiver_cmd'])
    time.sleep(2)
    print "==========iperf recv ack sver open!==========="

    #sender exec iperf cmd as iperf client to send data
    print "==========iperf send data!==========="
    sta2.cmd(cmd_dict['data_sender_cmd'])
    print "==========iperf send data done!==========="

    #receiver exec iperf cmd as sender to send ack
    print "==========iperf send ack!==========="
    sta1.cmd(cmd_dict['ack_sender_cmd'])
    print "==========iperf send ack done!==========="

    time.sleep(test_time+5)

def rerun_test(sta1, sta2, pack_data_send_rate, pack_send_rate,ack_data_send_rate, ack_send_rate, test_time, wifi_mode, test_times):
    """
    run test test_times(setted in config.py)
    :return: test done
    """
    print time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
    # re run PACK emu test
    print "rerun test %d times!!!" %test_times
    for i in range(test_times):
        # run rtt test
        '''
        for k in range(len(pack_send_rate)):
            print "==========No:%d-%d PACK Test Start!==========" % ((i+1),(k+1))
            cmd_dict = get_test_cmd(pack_data_send_rate[k], pack_send_rate[k], test_time, wifi_mode, "PACK%d"%(k+1))
            run_test(sta1, sta2, cmd_dict, test_time)
            time.sleep(5)
            print "==========No:%d-%d PACK Test Done!==========" % ((i+1),(k+1))
        '''
        # run ACK emu test
        for j in range(len(ack_send_rate)):
            print "==========No:%d-%d ACK Test Start!==========" %((i+1),(j+1))
            cmd_dict = get_test_cmd(ack_data_send_rate[j],ack_send_rate[j],test_time,wifi_mode,"ACK_%d"%(1 if j==0 else 2**j))
            run_test(sta1, sta2, cmd_dict, test_time)
            time.sleep(5)
            print "==========No:%d-%d ACK Test Done!==========" %((i+1),(j+1))

    print time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
    print "GAME OVER!!!"

def myNetwork():

    net = Mininet_wifi(topo=None,
                       build=False,
                       link=wmediumd,
                       wmediumd_mode=interference,
                       ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    c0 = net.addController(name='c0',
                           controller=Controller,
                           protocol='tcp',
                           port=6633)

    info( '*** Add switches/APs\n')
    ap1 = net.addAccessPoint('ap1', cls=OVSKernelAP, ssid='ap1-ssid',
                             channel='1', mode='g', position='389.0,191.0,0')

    info( '*** Add hosts/stations\n')
    sta2 = net.addStation('sta2', ip='10.0.0.2',
                           position='529.0,99.0,0', passwd='123456', radius_identity='sta2')
    sta1 = net.addStation('sta1', ip='10.0.0.1',
                           position='259.0,91.0,0', passwd='123456', radius_identity='sta1')

    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=3)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info( '*** Add links\n')
    net.addLink(sta1, ap1)
    net.addLink(ap1, sta2)

    #net.plotGraph(max_x=1000, max_y=1000)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches/APs\n')
    net.get('ap1').start([c0])

    info( '*** Post configure nodes\n')
       

    #CLI(net)

    sta1, sta2 = net.get('sta1','sta2')
    print sta1.IP()
    print sta2.IP()    
    
    #load config
    wifi_mode = config.wifi_mode
    test_time = config.test_time
    test_times = config.test_times
    wifi_mode_bw_dict = config.wifi_mode_max_rate_dict
    max_rate = wifi_mode_bw_dict[wifi_mode]
    RTT = config.to_test_RTT

    #testing
    pack_send_rate = []
    pack_data_send_rate = []
    for rtt in RTT:
        ack_send,data_send = cal_pack_rate(max_rate,rtt,wifi_mode)
        pack_send_rate.append(ack_send)
        pack_data_send_rate.append(data_send)
    ack_send_rate, ack_data_send_rate = cal_ack_rate(max_rate)
    print pack_send_rate, pack_data_send_rate,ack_send_rate,ack_data_send_rate

    #run test test_times
    rerun_test(sta1, sta2, pack_data_send_rate, pack_send_rate,ack_data_send_rate, ack_send_rate, test_time, wifi_mode, test_times)

    #cmd_dict = get_test_cmd(send_rate,ack_rate,test_time,wifi_mode,test_mode)
    #run_test(sta1, sta2, cmd_dict)
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

