import sys
from time import sleep, mktime
import subprocess
import csv
from datetime import datetime
import matplotlib
matplotlib.use('Agg')   # Force matplotlib to not use any Xwindows backend.
import matplotlib.pyplot as plt
from mininet.util import dumpNodeConnections, quietRun
from mininet.log import info, lg, setLogLevel
from mininet.node import Controller
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import Station, OVSKernelAP
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from subprocess import call

# time (sec), cwnd (MSS)
tcpprobe_csv_header = ['time', 'src_addr_port', 'dst_addr_port', 'bytes', 'next_seq', 'unacknowledged', 'cwnd',
                       'slow_start', 'swnd', 'smoothedRTT', 'rwnd']
# time (YYYYMMDDHHMMSS), interval (S.S-S.S), bps (bps)
iperf_csv_header = ['time', 'src_addr', 'src_port', 'dst_addr' ,'dst_port', 'other', 'interval', 'B_sent', 'bps']

#not understand
def clean_tcpprobe_procs():
    """ Serach and kill any running tcpprobe processes.
    """
    # Search and kill any running tcpprobe procs
    print('Killing any running tcpprobe processes...')
    procs = quietRun('pgrep -f /proc/net/tcpprobe').split()

    for proc in procs:
        output = quietRun('sudo kill -KILL {0}'.format(proc.rstrip()))
        if output is not '':
            print(output)

def draw_BR_plot(time_h1, bw_h1, alg):
    """ Draw the BR plot for the iperf client hosts.
        :param  time_h1 List of time values for host h1.
        :param  bw_h1   List of bandwidth values for host h1.
        :param  alg     TCP Congestion Control algorithm used in the test.
    """
    print('*** Drawing the fairness plot...')
    plt.plot(time_h1, bw_h1, label='Source Host 1 (h1)')

    plt.xlabel('Time (sec)')
    plt.ylabel('Bandwidth (Mbps)')

    plt.title("TCP Fairness Graph\n{0} TCP Congestion Control Algorithm".format(alg.capitalize()))

    plt.legend()

    plt.savefig('WiFIBR_graph_{0}'.format(alg))
    plt.close()



def parse_iperf_data(alg, host_addrs):
    """ Parse the iperf data files for the given algorithm and RTT.

        :param  alg         String with the TCP congestion control algorithms data to parse.
        :param  host_addrs  Dictionary with the host names as keys and their addresses as values.
    """
    print('*** Parsing iperf data...')
    data = dict({'sta1': {'Mbps': list(), 'time': list()}, 'sta2': {'Mbps': list(), 'time': list()}})

    # Use time's first value as time=0, and convert the bps to Mbps
    first_row = True
    with open('iperf_{0}_sta1-sta2.txt'.format(alg), 'r') as fcsv:
        r = csv.DictReader(fcsv, delimiter=',', fieldnames=iperf_csv_header)
        for row in r:
            if host_addrs['sta1'] in row['src_addr']:
                time = mktime(datetime.strptime(str(row['time']), '%Y%m%d%H%M%S').timetuple())

                # On the first row set up the required values. Then, check for repeated timestamps and fix that
                if first_row:
                    time_init = time
                    first_row = False
                    data['sta1']['time'].append(time - time_init)
                elif time-time_init == data['h1']['time'][-1]:
                    data['sta1']['time'].append(time - time_init + 1)
                else:
                    data['sta1']['time'].append(time - time_init)
                data['sta1']['Mbps'].append(int(row['bps'])/1000000)
    # Pop the last row because it is the average bandwidth of the session
    print('sta1: time={0}, bandwidth={1}'.format(data['sta1']['time'].pop(), data['sta1']['Mbps'].pop()))

    return data


def parse_tcpprobe_data(alg, host_addrs):
    """ Parse the tcpprobe data file for the given algorithm and RTT.
        :param  alg         String with the TCP congestion control algorithms data to parse.
        :param  host_addrs  Dictionary with the host names as keys and their addresses as values.
    """
    print('*** Parsing tcpprobe data...')
    data = dict({'sta1': {'cwnd': list(), 'time': list()}, 'sta2': {'cwnd': list(), 'time': list()}})

    first_row = True
    with open('tcpprobe_{0}.txt'.format(alg), 'r') as fcsv:
        r = csv.DictReader(fcsv, delimiter=' ', fieldnames=tcpprobe_csv_header, restval=-1000)
        for row in r:
            # Since the cwnd of sender h1 is set by the ACKs from receiver h2, we will search for rows where the
            # dst_addr_port field matches h1's IP to save h1's cwnd. We do the same for all other cases.
            if host_addrs['sta1'] in row['src_addr_port']:
                time = float(row['time'])
                if first_row:
                    first_row = False
                    time_init = time
                data['sta1']['time'].append(time - time_init)
                data['sta1']['cwnd'].append(int(row['cwnd']))

    return data


