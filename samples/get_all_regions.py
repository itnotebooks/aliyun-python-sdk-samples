#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author         : Eric Winn
# @Email          : eng.eric.winn@gmail.com
# @Time           : 2019/11/11 1:49 PM
# @Version        : 1.0
# @File           : get_all_regions
# @Software       : PyCharm


'''
安装：
pip install aliyun-python-sdk-ecs

参考：
https://help.aliyun.com/document_detail/25609.html?spm=a2c4g.11174283.6.1341.119052feDvILXq
'''

import json
import logging
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.DescribeRegionsRequest import DescribeRegionsRequest

logging.basicConfig(
    level='INFO',
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging


def print_dict_key(item, key):
    region_id = item.get(key)
    return region_id


class REGION:
    '''
    获取阿里云当前账户下所有的区域ID及其详细信息
    参考文档：https://help.aliyun.com/document_detail/25609.html?spm=a2c4g.11174283.6.1341.119052feDvILXq
    '''

    def __init__(self, access_key_id=None, access_key_secret=None):
        self.access_key = access_key_id
        self.secret = access_key_secret
        self.client = None
        self.currentPage = []
        self.regionList = []
        self.instance_list_total = []
        self.instance_ids_list = []
        self.TotalPageNum = 0
        self.PageSize = 100

    def __get_client(self, region_id='cn-hangzhou'):
        self.client = AcsClient(self.access_key, self.secret, region_id)

    def __do_action(self, request):
        try:
            request.set_accept_format('json')
            response = self.client.do_action_with_exception(request)
        except Exception as e:
            logger.error(e)
            return
        return json.loads(str(response, encoding='utf-8'))

    def get_region(self):
        '''
        获取账户支持的所有区域id
        :return:
        '''
        self.__get_client()
        request = DescribeRegionsRequest()
        response = self.__do_action(request)
        region_list = response.get('Regions').get('Region')
        assert response is not None
        assert region_list is not None
        self.regionList = list(map(print_dict_key, region_list, ['RegionId'] * len(region_list)))
        return self.regionList


if __name__ == '__main__':
    # TODO: 请填入阿里云账户的Access key ID 和Secret
    record = REGION('YOUR-ACCESS-KEY-ID', 'YOUR-ACCESS-KEY-SECRET')
    regions_list = record.get_region()
    print(regions_list)
