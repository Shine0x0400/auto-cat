# coding=utf-8
import datetime
import sys

import requests
from bs4 import BeautifulSoup

from pyh import *

# 中文
reload(sys)
sys.setdefaultencoding('utf-8')

pay_token = 'a121208f2c7648279f122ae7d8e3f656'
# cat_url = 'http://cat.vip.sankuai.com/cat/r/app?query1=2017-08-18;6724;;;845;2;1;;;10;00:00;23:59&query2=2017-08-18;6724;;;845;8;1;;;10;00:00;23:59&type=request&groupByField=&sort=&op=linechartJson&token=' + pay_token

command_all_sharked = 6724  # paycenter_sharked_android_all
command_all_sharked_with_domain = 713  # paycenter_sharked_android_all_with_domain
command_all_sharked_without_domain = 1842  # paycenter_sharked_android_all_without_domain
app_meituan = 10
version_meituan = 854
network_shark_cip = 2
network_shark_http = 3
network_normal_http = 8

statistics_dict = {}  # path--CommandStatistics
sorted_commands = []  # sorted by request count


class ConnectionStatistics:
    """网络连接数据"""

    def __init__(self, connection):
        self.connection = connection
        self.count = 0
        self.success_rate = 0
        self.time_avg = -1
        self.send_pkg_avg = -1
        self.recv_pkg_avg = -1


class CommandStatistics:
    def __init__(self, command):
        self.command = command
        self.shark_cip_statistics = ConnectionStatistics("shark_cip")
        self.shark_http_statistics = ConnectionStatistics("shark_http")
        self.normal_http_statistics = ConnectionStatistics("normal_http")


def get_no_domain_path(raw_path):
    return raw_path.replace("pay.meituan.com", "", 1)


def request_commands_statistics(date, network_type):
    """抓取指定日期指定网络连接类型下各命令字的数据"""
    if network_type == network_shark_cip:
        network_name = "shark_cip"
        attr_name = 'shark_cip_statistics'
        command = command_all_sharked_with_domain
    elif network_type == network_normal_http:
        network_name = "normal_http"
        attr_name = 'normal_http_statistics'
        command = command_all_sharked_without_domain
    elif network_type == network_shark_http:
        network_name = "shark_http"
        attr_name = 'shark_http_statistics'
        command = command_all_sharked_with_domain
    else:
        print "Wrong network type passed in: " + network_type
        return

    url = "http://cat.dianpingoa.com/cat/r/app?op=groupDetails&query1=%s;%d;;;%d;%d;1;;;%d;00:00;23:59&sort=request" % (
        date, command, version_meituan, network_type, app_meituan)
    print network_name + ' url: ' + url
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    trs = soup.find_all(id='web_content')[0].find_all('tbody')[0].find_all('tr')
    for tr in trs:
        tds = tr.find_all('td')
        path = get_no_domain_path(str(tds[0].contents[0].contents[0]))

        if statistics_dict.has_key(path):
            command = statistics_dict.get(path)
        else:
            command = CommandStatistics(path)
            statistics_dict[path] = command

        connect = ConnectionStatistics(network_name)
        connect.success_rate = str(tds[1].contents[0])
        connect.count = int(str(tds[2].contents[0]).replace(',', ''))
        connect.time_avg = str(tds[3].contents[0])
        connect.send_pkg_avg = str(tds[4].contents[0])
        connect.recv_pkg_avg = str(tds[5].contents[0])

        setattr(command, attr_name, connect)


def generate_html(date):
    page = PyH('PayAndroidCat')
    page << '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
    mydiv = page << div(style="text-align:center")
    mydiv << h3('CAT 支付长短连数据(Android) ' + date)
    mydiv << h5('数据统计自美团' + str(version_meituan))
    mytab = page << table(border="1", cellpadding="3", cellspacing="0", style="margin:auto")
    tr1 = mytab << tr(bgcolor="lightgrey")
    tr1 << th('命令字') + th('通道') + th('请求数') + th('平均时间(ms)') + th('成功率') + th('平均发包(B)') + th('平均回包(B)')
    for idx, c in enumerate(sorted_commands):
        colored = ((idx % 2) != 0)
        if c.shark_cip_statistics.count > 0:
            conn = c.shark_cip_statistics
            tr2 = mytab << tr()
            if colored:
                tr2.attributes['bgcolor'] = 'lightyellow'
            tr2 << td(c.command) + td(conn.connection) + td(conn.count) + td(conn.time_avg) + td(
                conn.success_rate) + td(conn.send_pkg_avg) + td(conn.recv_pkg_avg)
        if c.normal_http_statistics.count > 0:
            conn = c.normal_http_statistics
            tr2 = mytab << tr()
            if colored:
                tr2.attributes['bgcolor'] = 'lightyellow'
            tr2 << td(c.command) + td(conn.connection) + td(conn.count) + td(conn.time_avg) + td(
                conn.success_rate) + td(conn.send_pkg_avg) + td(conn.recv_pkg_avg)
        if c.shark_http_statistics.count > 0:
            conn = c.shark_http_statistics
            tr2 = mytab << tr()
            if colored:
                tr2.attributes['bgcolor'] = 'lightyellow'
            tr2 << td(c.command) + td(conn.connection) + td(conn.count) + td(conn.time_avg) + td(
                conn.success_rate) + td(conn.send_pkg_avg) + td(conn.recv_pkg_avg)

    # page.printOut(date + '_PayAndroidCat.html', ec='GBK')
    page.printOut(date + '_PayAndroidCat.html', ec='UTF-8')


if __name__ == '__main__':
    yesterday = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d")

    request_commands_statistics(yesterday, network_shark_cip)
    request_commands_statistics(yesterday, network_normal_http)

    # sort by request count
    sorted_commands = sorted(statistics_dict.itervalues(), key=lambda
        x: x.shark_cip_statistics.count + x.normal_http_statistics.count + x.shark_http_statistics.count, reverse=True)

    generate_html(yesterday)
    print('gaga')
