This folder contains the files related to the bandwidth test on ACK frequencies.

Make sure that you have correctly installed Mininet-wifi.

Mininet must run with "sudo".

In the "ack_test_scripts" filder, run "sudo python ack_test_1.py"

The default test is based on IEEE 802.11g network.

In fact, we find that "11n" or "11ac" is not correctly configured in the Miininet-wifi platform.

If you want to change the test time, wifi modes, or other parameters, configure the "config.py" file.

It is supposed that Mininet-wifi topology has the following configuration:

"sta1-ap1-sta2", "ap1-c1".

"sta1.IP = 10.0.0.1", "sta2.IP = 10.0.0.2".
