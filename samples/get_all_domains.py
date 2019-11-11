#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author         : Eric Winn
# @Email          : eng.eric.winn@gmail.com
# @Time           : 2019/11/11 1:48 PM
# @Version        : 1.0
# @File           : get_all_domains
# @Software       : PyCharm

'''
安装：
pip install aliyun-python-sdk-domain

参考：
https://help.aliyun.com/document_detail/67712.html?spm=a2c4g.11174283.6.674.bcaec8ca90FY8R
'''

import json
import logging
from aliyunsdkcore.client import AcsClient
from aliyunsdkdomain.request.v20180129.QueryDomainListRequest import QueryDomainListRequest
from aliyunsdkdomain.request.v20180129.QueryDomainByInstanceIdRequest import QueryDomainByInstanceIdRequest

logging.basicConfig(
    level='INFO',
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging


class Domain:
    '''
    获取阿里云账户下所有的域名信息，包含域名注册信息、注册商、有效期、联系邮箱、dns Server、状态等信息

    参考文档：https://help.aliyun.com/document_detail/67712.html?spm=a2c4g.11174283.6.674.bcaec8ca90FY8R
    如果传入access_key_id和access_key_secret则使用传入的access key建立连接
    返回此账户下所有的域名信息
    '''

    def __init__(self, access_key=None, secret=None):
        self.page_size = 50
        self.access_key = access_key
        self.secret = secret
        self.client = AcsClient(self.access_key, self.secret, "cn-hangzhou")
        self.TotalPageNum = 0
        self.TotalItemNum = 0
        self.currentPage = []

    def __do_action(self, request):
        try:
            response = self.client.do_action_with_exception(request)
        except Exception as e:
            logger.error(e)
            return
        return json.loads(str(response, encoding='utf-8'))

    def __get_total_page_num(self, PageNum=1):
        '''
        获取总域名数，及当前页域名列表
        :param PageNum:
        :return:
        '''
        request = QueryDomainListRequest()
        request.set_accept_format('json')
        request.set_PageNum(PageNum)
        request.set_PageSize(int(self.page_size))
        response = self.__do_action(request)
        if response:
            self.currentPage = response['Data']['Domain']
            if PageNum == 1:
                self.TotalPageNum = int(response['TotalPageNum'])

    def __get_domainInfo(self, domainIns):
        '''
        获取域名详细注册信息，同whois查询结果
        :return:
        '''
        request = QueryDomainByInstanceIdRequest()
        request.set_InstanceId(domainIns)
        return self.__do_action(request)

    def __translate(self, domain):
        '''
        字段翻译，只获取需要的部分，便于入库
        :param domain:
        :return:
        '''
        domainInfo = {}
        domainInfo['name'] = domain['DomainName']
        domainInfo['domain_isp'] = 1
        domainInfo['domain_id'] = domain['InstanceId']
        domainInfo['domain_status'] = int(domain['DomainStatus'])
        domainInfo['registrant_type'] = int(domain['RegistrantType'])
        domainInfo['registration_date'] = domain['RegistrationDate']
        domainInfo['expiration_date'] = domain['ExpirationDate']
        info = self.__get_domainInfo(domain['InstanceId'])
        domainInfo['nameserver_master'] = info['DnsList']['Dns'][0]
        domainInfo['nameserver_slave'] = info['DnsList']['Dns'][1]
        domainInfo['owner'] = info['ZhRegistrantOrganization']
        domainInfo['email'] = info['Email']
        domainInfo['verification_status'] = info['DomainNameVerificationStatus']
        return domainInfo

    def get_domainListInfo(self):
        domainListInfo = []
        if not self.client: return []
        self.__get_total_page_num()
        for page in range(1, self.TotalPageNum + 1):
            self.__get_total_page_num(page)
            domainListInfo.extend(list(map(self.__translate, self.currentPage)))
        return domainListInfo


if __name__ == '__main__':
    # TODO: 请填入阿里云账户的Access key ID 和Secret
    domain = Domain('YOUR-ACCESS-KEY-ID', 'YOUR-ACCESS-KEY-SECRET')
    domains_list = domain.get_domainListInfo()
    print(domains_list)
