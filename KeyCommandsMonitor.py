# coding=utf-8
"""
支付关键接口监控,周报&日报
"""
import argparse
import datetime
import sys

import requests
from bs4 import BeautifulSoup

from pyh import *

# 中文
reload(sys)
sys.setdefaultencoding('utf-8')

# http://cat.dianpingoa.com/cat/r/app?op=dailyApiLine&query1=2017-10-08;7110;;;;;1;;;;2017-10-08;00:00;00:00&query2=2017-10-08;7128;;;;;2;;;;2017-10-08;00:00;00:00&type=success&groupByField=&sort=
cat_url = 'http://cat.dianpingoa.com/cat/r/app?op=dailyApiLine&query1=%s;%d;;;;;1;;;;%s;00:00;00:00&query2=%s;%d;;;;;2;;;;%s;00:00;00:00&type=%s&groupByField=platform&sort='

command_dict_android = {'/hellopay/dispatcher': 7108, '/cashier/dispatcher': 548, '/cashier/gohellopay': 7109,
                        '/cashier/directpay': 7107, '/hellopay/bindpay': 7110, '/conch/wallet/walletmain': 7111}

command_dict_ios = {'/hellopay/dispatcher': 5652, '/cashier/dispatcher': 4848, '/cashier/gohellopay': 7129,
                    '/cashier/directpay': 1478, '/hellopay/bindpay': 7128, '/conch/wallet/walletmain': 5631}

cat_platform_ios = 'ios'
cat_platform_android = 'android'

statistics_dict = {}  # path--CommandStatistics
sorted_commands = []  # sorted by request count


class ConnectionStatistics:
    """特定平台网络连接数据"""

    def __init__(self, platform):
        self.platform = platform
        self.count = 0
        self.net_rate = 0
        self.biz_rate = 0
        self.time_avg = -1
        self.send_pkg_avg = -1
        self.recv_pkg_avg = -1


class CommandStatistics:
    """指定命令字数据"""

    def __init__(self, command):
        self.command = command
        self.ios = ConnectionStatistics("ios")
        self.android = ConnectionStatistics("android")
        self.all_platform = ConnectionStatistics("all")


def parse_args():
    parser = argparse.ArgumentParser(description='Generate weekly or daily report of key commands.')
    parser.add_argument('--kind', metavar='REPORT_KIND', choices=['weekly', 'daily'],
                        default='weekly',
                        help='indicate which kind report would be generated. Options are weekly and daily.')
    parser.add_argument('--workers', type=int, default=8,
                        help='number of workers to use, 8 by default.')
    return parser.parse_args()


def crawling_and_save(cmd):
    """crawling from CAT web page and save in out dict"""

    if statistics_dict.has_key(cmd):
        command = statistics_dict.get(cmd)
    else:
        command = CommandStatistics(cmd)
        statistics_dict[cmd] = command

    cmd_id_a = command_dict_android.get(cmd)
    cmd_id_i = command_dict_ios.get(cmd)

    rate_url = cat_url % (start, cmd_id_a, end, start, cmd_id_i, end, 'success')
    crawling_net_rate(rate_url, command)
    biz_url = cat_url % (start, cmd_id_a, end, start, cmd_id_i, end, 'businessSuccess')
    crawling_biz_rate(biz_url, command)


def crawling_net_rate(url, command_stats):
    """crawling network success rate and other statistics"""
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    trs = soup.find_all(id='web_content')[0].find_all('tbody')[0].find_all('tr')

    # save android stats
    tds = trs[0].find_all('td')
    platform = command_stats.android
    platform.net_rate = tds[1].get_text()
    platform.count = int(str(tds[2].get_text()).replace(',', ''))
    platform.time_avg = tds[3].get_text()
    platform.send_pkg_avg = tds[4].get_text()
    platform.recv_pkg_avg = tds[5].get_text()
    # save ios stats
    tds = trs[1].find_all('td')
    platform = command_stats.ios
    platform.net_rate = tds[1].get_text()
    platform.count = int(str(tds[2].get_text()).replace(',', ''))
    platform.time_avg = tds[3].get_text()
    platform.send_pkg_avg = tds[4].get_text()
    platform.recv_pkg_avg = tds[5].get_text()


def crawling_biz_rate(url, command_stats):
    """crawling business success rate"""
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    trs = soup.find_all(id='web_content')[0].find_all('tbody')[0].find_all('tr')
    # save android stats
    tds = trs[0].find_all('td')
    platform = command_stats.android
    platform.biz_rate = tds[1].get_text()
    # save ios stats
    tds = trs[1].find_all('td')
    platform = command_stats.ios
    platform.biz_rate = tds[1].get_text()


def generate_html(kind, start, end):
    page = PyH('PayCat')
    page << '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
    mydiv = page << div(style="text-align:center")
    date = start + '-' + end if (kind == 'weekly') else end
    mydiv << h3('支付关键接口监控 ' + date)
    mytab = page << table(border="1", cellpadding="3", cellspacing="0", style="margin:auto")
    tr1 = mytab << tr(bgcolor="lightgrey")
    tr1 << th('命令字') + th('平台') + th('请求数') + th('平均时间(ms)') + th('网络成功率') + th('业务成功率') + th('平均发包(B)') + th('平均回包(B)')
    for idx, c in enumerate(sorted_commands):
        colored = ((idx % 2) != 0)

        conn = c.android
        tr2 = mytab << tr()
        if colored:
            tr2.attributes['bgcolor'] = 'lightyellow'
        tr2 << td(c.command) + td(conn.platform) + td(format(conn.count, ',')) + td(conn.time_avg) + td(
            conn.net_rate) + td(conn.biz_rate) + td(conn.send_pkg_avg) + td(conn.recv_pkg_avg)

        conn = c.ios
        tr2 = mytab << tr()
        if colored:
            tr2.attributes['bgcolor'] = 'lightyellow'
        tr2 << td('') + td(conn.platform) + td(format(conn.count, ',')) + td(conn.time_avg) + td(conn.net_rate) + td(
            conn.biz_rate) + td(conn.send_pkg_avg) + td(conn.recv_pkg_avg)

    page.printOut(date + '_PayCat.html', ec='UTF-8')


if __name__ == '__main__':
    options = parse_args()
    kind = options.kind
    end = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d")
    if kind == 'weekly':
        start = (datetime.datetime.now() + datetime.timedelta(days=-7)).strftime("%Y-%m-%d")
    elif kind == 'daily':
        start = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d")
    else:
        raise Exception("Invalid kind", kind)
    print 'kind=%s\tstart=%s, end=%s' % (kind, start, end)

    for key in command_dict_android.keys():
        crawling_and_save(key)

    # sort by request count
    sorted_commands = sorted(statistics_dict.itervalues(), key=lambda x: x.ios.count + x.android.count, reverse=True)

    generate_html(kind, start, end)

    print 'gaga'
