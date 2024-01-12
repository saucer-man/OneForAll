#!/usr/bin/python3
# coding=utf-8

"""
OneForAll export from database module

:copyright: Copyright (c) 2019, Jing Ling. All rights reserved.
:license: GNU General Public License v3.0, see LICENSE for more details.
"""

import fire

from common import utils
from common.database import Database
from config.log import logger


def export_data(target, db=None, alive=False, limit=None, path=None, fmt='csv', show=False):
    """
    OneForAll export from database module

    Example:
        python3 export.py --target name --fmt csv --dir= ./result.csv
        python3 export.py --target name --tb True --show False
        python3 export.py --db result.db --target name --show False

    Note:
        --fmt csv/json (result format)
        --path   Result directory (default directory is ./results)

    :param str  target:  Table to be exported
    :param str  db:      Database path to be exported (default ./results/result.sqlite3)
    :param bool alive:   Only export the results of alive subdomains (default False)
    :param str  limit:   Export limit (default None)
    :param str  fmt:     Result format (default csv)
    :param str  path:    Result directory (default None)
    :param bool show:    Displays the exported data in terminal (default False)
    """

    database = Database(db)
    domains = utils.get_domains(target)
    datas = list()
    if domains:
        for domain in domains:
            table_name = domain.replace('.', '_')
            rows = database.export_data(table_name, alive, limit)
            if rows is None:
                continue
            data, _, _ = do_export(fmt, path, rows, show, domain, target)  # 这里将rows保存在csv中
            datas.extend(data)
    database.close()
    if len(domains) > 1:  # 只有target为文件名的时候，才会走到这里，oneforall.py用不到这个
        utils.export_all(alive, fmt, path, datas)
    return datas


