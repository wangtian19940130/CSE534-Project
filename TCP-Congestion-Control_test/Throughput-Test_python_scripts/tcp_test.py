import sys
from time import sleep, mktime
import subprocess
import csv
from datetime import datetime
import matplotlib
matplotlib.use('Agg')   # Force matplotlib to not use any Xwindows backend.
import matplotlib.pyplot as plt
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import dumpNodeConnections, quietRun
from mininet.log import info, lg, setLogLevel

# time (sec), cwnd (MSS)
tcpprobe_csv_header = ['time', 'src_addr_port', 'dst_addr_port', 'bytes', 'next_seq', 'unacknowledged', 'cwnd',
                       'slow_start', 'swnd', 'smoothedRTT', 'rwnd']
# time (YYYYMMDDHHMMSS), interval (S.S-S.S), bps (bps)
iperf_csv_header = ['time', 'src_addr', 'src_port', 'dst_addr' ,'dst_port', 'other', 'interval', 'B_sent', 'bps']


class tcpTopo(Topo):
    def build(self, delay=2):
        """ Create the topology by overriding the class parent's method.
            :param  delay   One way propagation delay, delay = RTT / 2. Default is 2ms.
        """
        # The bandwidth (bw) is in Mbps, delay in milliseconds and queue size is in packets
        hi_params = dict(bw=960, delay='0ms', max_queue_size=80*delay, use_htb=True)  # host interface tc params
    
        # Create routers s1
        s1 = self.addSwitch('s1')

        # Create the hosts h1,h2, and link them to access router 1
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        
      #addlink
        self.addLink(s1, h1, cls=TCLink, **hi_params)
        self.addLink(s1, h2, cls=TCLink, **hi_params)

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

#


def draw_BR_plot(time_h1, bw_h1, alg, delay):
    """ Draw the fairness plot for the iperf client hosts.
        :param  time_h1 List of time values for host h1.
        :param  bw_h1   List of bandwidth values for host h1.
        :param  alg     TCP Congestion Control algorithm used in the test.
        :param  delay   Delay used in the test.
    """
    print('*** Drawing the fairness plot...')
    plt.plot(time_h1, bw_h1, label='Source Host 1 (h1)')

    plt.xlabel('Time (sec)')
    plt.ylabel('Bandwidth (Mbps)')

    plt.title("TCP BR Graph\n{0} TCP Congestion Control Algorithm Delay={1}ms"
              .format(alg.capitalize(), delay))

    plt.legend()

    plt.savefig('BR_graph_{0}_{1}ms'.format(alg, delay))
    plt.close()

def parse_iperf_data(alg, delay, host_addrs):
    """ Parse the iperf data files for the given algorithm and RTT.
        :param  alg         String with the TCP congestion control algorithms data to parse.
        :param  delay       Integer with the delay data to parse.
        :param  host_addrs  Dictionary with the host names as keys and their addresses as values.
    """
    print('*** Parsing iperf data...')
    data = dict({'h1': {'Mbps': list(), 'time': list()}, 'h2': {'Mbps': list(), 'time': list()}})

    # Use time's first value as time=0, and convert the bps to Mbps
    first_row = True
    with open('iperf_{0}_h1-h2_{1}ms.txt'.format(alg, delay), 'r') as fcsv:
        r = csv.DictReader(fcsv, delimiter=',', fieldnames=iperf_csv_header)
        for row in r:
            if host_addrs['h1'] in row['src_addr']:
                time = mktime(datetime.strptime(str(row['time']), '%Y%m%d%H%M%S').timetuple())

                # On the first row set up the required values. Then, check for repeated timestamps and fix that
                if first_row:
                    time_init = time
                    first_row = False
                    data['h1']['time'].append(time - time_init)
                elif time-time_init == data['h1']['time'][-1]:
                    data['h1']['time'].append(time - time_init + 1)
                else:
                    data['h1']['time'].append(time - time_init)
                data['h1']['Mbps'].append(int(row['bps'])/1000000)
    # Pop the last row because it is the average bandwidth of the session
    print('h1: time={0}, bandwidth={1}'.format(data['h1']['time'].pop(), data['h1']['Mbps'].pop()))

    return data


