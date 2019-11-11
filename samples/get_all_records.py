#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author         : Eric Winn
# @Email          : eng.eric.winn@gmail.com
# @Time           : 2019/11/11 1:49 PM
# @Version        : 1.0
# @File           : get_all_records
# @Software       : PyCharm

'''
安装：
pip install aliyun-python-sdk-alidns

参考：
https://help.aliyun.com/document_detail/67712.html?spm=a2c4g.11174283.6.674.bcaec8ca90FY8R
'''

import json
import logging
from aliyunsdkcore.client import AcsClient
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest

logging.basicConfig(
    level='INFO',
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging


def print_dict_key(item, key):
    region_id = item.get(key)
    return region_id


class Record:
    '''
    获取阿里云账户下所有的域名的解析信息

    参考文档：https://help.aliyun.com/document_detail/29776.html?spm=a2c4g.11186623.3.3.5a543b59RyjdAD
    如果传入access_key_id和access_key_secret则使用传入的access key建立连接
    返回一个域名的所有解析记录
    '''

    def __init__(self, access_key_id=None, access_key_secret=None):
        self.access_key = access_key_id
        self.secret = access_key_secret
        self.client = AcsClient(self.access_key, self.secret, "cn-hangzhou")
        self.currentPage = []
        self.TotalPageNum = 0
        self.PageSize = 500

    def __do_action(self, request):
        try:
            response = self.client.do_action_with_exception(request)
        except Exception as e:
            logger.error(e)
            return
        return json.loads(str(response, encoding='utf-8'))

    def __get_total_page_num(self, domainName, PageNum=1, PageSize=1):
        '''
        获取解析记录页数
        :param domainName: 域名
        :return:
        '''
        request = DescribeDomainRecordsRequest()
        request.set_DomainName(domainName)
        request.set_PageNumber(PageNum)
        request.set_PageSize(PageSize)
        response = self.__do_action(request)
        if self.TotalPageNum != 0:
            return response['DomainRecords']['Record']

        else:
            if int(response['TotalCount']) % self.PageSize != 0:
                self.TotalPageNum = int(response['TotalCount'] / self.PageSize) + 1
            else:
                self.TotalPageNum = int(response['TotalCount'] / self.PageSize)
            return self.TotalPageNum

    def get_records(self, domainName):
        '''
        获取解析记录
        :param domainName:
        :return: 本域名下所有的解析信息
        '''
        self.TotalPageNum = 0
        self.PageSize = 100
        records_list = []
        self.__get_total_page_num(domainName)
        for p in range(1, self.TotalPageNum + 1):
            records_list.extend(self.__get_total_page_num(domainName, p, self.PageSize))
        return records_list


if __name__ == '__main__':
    # TODO: 请填入阿里云账户的Access key ID 和Secret
    record = Record('YOUR-ACCESS-KEY-ID', 'YOUR-ACCESS-KEY-SECRET')
    records_list = record.get_records('YOUR-DOMAIN')
    print(records_list)