def do_export(fmt, path, rows, show, domain, target):
    fmt = utils.check_format(fmt) # 检查导出格式csv
    path = utils.check_path(path, target, fmt) # 得到path,这里会根据域名生成一个 WindowsPath('C:/Users/yanq/Documents/OneForAll/results/saucer-man.com.csv')
    if show: # false
        print(rows.dataset)
    data = rows.export(fmt)  # rows是RecordCollection 对象，也就是数据库对象


    # 到这里之后data为
    # id,alive,request,resolve,url,subdomain,level,cname,ip,public,cdn,port,status,reason,title,banner,cidr,asn,org,addr,isp,source
    # 6,1,1,1,http://ai.saucer-man.com,ai.saucer-man.com,1,ai.saucer-man.com,8.219.203.196,1,1,80,200,OK,Welcome to nginx!,nginx/1.25.1,8.216.0.0/13,AS134963,Alibaba.com Singapore E-Commerce Private Limited,中国,阿里巴巴,CrtshQuery
    # 8,1,1,1,https://ai.saucer-man.com,ai.saucer-man.com,1,ai.saucer-man.com,8.219.203.196,1,1,443,200,OK,Welcome to nginx!,nginx/1.25.1,8.216.0.0/13,AS134963,Alibaba.com Singapore E-Commerce Private Limited,中国,阿里巴巴,CrtshQuery
    # 1,1,1,1,https://ai2.saucer-man.com,ai2.saucer-man.com,1,ai2.saucer-man.com,42.192.189.2,1,0,443,403,Forbidden,403 Forbidden,nginx/1.18.0 (Ubuntu),42.192.0.0/15,AS-,-,中国上海上海市,电信,CrtshQuery
    # 9,0,0,1,http://ai2.saucer-man.com,ai2.saucer-man.com,1,ai2.saucer-man.com,42.192.189.2,1,0,80,,"(MaxRetryError(""HTTPConnectionPool(host='ai2.saucer-man.com', port=80): Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x0000015EECA502E0>: Failed to establish a new connection: [WinError 10061] 由于目标计算机积极拒绝，无法连接。'))""),)",,,42.192.0.0/15,AS-,-,中国上海上海市,电信,CrtshQuery
    # 3,1,1,1,https://ai3.saucer-man.com,ai3.saucer-man.com,1,ai3.saucer-man.com,42.192.189.2,1,0,443,403,Forbidden,403 Forbidden,nginx/1.18.0 (Ubuntu),42.192.0.0/15,AS-,-,中国上海上海市,电信,CrtshQuery
    # 12,0,0,1,http://ai3.saucer-man.com,ai3.saucer-man.com,1,ai3.saucer-man.com,42.192.189.2,1,0,80,,"(MaxRetryError(""HTTPConnectionPool(host='ai3.saucer-man.com', port=80): Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x0000015EEC865A00>: Failed to establish a new connection: [WinError 10061] 由于目标计算机积极拒绝，无法连接。'))""),)",,,42.192.0.0/15,AS-,-,中国上海上海市,电信,CrtshQuery
    # 5,1,1,1,http://file.saucer-man.com,file.saucer-man.com,1,file.saucer-man.com,106.52.169.251,1,1,80,200,OK,File Browser,nginx/1.19.10,106.52.160.0/20,AS45090,Shenzhen Tencent Computer Systems Company Limited,中国广东省广州市,电信,FullHuntAPIQuery
    # 11,0,0,1,https://file.saucer-man.com,file.saucer-man.com,1,file.saucer-man.com,106.52.169.251,1,0,443,,"(MaxRetryError(""HTTPSConnectionPool(host='file.saucer-man.com', port=443): Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x0000015EEC7F90D0>: Failed to establish a new connection: [WinError 10061] 由于目标计算机积极拒绝，无法连接。'))""),)",,,106.52.160.0/20,AS45090,Shenzhen Tencent Computer Systems Company Limited,中国广东省广州市,电信,FullHuntAPIQuery
    # 2,1,1,1,https://saucer-man.com,saucer-man.com,0,saucer-man.com.w.kunlungr.com,58.218.215.165,1,1,443,200,OK,SAUCERMAN,"Tengine,cache37.l2cn3008[82,81,200-0,M], cache39.l2cn3008[83,0], kunlun2.cn5266[86,86,200-0,M], kunlun4.cn5266[90,0],PHP/7.4.33",58.218.208.0/20,AS4134,China Telecom,中国江苏省徐州市,电信,MySSLQuery
    # 7,1,1,1,http://saucer-man.com,saucer-man.com,0,saucer-man.com.w.kunlungr.com,58.218.215.165,1,1,80,200,OK,SAUCERMAN,"Tengine,cache37.l2cn3008[76,76,200-0,M], cache76.l2cn3008[77,0], kunlun2.cn5266[84,84,200-0,M], kunlun2.cn5266[86,0],PHP/7.4.33",58.218.208.0/20,AS4134,China Telecom,中国江苏省徐州市,电信,MySSLQuery
    # 4,1,1,1,http://www.saucer-man.com,www.saucer-man.com,1,www.saucer-man.com,106.52.169.251,1,0,80,200,OK,SAUCERMAN,"nginx/1.19.10,PHP/7.4.33",106.52.160.0/20,AS45090,Shenzhen Tencent Computer Systems Company Limited,中国广东省广州市,电信,CrtshQuery
    # 10,0,0,1,https://www.saucer-man.com,www.saucer-man.com,1,www.saucer-man.com,106.52.169.251,1,0,443,,"(MaxRetryError(""HTTPSConnectionPool(host='www.saucer-man.com', port=443): Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x0000015EEC612340>: Failed to establish a new connection: [WinError 10061] 由于目标计算机积极拒绝，无法连接。'))""),)",,,106.52.160.0/20,AS45090,Shenzhen Tencent Computer Systems Company Limited,中国广东省广州市,电信,CrtshQuery



    # 这里吧data的header行去掉，然后保存，不然每次都会追加保存header
    split_strings = data.split('\r\n', 1)
    header = split_strings[0] + '\r\n'
    data = split_strings[1]
    if fmt == 'csv':
        header = '\ufeff' + header

    # 如果文件不存在，则会创建一个csv，带上头和header
    if not path.exists() and fmt == 'csv':
        logger.log('ALERT', f'The {path} not exists and will be created')
        with open(path, 'w', errors='ignore', newline='') as file:
            file.write(header)


    utils.save_to_file(path, data) # 将data保存在path中，是直接采用file write方法实现的
    logger.log('ALERT', f'The subdomain result for {domain}: {path}')
    data = rows.as_dict()
    return data, fmt, path


if __name__ == '__main__':
    fire.Fire(export_data)
