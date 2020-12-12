To run the test on TCP-TACK, first make sure that you have correctly installed Mininet-wifi.

Attention that Mininet must be run with "sudo".

The TCP-TACK_test file is the Mininet script file.

Run by command line: "sudo python TCP-TACK_test.py"

This test is not purely carried out by python scripts, you also need to run command lines which can be found in the file named "CLT".

The throughput/ACK analysis need to capture the traffic and then parse the ".pcap" file.
In this case, you need to turn up the interface "hwsim0" and launch wireshark with "sudo".

This test, in fact, uses UDP to simulate TCP behaviors and such simulation is suggested by the "TCP-TACK" paper. 