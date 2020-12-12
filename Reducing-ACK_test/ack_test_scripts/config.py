#data & ack send link
sender_data_ip = "10.0.0.2"
receiver_data_ip = "10.0.0.1"

#wifi_mode 802.  11b/11g/11n/11ac
wifi_mode = "11g"
#test time length each time
test_time = 10
#rerun test times
test_times = 1

#udp baseline
"""
To test the limit throughput
iperf test the bw of two Mobile Stations
iperf3 -s /iperf3 -c 10.0.0.2  
iperf -u -s /iperf -c 10.0.0.2 -t 60 -i 1 -b 300M   

Rerun this test many times to get udp_baselines: 
11ac limit link bw: 590Mbps
11n limit link bw : 210Mbps
11g limit link bw : 26Mbps
11b limit link bw : 7Mbps
"""

wifi_mode_max_rate_dict = {'11b': 7 * 1024, '11g': 26 * 1024, '11n': 210 * 1024, '11ac': 590 * 1024}

#RTT condition to emulate
to_test_RTT = [1,10]
