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

cat_url = 'http://cat.dianpingoa.com/cat/r/app?op=dailyApiLine&query1=%s;%d;;;;;;;;;%s;00:00;00:00&query2=&type=%s&groupByField=platform&sort='

command_dict = {'/hellopay/dispatcher': 7108, '/cashier/dispatcher': 548, '/cashier/gohellopay': 7109,
                '/cashier/directpay': 7107, '/hellopay/bindpay': 7110, '/conch/wallet/walletmain': 7111}

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

    cmd_id = command_dict.get(cmd)
    if statistics_dict.has_key(cmd):
        command = statistics_dict.get(cmd)
    else:
        command = CommandStatistics(cmd)
        statistics_dict[cmd] = command

    crawling_net_rate(cmd_id, command)
    crawling_biz_rate(cmd_id, command)


def crawling_net_rate(cmd_id, command_stats):
    """crawling network success rate and other statistics"""
    rate_url = cat_url % (start, cmd_id, end, 'success')
    resp = requests.get(rate_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    trs = soup.find_all(id='comparison_content')[0].find_all('tbody')[0].find_all('tr')
    for tr in trs:
        tds = tr.find_all('td')
        if tds[3].get_text() == cat_platform_ios:
            platform = command_stats.ios
            platform.net_rate = tds[7].get_text()
            platform.count = int(str(tds[8].get_text()).replace(',', ''))
            platform.time_avg = tds[9].get_text()
            platform.send_pkg_avg = tds[10].get_text()
            platform.recv_pkg_avg = tds[11].get_text()
        elif tds[3].get_text() == cat_platform_android:
            platform = command_stats.android
            platform.net_rate = tds[7].get_text()
            platform.count = int(str(tds[8].get_text()).replace(',', ''))
            platform.time_avg = tds[9].get_text()
            platform.send_pkg_avg = tds[10].get_text()
            platform.recv_pkg_avg = tds[11].get_text()
    total_tds = soup.find_all(id='web_content')[0].find_all('tbody')[0].find_all('tr')[0].find_all('td')
    platform = command_stats.all_platform
    platform.net_rate = total_tds[1].get_text()
    platform.count = int(str(total_tds[2].get_text()).replace(',', ''))
    platform.time_avg = total_tds[3].get_text()
    platform.send_pkg_avg = total_tds[4].get_text()
    platform.recv_pkg_avg = total_tds[5].get_text()


def crawling_biz_rate(cmd_id, command_stats):
    """crawling business success rate"""
    rate_url = cat_url % (start, cmd_id, end, 'businessSuccess')
    resp = requests.get(rate_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    trs = soup.find_all(id='comparison_content')[0].find_all('tbody')[0].find_all('tr')
    for tr in trs:
        tds = tr.find_all('td')
        if tds[3].get_text() == cat_platform_ios:
            platform = command_stats.ios
            platform.biz_rate = tds[7].get_text()
        elif tds[3].get_text() == cat_platform_android:
            platform = command_stats.android
            platform.biz_rate = tds[7].get_text()
    total_tds = soup.find_all(id='web_content')[0].find_all('tbody')[0].find_all('tr')[0].find_all('td')
    platform = command_stats.all_platform
    platform.biz_rate = total_tds[1].get_text()


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
        if c.android.count > 0:
            conn = c.android
            tr2 = mytab << tr()
            if colored:
                tr2.attributes['bgcolor'] = 'lightyellow'
            tr2 << td('') + td(conn.platform) + td(conn.count) + td(conn.time_avg) + td(conn.net_rate) + td(
                conn.biz_rate) + td(conn.send_pkg_avg) + td(conn.recv_pkg_avg)
        if c.ios.count > 0:
            conn = c.ios
            tr2 = mytab << tr()
            if colored:
                tr2.attributes['bgcolor'] = 'lightyellow'
            tr2 << td('') + td(conn.platform) + td(conn.count) + td(conn.time_avg) + td(conn.net_rate) + td(
                conn.biz_rate) + td(conn.send_pkg_avg) + td(conn.recv_pkg_avg)
        if c.all_platform.count > 0:
            conn = c.all_platform
            tr2 = mytab << tr()
            if colored:
                tr2.attributes['bgcolor'] = 'lightyellow'
            tr2 << td(c.command) + td(conn.platform) + td(conn.count) + td(conn.time_avg) + td(conn.net_rate) + td(
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

    for key in command_dict.keys():
        crawling_and_save(key)

    # sort by request count
    sorted_commands = sorted(statistics_dict.itervalues(), key=lambda x: x.all_platform.count, reverse=True)

    generate_html(kind, start, end)

    print 'gaga'
