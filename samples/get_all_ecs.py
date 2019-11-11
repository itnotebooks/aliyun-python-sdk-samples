#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author         : Eric Winn
# @Email          : eng.eric.winn@gmail.com
# @Time           : 2019/11/11 1:49 PM
# @Version        : 1.0
# @File           : get_all_ecs
# @Software       : PyCharm


'''
安装：
pip install aliyun-python-sdk-ecs

参考：
https://help.aliyun.com/document_detail/25609.html?spm=a2c4g.11174283.6.1341.119052feDvILXq
https://help.aliyun.com/document_detail/25506.html?spm=a2c4g.11186623.6.1162.477c49baOuAWJA
https://help.aliyun.com/document_detail/25514.html?spm=a2c4g.11186623.6.1216.39a5431dHF33HN
'''

import json
import logging
from multiprocessing import Pool
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.DescribeRegionsRequest import DescribeRegionsRequest
from aliyunsdkecs.request.v20140526.DescribeDisksRequest import DescribeDisksRequest

logging.basicConfig(
    level='INFO',
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging


def print_dict_key(item, key):
    region_id = item.get(key)
    return region_id


class ECS:
    '''
    获取阿里云当前账户下所有的ECS主机及其详细信息
    参考文档：https://help.aliyun.com/document_detail/25506.html?spm=a2c4g.11186623.6.1162.477c49baOuAWJA
    参考文档：https://help.aliyun.com/document_detail/25514.html?spm=a2c4g.11186623.6.1216.39a5431dHF33HN
    '''

    def __init__(self, access_key_id=None, access_key_secret=None):
        self.access_key = access_key_id
        self.secret = access_key_secret
        self.client = None
        self.currentPage = []
        self.regionList = []
        self.instance_list_total = []
        self.disk_list_total = []
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

    def __get_total_page_num(self, PageNum=1, PageSize=1):
        '''
        获取ECS总数，及当前页ECS列表
        :param PageNum: 页ID
        :param PageSize: 页大小
        :return:
        '''
        request = DescribeInstancesRequest()
        request.set_PageNumber(PageNum)
        request.set_PageSize(PageSize)
        response = self.__do_action(request)
        if self.TotalPageNum != 0:
            ins_obj = response['Instances']['Instance']
            self.instance_list_total.extend(ins_obj)
            return

        else:
            if int(response['TotalCount']) % self.PageSize != 0:
                self.TotalPageNum = int(response['TotalCount'] / self.PageSize) + 1
            else:
                self.TotalPageNum = int(response['TotalCount'] / self.PageSize)
            return self.TotalPageNum

    def __get_disk_total_page_num(self, PageNum=1, PageSize=1):
        request = DescribeDisksRequest()
        request.set_PageSize(PageSize)
        request.set_PageNumber(PageNum)
        response = self.__do_action(request)

        if self.TotalPageNum != 0:
            ins_obj = response['Disks']['Disk']
            self.disk_list_total.extend(ins_obj)
            return

        else:
            if int(response['TotalCount']) % self.PageSize != 0:
                self.TotalPageNum = int(response['TotalCount'] / self.PageSize) + 1
            else:
                self.TotalPageNum = int(response['TotalCount'] / self.PageSize)
            return self.TotalPageNum

    def __get_ecs_of_region(self, region):
        '''
        按区获取
        :param region:
        :return:
        '''
        self.TotalPageNum = 0
        self.__get_client(region)
        self.__get_total_page_num()
        # self.instance_list_obj.clear()
        list(map(self.__get_total_page_num, range(1, self.TotalPageNum + 1), [self.PageSize] * self.TotalPageNum))
        return

    def __get_disk_of_region(self, region):
        '''
        按区获取硬盘
        :param region:
        :return:
        '''
        self.TotalPageNum = 0
        self.__get_client(region)
        self.__get_disk_total_page_num()
        list(map(self.__get_disk_total_page_num, range(1, self.TotalPageNum + 1), [self.PageSize] * self.TotalPageNum))
        return

    def translate(self, ins):
        '''
        将接口返回的数据翻译成库字段，便于批量插入
        :param ins:
        :return:
        '''

        instrance = {}
        try:
            instrance['disk'] = 0
            instrance['hostname'] = ins['HostName']

            if ins.get('NetworkInterfaces'):
                instrance['host_ip'] = ins['NetworkInterfaces']['NetworkInterface'][0]['PrimaryIpAddress']

            if ins['PublicIpAddress'].get('IpAddress'):
                ip = ins['PublicIpAddress'].get('IpAddress', '')
                instrance['public_ip'] = ip[0]

            if ins.get('NetworkInterfaces'):
                instrance['mac'] = ins['NetworkInterfaces']['NetworkInterface'][0]['MacAddress']

            instrance['os'] = ins['OSNameEn']
            instrance['cpu'] = ins['Cpu']
            instrance['memory'] = int(ins['Memory'] / 1024)
            instrance['sn'] = ins['SerialNumber']

            instrance['instance_id'] = ins['InstanceId']
            instrance['instance_name'] = ins['InstanceName']

            instrance['create_time'] = ins['CreationTime']
            instrance['expiration_time'] = ins['ExpiredTime']
            instrance['zone'] = ins['ZoneId']
            instrance['region'] = ins['RegionId']
            instrance['status'] = ins['Status']
            if ins['Status'] != 'Running':
                instrance['power_state'] = 'poweredOff'
            else:
                instrance['power_state'] = 'poweredOn'

            instrance['ostype'] = ins['OSType']
            instrance['instancechargetype'] = ins['InstanceChargeType']
            instrance['internetchargetype'] = ins['InternetChargeType']
            instrance['salecycle'] = ins.get('SaleCycle', '')
            instrance['comment'] = ins.get('Description', '')

            instrance['specs'] = {
                'name': ins['InstanceType'],
                'family': ins['InstanceTypeFamily'],
                'cpu': ins['Cpu'],
                'memory': ins['Memory']
            }
        except Exception as e:
            logger.error(e)
        return instrance

    def get_ecs(self):
        '''
        获取所有ECS信息
        :return:
        '''

        list(map(self.__get_ecs_of_region, self.regionList))
        pool = Pool(50)
        ins_list_total = list(pool.map(self.translate, self.instance_list_total))
        return ins_list_total

    def get_disk(self):
        '''
        获取所有硬盘信息
        :return:
        '''

        self.PageSize = 100
        list(map(self.__get_disk_of_region, self.regionList))

        return self.disk_list_total

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
    ecs = ECS('YOUR-ACCESS-KEY-ID', 'YOUR-ACCESS-KEY-SECRET')
    ecs.get_region()

    # 获取所有区域下的ECS实例及其信息
    print(ecs.get_ecs())

    # 获取所有区域下的磁盘信息
    print(ecs.get_disk())