def parse_tcpprobe_data(alg, delay, host_addrs):
    """ Parse the tcpprobe data file for the given algorithm and RTT.
        :param  alg         String with the TCP congestion control algorithms data to parse.
        :param  delay       Integer with the delay data to parse.
        :param  host_addrs  Dictionary with the host names as keys and their addresses as values.
    """
    print('*** Parsing tcpprobe data...')
    data = dict({'h1': {'cwnd': list(), 'time': list()}, 'h2': {'cwnd': list(), 'time': list()},})

    first_row = True
    with open('tcpprobe_{0}_{1}ms.txt'.format(alg, delay), 'r') as fcsv:
        r = csv.DictReader(fcsv, delimiter=' ', fieldnames=tcpprobe_csv_header, restval=-1000)
        for row in r:
            # Since the cwnd of sender h1 is set by the ACKs from receiver h2, we will search for rows where the
            # dst_addr_port field matches h1's IP to save h1's cwnd. We do the same for all other cases.
            if host_addrs['h1'] in row['src_addr_port']:
                time = float(row['time'])
                if first_row:
                    first_row = False
                    time_init = time
                data['h1']['time'].append(time - time_init)
                data['h1']['cwnd'].append(int(row['cwnd']))
            #elif host_addrs['h2'] in row['src_addr_port']:
            #    data['h2']['time'].append(float(row['time']))
            #    data['h2']['cwnd'].append(int(row['cwnd']))
            # Use the time_init calculated for the first host

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


def tcp_tests(alg, delay, iperf_runtime):
    """ Run the TCP congestion control tests.
        :param  alg       string with the TCP congestion control algorithms to test.
        :param  delay    integer with the one-directional propagation delays to test.
        :param  iperf_runtime       Time to run the iperf clients in seconds.
    """
    print("*** Tests settings:\n - Algorithm: {0}\n - delay: {1}\n - Iperf runtime: {2}\n"
          .format(alg, delay, iperf_runtime))
    #for alg in algs:
    print('*** Starting test for algorithm={0},delay={1}ms'.format(alg,delay))
    #for delay in delays:

    # Start tcp probe process
    #print('*** Starting tcpprobe recording...') remove this part for this project
    #tcpprobe_proc = start_tcpprobe('tcpprobe_{0}_{1}ms.txt'.format(alg, delay)) #

    # Create the net topology
    print('*** Creating topology for delay={0}ms...'.format(delay))
    topo =tcpTopo(delay=delay) #

    # Start mininet
    net = Mininet(topo)
    #net = Mininet_wifi(topo)
    net.start()

    # Get the hosts
    h1, h2 = net.get('h1', 'h2')
    host_addrs = dict({'h1': h1.IP(), 'h2': h2.IP()})
    print('Host addrs: {0}'.format(host_addrs))

    # Run iperf
    popens = dict()
    print("*** Starting iperf servers h2...")
    popens[h2] = h2.popen(['iperf', '-s', '-p', '5001', '-w', '16m'])

    print("*** Starting iperf client h1...")
    popens[h1] = h1.popen('iperf -c {0} -p 5001 -i 1 -w 16m -M 1460 -N -Z {1} -t {2} -y C > \
                                   iperf_{1}_{3}_{4}ms.txt'
                                  .format(h2.IP(), alg, iperf_runtime, 'h1-h2', delay), shell=True)

    # Delay before starting the second iperf proc

    # Wait for clients to finish sending data
    print("*** Waiting {0}sec for iperf clients to finish...".format(iperf_runtime))

    popens[h1].wait()

    # Terminate the servers and tcpprobe subprocesses
    print('*** Terminate the iperf servers and tcpprobe processes...')
    popens[h2].terminate()

    #tcpprobe_proc.terminate()

    popens[h2].wait()
   
    #tcpprobe_proc.wait()
    #clean_tcpprobe_procs()

    print("*** Stopping test...")
    net.stop()

    print('*** Processing data...')
    #data_cwnd = parse_tcpprobe_data(alg, delay, host_addrs)
    data= parse_iperf_data(alg, delay, host_addrs)

    #draw_cwnd_plot(data_cwnd['h1']['time'], data_cwnd['h1']['cwnd'], data_cwnd['h3']['time'], data_cwnd['h3']['cwnd'], alg, delay)
    draw_BR_plot(data['h1']['time'], data['h1']['Mbps'], alg, delay)


if __name__ == '__main__':
        # Run tests
    setLogLevel('info')
    if (len(sys.argv)!=4):
       print("not enough arguments: python tcp_test.py algorithm delays iperf_runtime , exit")
       exit(1)
       #tcp_tests()
    else:
       tcp_tests(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
