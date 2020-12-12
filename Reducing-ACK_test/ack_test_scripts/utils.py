import datetime
import config
import time
import os

def cal_pack_rate(max_rate,RTT,wifi_mode):
    """
    :param max_rate:
    :return: rate Kbps
    """
    if wifi_mode == 'b' and RTT == 10:
        pack_cnt = (max_rate * 1024) / ((1472 + 52) * 8)

    else:
        pack_cnt = 1*1000*4 / RTT
    pack_data_cnt = int(float((max_rate * 1024 - pack_cnt * 52 * 8) / (1472 * 8)))
    pack_data_send_rate = 1472 * pack_data_cnt * 8 / 1024
    pack_send_rate = 52 * pack_cnt * 8 / 1024
    # print pack_cnt,pack_data_cnt,pack_data_send_rate,pack_send_rate
    print pack_cnt

    return pack_send_rate,pack_data_send_rate

def cal_ack_rate(max_rate):
    """
    :param max_rate:
    :return: rate Kbps
    """
    k = [1, 2, 4, 8, 16]
    ack_cnt = [(max_rate * 1024) / ((1472 * n + 52) * 8) for n in k]
    ack_data_cnt = [(max_rate * 1024) * n / ((1474 * n + 52) * 8) for n in k]
    ack_send_rate = [52 * m * 8 / 1024 for m in ack_cnt]
    ack_data_send_rate = [1472 * m * 8 / 1024 for m in ack_data_cnt]
    # print ack_cnt,ack_data_cnt,ack_send_rate,ack_data_send_rate
    print ack_cnt
    return ack_send_rate,ack_data_send_rate
