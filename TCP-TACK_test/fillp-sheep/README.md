# FillP

FillP is a user-space transport protocol implementation based on [TACK](https://dl.acm.org/doi/abs/10.1145/3387514.3405850), aiming at improving the wireless/wired transfer performance by filling up the pipe while maintaining reliability and efficiency.

## Setup

    cd client   or    cd server

    export LD_LIBRARY_PATH=./  (this should be done in both server and client folders to enable the path)



## Transfer Data Stream

    ./server -s server_ip -p server_port -r testcase001

    ./client -c server_ip -p server_port -r testcase001