def start_tcpprobe(filename):  #not sure what mean
    """ Install tcp_pobe module and dump to file.

        :param  filename    Path to the file where to dump the tcpprobe data.
    """
    print('Unloading tcp_probe module...')
    clean_tcpprobe_procs()

    # Unload the module
    output = quietRun('sudo rmmod tcp_probe')
    if output != '':
        print(output.rstrip())

    print('Loading tcp_probe module...')
    # TODO: why do we use the full=1 arg? Do not filter to port=5001, but use the IP of the sender instead.
    output = quietRun('sudo modprobe tcp_probe full=1')
    if output != '':
        print(output.rstrip())

    print('Saving tcpprobe output to: {0}'.format(filename))
    return subprocess.Popen('sudo cat /proc/net/tcpprobe > {0}'.format(filename), shell=True)


def tcp_tests(alg, iperf_runtime):
    """ Run the TCP congestion control tests.
        :param  alg       string with the TCP congestion control algorithms to test.
        :param  iperf_runtime       Time to run the iperf clients in seconds.
    """
    print("*** Tests settings:\n - Algorithm: {0}\n - Iperf runtime: {1}\n"
          .format(alg, iperf_runtime))

    # Start tcp probe process
    #print('*** Starting tcpprobe recording...') #why this part
    #tcpprobe_proc = start_tcpprobe('tcpprobe_{0}.txt'.format(alg)) #
    """
    copy from ack_test
    """
    # Create the net topology
    print('*** Creating topology...')
  
    net = Mininet_wifi(topo=None,build=False,link=wmediumd,wmediumd_mode=interference,ipBase='10.0.0.0/8')
    info( '*** Adding controller\n' )
    c0 = net.addController(name='c0',controller=Controller,protocol='tcp',port=6633)
    
    info( '*** Add switches/APs\n')
    ap1 = net.addAccessPoint('ap1', cls=OVSKernelAP, ssid='ap1-ssid', channel='1', mode='g', position='389.0,191.0,0')

    info( '*** Add hosts/stations\n')
    sta2 = net.addStation('sta2', ip='10.0.0.2', position='529.0,99.0,0', passwd='123456', radius_identity='sta2')
    sta1 = net.addStation('sta1', ip='10.0.0.1', position='259.0,91.0,0', passwd='123456', radius_identity='sta1')

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
    print(sta1.IP())
    print(sta2.IP())
    host_addrs = dict({'sta1': sta1.IP(), 'sta2': sta2.IP()})
    # Run iperf
    popens = dict()
    print("*** Starting iperf servers sta2...")
    popens[sta2] = sta2.popen(['iperf', '-s', '-p', '5001', '-w', '16m'])

    # Client options:
    # -i: interval between reports set to 1sec
    # -l: length read/write buffer set to default 8KB
    # -w: TCP window size (socket buffer size) set to 16MB
    # -M: TCP MSS (MTU-40B) set to 1460B for an MTU of 1500B
    # -N: disable Nagle's Alg
    # -Z: select TCP Congestion Control alg
    # -t: transmission time
    # -f: format set to kilobits
    # -y: report style set to CSV
    print("*** Starting iperf client sta1...")
    popens[sta1] = sta1.popen('iperf -c {0} -p 5001 -i 1 -w 16m -M 1460 -N -Z {1} -t {2} -y C > \
                                   iperf_{1}_{3}.txt'
                                  .format(sta2.IP(), alg, iperf_runtime, 'sta1-sta2'), shell=True)
   
    print("*** Waiting {0}sec for iperf clients to finish...".format(iperf_runtime))
    
    popens[sta1].wait()

    # Terminate the servers and tcpprobe subprocesses
    print('*** Terminate the iperf servers and tcpprobe processes...')
    popens[sta2].terminate()
    #tcpprobe_proc.terminate()

    popens[sta2].wait()
    #tcpprobe_proc.wait()
    #clean_tcpprobe_procs()

    print("*** Stopping test...")
    net.stop()

    print('*** Processing data...')
    
    data = parse_iperf_data(alg, host_addrs)

    draw_BR_plot(data['sta1']['time'], data['sta1']['Mbps'],alg)


if __name__ == '__main__':
        # Run tests
    setLogLevel('info')
    if (len(sys.argv)!=3):
       print("not enough arguments: python tcp_test.py iperf_runtime, exit")
       exit(1)
    else:
       tcp_tests(sys.argv[1], int(sys.argv[2]))
