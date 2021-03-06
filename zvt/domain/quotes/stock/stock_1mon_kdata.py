# -*- coding: utf-8 -*-
# this file is generated by gen_kdata_schema function, dont't change it
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract.register import register_schema
from zvt.domain.quotes import StockKdataCommon
from zvt.contract.common import Region, Provider

KdataBase = declarative_base()


class Stock1monKdata(KdataBase, StockKdataCommon):
    __tablename__ = 'stock_1mon_kdata'

class Stock1monHfqKdata(KdataBase, StockKdataCommon):
    __tablename__ = 'stock_1mon_hfq_kdata'

class Stock1monBfqKdata(KdataBase, StockKdataCommon):
    __tablename__ = 'stock_1mon_bfq_kdata'


register_schema(regions=[Region.CHN, Region.US], 
                providers={Region.CHN: [Provider.JoinQuant, Provider.BaoStock], 
                           Region.US: [Provider.Yahoo]}, 
                db_name='stock_1mon_kdata', schema_base=KdataBase)

register_schema(regions=[Region.CHN, Region.US], 
                providers={Region.CHN: [Provider.JoinQuant, Provider.BaoStock], 
                           Region.US: [Provider.Yahoo]}, 
                db_name='stock_1mon_hfq_kdata', schema_base=KdataBase)

register_schema(regions=[Region.CHN, Region.US], 
                providers={Region.CHN: [Provider.JoinQuant, Provider.BaoStock], 
                           Region.US: [Provider.Yahoo]}, 
                db_name='stock_1mon_bfq_kdata', schema_base=KdataBase)


__all__ = ['Stock1monKdata', 'Stock1monHfqKdata', 'Stock1monBfqKdata']
