#!/usr/bin/python3
# coding=utf-8

"""
OneForAll is a powerful subdomain integration tool

:copyright: Copyright (c) 2019, Jing Ling. All rights reserved.
:license: GNU General Public License v3.0, see LICENSE for more details.
"""

import fire
from datetime import datetime


import export
from brute import Brute
from common import utils, resolve, request
from modules.collect import Collect
from modules.srv import BruteSRV
from modules.finder import Finder
from modules.altdns import Altdns
from modules.enrich import Enrich
from modules import wildcard
from config import settings
from config.log import logger
from takeover import Takeover

yellow = '\033[01;33m'
white = '\033[01;37m'
green = '\033[01;32m'
blue = '\033[01;34m'
red = '\033[1;31m'
end = '\033[0m'

version = 'v0.4.5'
message = white + '{' + red + version + ' #dev' + white + '}'

oneforall_banner = f"""
OneForAll is a powerful subdomain integration tool{yellow}
             ___             _ _ 
 ___ ___ ___|  _|___ ___ ___| | | {message}{green}
| . |   | -_|  _| . |  _| .'| | | {blue}
|___|_|_|___|_| |___|_| |__,|_|_| {white}git.io/fjHT1

{red}OneForAll is under development, please update before each use!{end}
"""


class OneForAll(object):
    """
    OneForAll help summary page

    OneForAll is a powerful subdomain integration tool

    Example:
        python3 oneforall.py version
        python3 oneforall.py check
        python3 oneforall.py --target example.com run
        python3 oneforall.py --targets ./domains.txt run
        python3 oneforall.py --target example.com --alive False run
        python3 oneforall.py --target example.com --brute False run
        python3 oneforall.py --target example.com --port medium run
        python3 oneforall.py --target example.com --fmt csv run
        python3 oneforall.py --target example.com --dns False run
        python3 oneforall.py --target example.com --req False run
        python3 oneforall.py --target example.com --takeover False run
        python3 oneforall.py --target example.com --show True run

    Note:
        --port   small/medium/large  See details in ./config/setting.py(default small)
        --fmt    csv/json (result format)
        --path   Result path (default None, automatically generated)

    :param str  target:     One domain (target or targets must be provided)
    :param str  targets:    File path of one domain per line
    :param bool brute:      Use brute module (default True)
    :param bool dns:        Use DNS resolution (default True)
    :param bool req:        HTTP request subdomains (default True)
    :param str  port:       The port range to request (default small port is 80,443)
    :param bool alive:      Only export alive subdomains (default False)
    :param str  fmt:        Result format (default csv)
    :param str  path:       Result path (default None, automatically generated)
    :param bool takeover:   Scan subdomain takeover (default False)
    """
    def __init__(self, target=None, targets=None, brute=None, dns=None, req=None,
                 port=None, alive=None, fmt=None, path=None, takeover=None):
        self.target = target
        self.targets = targets
        self.brute = brute
        self.dns = dns
        self.req = req
        self.port = port
        self.alive = alive
        self.fmt = fmt
        self.path = path
        self.takeover = takeover
        self.domain = str()  # The domain currently being collected
        self.domains = set()  # All domains that are to be collected
        self.data = list()  # The subdomain results of the current domain
        self.datas = list()  # All subdomain results of the domain
        self.access_internet = False
        self.enable_wildcard = False

    def config_param(self):
        """
        Config parameter
        """
        if self.brute is None:
            self.brute = bool(settings.enable_brute_module)
        if self.dns is None:
            self.dns = bool(settings.enable_dns_resolve)
        if self.req is None:
            self.req = bool(settings.enable_http_request)
        if self.takeover is None:
            self.takeover = bool(settings.enable_takeover_check)
        if self.port is None:
            self.port = settings.http_request_port
        if self.alive is None:
            self.alive = bool(settings.result_export_alive)
        if self.fmt is None:
            self.fmt = settings.result_save_format
        if self.path is None:
            self.path = settings.result_save_path

    def check_param(self):
        """
        Check parameter
        """
        if self.target is None and self.targets is None:
            logger.log('FATAL', 'You must provide either target or targets parameter')
            exit(1)

    def export_data(self):
        """
        Export data from the database

        :return: exported data
        :rtype: list
        """
        return export.export_data(self.domain, alive=self.alive, fmt=self.fmt, path=self.path)

    def main(self):
        """
        OneForAll main process

        :return: subdomain results
        :rtype: list
        """
        utils.init_table(self.domain)  # 在sqllite数据库中创建一个新的table，这里后续就不创建了

        # 下面能不能上网 感觉不需要检查，先给注释了吧
        # if not self.access_internet:
        #     logger.log('ALERT', 'Because it cannot access the Internet, '
        #                         'OneForAll will not execute the subdomain collection module!')
        # if self.access_internet:
        # 下面检查是否存在泛解析，如果存在泛解析就不需要爆破了
        self.enable_wildcard = wildcard.detect_wildcard(self.domain)

        # 下面运行信息收集模块，也就是配置文件中写的模块
        collect = Collect(self.domain)
        collect.run()
        # 收集完了之后保存的是数据库和json好像没有csv


        # 下面通过枚举常见的SRV记录并做查询来收集子域srv
        srv = BruteSRV(self.domain)
        srv.run()


        # 下面是子域名爆破，这里先暂停了
        if self.brute:
            # Due to there will be a large number of dns resolution requests,
            # may cause other network tasks to be error
            brute = Brute(self.domain, word=True, export=False)
            brute.enable_wildcard = self.enable_wildcard
            brute.quite = True
            brute.run()

        utils.deal_data(self.domain) # 删除sqllite数据库中的子域的空数据和重复数据
        # Export results without resolve
        if not self.dns: # 使用DNS解析子域，默认为true，所以不会走这里
            self.data = self.export_data()
            self.datas.extend(self.data)
            return self.data

        self.data = utils.get_data(self.domain)  # 从数据库中得到data

        # print("self.data")
        # print(self.data) # [{'id': 1, 'alive': None, 'request': None, 'resolve': None, 'url': 'http://notes.saucer-man.com', 'subdomain': 'notes.saucer-man.com', 'port': 80, 'level': 1, 'cname': None, 'ip': None, 'public': None, 'cdn': None, 'status': None, 'reason': None, 'title': None, 'banner': None, 'header': None, 'history': None, 'response': None, 'ip_times': None, 'cname_times': None, 'ttl': None, 'cidr': None, 'asn': None, 'org': None, 'addr': None, 'isp': None, 'resolver': None, 'module': 'Certificate', 'source': 'CensysAPIQuery', 'elapse': 0.9, 'find': 6}, {'id': 2, 'alive': None, 'request': None, 'resolve': None, 'url': 'http://ai.saucer-man.com', 'subdomain': 'ai.saucer-man.com', 'port': 80, 'level': 1, 'cname': None, 'ip': None, 'public': None, 'cdn': None, 'status': None, 'reason': None, 'title': None, 'banner': None, 'header': None, 'history': None, 'response': None, 'ip_times': None, 'cname_times': None, 'ttl': None, 'cidr': None, 'asn': None, 'org': None, 'addr': None, 'isp': None, 'resolver': None, 'module': 'Certificate', 'source': 'CensysAPIQuery', 'elapse': 0.9, 'find': 6}, {'id': 3, 'alive': None, 'request': None, 'resolve': None, 'url': 'http://www.saucer-man.com', 'subdomain': 'www.saucer-man.com', 'port': 80, 'level': 1, 'cname': None, 'ip': None, 'public': None, 'cdn': None, 'status': None, 'reason': None, 'title': None, 'banner': None, 'header': None, 'history': None, 'response': None, 'ip_times': None, 'cname_times': None, 'ttl': None, 'cidr': None, 'asn': None, 'org': None, 'addr': None, 'isp': None, 'resolver': None, 'module': 'Certificate', 'source': 'CensysAPIQuery', 'elapse': 0.9, 'find': 6}, {'id': 4, 'alive': None, 'request': None, 'resolve': None, 'url': 'http://saucer-man.com', 'subdomain': 'saucer-man.com', 'port': 80, 'level': 0, 'cname': None, 'ip': None, 'public': None, 'cdn': None, 'status': None, 'reason': None, 'title': None, 'banner': None, 'header': None, 'history': None, 'response': None, 'ip_times': None, 'cname_times': None, 'ttl': None, 'cidr': None, 'asn': None, 'org': None, 'addr': None, 'isp': None, 'resolver': None, 'module': 'Certificate', 'source': 'CensysAPIQuery', 'elapse': 0.9, 'find': 6}, {'id': 5, 'alive': None, 'request': None, 'resolve': None, 'url': 'http://ai2.saucer-man.com', 'subdomain': 'ai2.saucer-man.com', 'port': 80, 'level': 1, 'cname': None, 'ip': None, 'public': None, 'cdn': None, 'status': None, 'reason': None, 'title': None, 'banner': None, 'header': None, 'history': None, 'response': None, 'ip_times': None, 'cname_times': None, 'ttl': None, 'cidr': None, 'asn': None, 'org': None, 'addr': None, 'isp': None, 'resolver': None, 'module': 'Certificate', 'source': 'CensysAPIQuery', 'elapse': 0.9, 'find': 6}, {'id': 6, 'alive': None, 'request': None, 'resolve': None, 'url': 'http://ai3.saucer-man.com', 'subdomain': 'ai3.saucer-man.com', 'port': 80, 'level': 1, 'cname': None, 'ip': None, 'public': None, 'cdn': None, 'status': None, 'reason': None, 'title': None, 'banner': None, 'header': None, 'history': None, 'response': None, 'ip_times': None, 'cname_times': None, 'ttl': None, 'cidr': None, 'asn': None, 'org': None, 'addr': None, 'isp': None, 'resolver': None, 'module': 'Certificate', 'source': 'CensysAPIQuery', 'elapse': 0.9, 'find': 6}]


        # Resolve subdomains
        utils.clear_data(self.domain)  # 删除表，这里不知道是为啥

        # 下面解析子域名的dns记录，A记录和ip地址等等
        self.data = resolve.run_resolve(self.domain, self.data)

        print("解析玩之后的data")
        print(self.data) # [{'id': 1, 'alive': None, 'request': None, 'resolve': 1, 'url': 'http://ai2.saucer-man.com', 'subdomain': 'ai2.saucer-man.com', 'port': 80, 'level': 1, 'cname': 'ai2.saucer-man.com', 'ip': '42.192.189.2', 'public': None, 'cdn': None, 'status': None, 'reason': 'OK', 'title': None, 'banner': None, 'header': None, 'history': None, 'response': None, 'ip_times': None, 'cname_times': None, 'ttl': '600', 'cidr': None, 'asn': None, 'org': None, 'addr': None, 'isp': None, 'resolver': '4.2.2.6:53', 'module': 'Certificate', 'source': 'CensysAPIQuery', 'elapse': 1.1, 'find': 6}, {'id': 2, 'alive': None, 'request': None, 'resolve': 1, 'url': 'http://saucer-man.com', 'subdomain': 'saucer-man.com', 'port': 80, 'level': 0, 'cname': 'saucer-man.com.w.kunlungr.com', 'ip': '58.218.215.165', 'public': None, 'cdn': None, 'status': None, 'reason': 'OK', 'title': None, 'banner': None, 'header': None, 'history': None, 'response': None, 'ip_times': None, 'cname_times': None, 'ttl': '60', 'cidr': None, 'asn': None, 'org': None, 'addr': None, 'isp': None, 'resolver': '4.2.2.2:53', 'module': 'Certificate', 'source': 'CensysAPIQuery', 'elapse': 1.1, 'find': 6}, {'id': 3, 'alive': None, 'request': None, 'resolve': 1, 'url': 'http://ai.saucer-man.com', 'subdomain': 'ai.saucer-man.com', 'port': 80, 'level': 1, 'cname': 'ai.saucer-man.com', 'ip': '8.219.203.196', 'public': None, 'cdn': None, 'status': None, 'reason': 'OK', 'title': None, 'banner': None, 'header': None, 'history': None, 'response': None, 'ip_times': None, 'cname_times': None, 'ttl': '600', 'cidr': None, 'asn': None, 'org': None, 'addr': None, 'isp': None, 'resolver': '1.1.1.1:53', 'module': 'Certificate', 'source': 'CensysAPIQuery', 'elapse': 1.1, 'find': 6}, {'id': 4, 'alive': None, 'request': None, 'resolve': 1, 'url': 'http://www.saucer-man.com', 'subdomain': 'www.saucer-man.com', 'port': 80, 'level': 1, 'cname': 'www.saucer-man.com', 'ip': '106.52.169.251', 'public': None, 'cdn': None, 'status': None, 'reason': 'OK', 'title': None, 'banner': None, 'header': None, 'history': None, 'response': None, 'ip_times': None, 'cname_times': None, 'ttl': '600', 'cidr': None, 'asn': None, 'org': None, 'addr': None, 'isp': None, 'resolver': '1.0.0.2:53', 'module': 'Certificate', 'source': 'CensysAPIQuery', 'elapse': 1.1, 'find': 6}, {'id': 5, 'alive': None, 'request': None, 'resolve': 1, 'url': 'http://ai3.saucer-man.com', 'subdomain': 'ai3.saucer-man.com', 'port': 80, 'level': 1, 'cname': 'ai3.saucer-man.com', 'ip': '42.192.189.2', 'public': None, 'cdn': None, 'status': None, 'reason': 'OK', 'title': None, 'banner': None, 'header': None, 'history': None, 'response': None, 'ip_times': None, 'cname_times': None, 'ttl': '600', 'cidr': None, 'asn': None, 'org': None, 'addr': None, 'isp': None, 'resolver': '1.0.0.2:53', 'module': 'Certificate', 'source': 'CensysAPIQuery', 'elapse': 1.1, 'find': 6}]



        # Save resolve results
        resolve.save_db(self.domain, self.data)  # 保存在数据库中

        # Export results without HTTP request
        # req 就是表示是否对子域名进行http请求，默认为true,一般不会走下面的判断
        if not self.req:
            self.data = self.export_data()
            self.datas.extend(self.data)
            return self.data

        if self.enable_wildcard:  # 如果存在泛解析，去掉泛解析的data，这里一般不会走到
            # deal wildcard
            self.data = wildcard.deal_wildcard(self.data)

        # HTTP request
        utils.clear_data(self.domain)  # 又删除数据库

        # 对子域名进行http请求，将结果保存在sql中
        request.run_request(self.domain, self.data, self.port)

        # Finder module
        # 开启finder模块,开启会从响应体和JS中再次发现子域(默认True)
        # 从数据库中取出resp，做正则匹配
        if settings.enable_finder_module:
            finder = Finder()
            finder.run(self.domain, self.data, self.port)

        # altdns module
        # 开启altdns模块,开启会利用置换技术重组子域再次发现新子域(默认True)
        if settings.enable_altdns_module:
            altdns = Altdns(self.domain)
            altdns.run(self.data, self.port)

        # Information enrichment module
        # # 开启enrich模块，开启会富化出信息，如ip的cdn，cidr，asn，org，addr和isp等信息
        if settings.enable_enrich_module:
            enrich = Enrich(self.domain)
            enrich.run()

        # 从数据库中取出数据，并且保存在csv文件中
        self.data = self.export_data()

        # self.datas一般为空
        self.datas.extend(self.data)

        # Scan subdomain takeover
        # 扫描子域名接管，默认为False
        if self.takeover:
            subdomains = utils.get_subdomains(self.data)
            takeover = Takeover(targets=subdomains)
            takeover.run()

        utils.clear_data(self.domain)  # 最后的最后，删除表，csv已经在上面保存过了
        return self.data

    def run(self):
        """
        OneForAll running entrance

        :return: All subdomain results
        :rtype: list
        """
        print(oneforall_banner) # 输出banner
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'[*] Starting OneForAll @ {dt}\n')
        logger.log('DEBUG', 'Python ' + utils.python_version())
        logger.log('DEBUG', 'OneForAll ' + version)
        utils.check_dep()  # 检查依赖，python版本等
        # self.access_internet = utils.get_net_env()  # 检查能不能上网，这里通过访问baidu什么的来决定
        # if self.access_internet and settings.enable_check_version:
        #     utils.check_version(version)  # 检查版本是否有更新
        logger.log('INFOR', 'Start running OneForAll')
        self.config_param()  # 配置参数，优先命令行，然后配置文件 api.py 和 setting.py
        self.check_param()  # 检查参数，这里只检查了target是否为空
        self.domains = utils.get_domains(self.target, self.targets)   # 读取单个target 或者targets文件 到self.domains，这里会验证domain的有效性
        count = len(self.domains)
        logger.log('INFOR', f'Got {count} domains')
        if not count:
            logger.log('FATAL', 'Failed to obtain domain')
            exit(1)
        for domain in self.domains:
            self.domain = utils.get_main_domain(domain)  # 得到域名的顶级域名，www.baidu.com  --> baidu.com
            self.main()  # 执行子域名查找的逻辑，结果保存在sql中
        if count > 1:
            utils.export_all(self.alive, self.fmt, self.path, self.datas)  # 导出datas的结果到csv中
        logger.log('INFOR', 'Finished OneForAll')

    @staticmethod
    def version():
        """
        Print version information and exit
        """
        print(oneforall_banner)
        exit(0)

    @staticmethod
    def check():
        """
        Check if there is a new version and exit
        """
        utils.check_version(version)
        exit(0)


if __name__ == '__main__':
    fire.Fire(OneForAll)
