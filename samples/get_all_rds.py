#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author         : Eric Winn
# @Email          : eng.eric.winn@gmail.com
# @Time           : 2019/11/11 1:49 PM
# @Version        : 1.0
# @File           : get_all_rds
# @Software       : PyCharm


'''
安装：
pip install aliyun-python-sdk-rds

参考：
https://help.aliyun.com/document_detail/25609.html?spm=a2c4g.11174283.6.1341.119052feDvILXq
https://help.aliyun.com/document_detail/26232.html?spm=a2c4g.11186623.6.1450.57ea75abVgYvHr
https://help.aliyun.com/document_detail/26231.html?spm=a2c4g.11186623.6.1449.760a75abInu9sW
'''

import json
import logging
from multiprocessing import Pool
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.DescribeRegionsRequest import DescribeRegionsRequest
from aliyunsdkrds.request.v20140815.DescribeDBInstancesRequest import DescribeDBInstancesRequest
from aliyunsdkrds.request.v20140815.DescribeDBInstanceAttributeRequest import DescribeDBInstanceAttributeRequest

logging.basicConfig(
    level='INFO',
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging


def print_dict_key(item, key):
    region_id = item.get(key)
    return region_id


class RDS:
    '''
    获取阿里云当前账户下所有的RDS实例及其详细信息
    参考文档：https://help.aliyun.com/document_detail/26232.html?spm=a2c4g.11186623.6.1450.57ea75abVgYvHr
    参考文档：https://help.aliyun.com/document_detail/26231.html?spm=a2c4g.11186623.6.1449.760a75abInu9sW
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

    def __get_total_page_num(self, PageNum=1, PageSize=1):
        '''
        获取RDS总数，及当前页RDS列表
        :param PageNum: 页ID
        :param PageSize: 页大小
        :return:
        '''
        request = DescribeDBInstancesRequest()
        request.set_PageNumber(PageNum)
        request.set_PageSize(PageSize)
        response = self.__do_action(request)
        if self.TotalPageNum != 0:
            ins_obj = response['Items']['DBInstance']
            self.instance_list_total.extend(ins_obj)
            return
        else:
            if int(response['TotalRecordCount']) % self.PageSize != 0:
                self.TotalPageNum = int(response['TotalRecordCount'] / self.PageSize) + 1
            else:
                self.TotalPageNum = int(response['TotalRecordCount'] / self.PageSize)
            return self.TotalPageNum

    def __get_rds_of_region(self, region):
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

    def __get_rds_ids(self):
        '''
        获取所有ECS信息
        :return:
        '''

        list(map(self.__get_rds_of_region, self.regionList))
        self.instance_ids_list = list(
            map(print_dict_key, self.instance_list_total, ['DBInstanceId'] * len(self.instance_list_total)))
        self.instance_list_total = []
        return self.instance_ids_list

    def __get_rds_attribute(self, ins_id):
        request = DescribeDBInstanceAttributeRequest()
        request.set_DBInstanceId(ins_id)
        response = self.__do_action(request)
        self.instance_list_total.extend(response['Items']['DBInstanceAttribute'])

    def translate(self, ins):
        '''
        将接口返回的数据翻译成库字段，便于批量插入
        :param ins:RDS Instance ID
        :return: 与表字段匹配的Mapping
        '''

        instrance = {}
        try:
            instrance['instance_id'] = ins['DBInstanceId']
            instrance['instance_name'] = ins.get('DBInstanceDescription')
            instrance['instance_type'] = ins.get('DBInstanceDescription')
            instrance['instancenet_type'] = ins.get('DBInstanceNetType')
            instrance['vpc_cloud_instance_id'] = ins.get('VpcCloudInstanceId')
            instrance['vpc_id'] = ins.get('VpcId')
            instrance['connection_mode'] = ins.get('ConnectionMode')
            instrance['vswitch_id'] = ins.get('VSwitchId')
            instrance['host_address'] = ins.get('ConnectionString')
            instrance['port'] = ins.get('Port')
            instrance['engine'] = ins.get('Engine')
            instrance['engine_version'] = ins.get('EngineVersion')
            instrance['status'] = ins.get('DBInstanceStatus')
            instrance['lock_mode'] = ins.get('LockMode')

            # 如果有被锁定，则取其原因
            if ins.get('LockReason'):
                instrance['lock_reason'] = ins.get('LockReason')

            instrance['resource_group_id'] = ins.get('ResourceGroupId')
            instrance['zone'] = ins.get('ZoneId')
            instrance['region'] = ins.get('RegionId')

            instrance['category'] = ins.get('Category')

            # 如果有设置时区，则取值
            if ins.get('TimeZone'):
                instrance['timezone'] = ins.get('TimeZone')

            instrance['instancechargetype'] = ins.get('PayType')
            instrance['comment'] = ins.get('DBInstanceDescription')

            # 如果有只读实例，则取其ID
            if ins['ReadOnlyDBInstanceIds'].get('ReadOnlyDBInstanceId'):
                instrance['readonly_ins'] = ins['ReadOnlyDBInstanceIds'].get('ReadOnlyDBInstanceId')

            instrance['maintain_time'] = ins.get('MaintainTime')
            instrance['create_time'] = ins.get('CreationTime')
            instrance['expiration_time'] = ins.get('ExpireTime')

            instrance['cpu'] = ins.get('DBInstanceCPU')

            instrance['memory'] = int(ins.get('DBInstanceMemory')) / 1024

            instrance['disk'] = ins['DBInstanceStorage']

            # 规格
            instrance['specs'] = {
                'name': ins['DBInstanceClass'],
                'family': ins['DBInstanceClassType'],
                'cpu': instrance['cpu'],
                'memory': instrance['memory'],
                'max_conn': ins['MaxConnections'],
                'max_iops': ins['MaxIOPS'],
                'db_max_quantity': ins['DBMaxQuantity'],
                'account_max_quantity': ins['AccountMaxQuantity']
            }

        except Exception as e:
            logger.error(e)
        return instrance

    def get_rds(self):
        '''
        获取所有RDS信息
        :return:
        '''

        # 获取所有区域下的RDS实例ID
        self.__get_rds_ids()

        # 初始化连接
        self.__get_client()
        # 获取所有RDS详细配置信息
        list(map(self.__get_rds_attribute, self.instance_ids_list))
        # 字段翻译
        pool = Pool(50)
        instance_list_total = list(pool.map(self.translate, self.instance_list_total))
        return instance_list_total

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
    rds = RDS('YOUR-ACCESS-KEY-ID', 'YOUR-ACCESS-KEY-SECRET')
    rds.get_region()
    # 获取所有区域下的RDS实例及其信息
    print(rds.get_rds())
