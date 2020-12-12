

    cd client   or    cd server

    export LD_LIBRARY_PATH=./  (this should be done in both server and client folders to enable the path)


    ./server -s server_ip -p server_port -r testcase001

    ./client -c server_ip -p server_port -r testcase001
