# -*- coding: utf-8 -*-
# this file is generated by gen_kdata_schema function, dont't change it
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract.register import register_schema
from zvt.domain.quotes import StockKdataCommon
from zvt.contract.common import Region, Provider

KdataBase = declarative_base()


class Stock15mKdata(KdataBase, StockKdataCommon):
    __tablename__ = 'stock_15m_kdata'

class Stock15mHfqKdata(KdataBase, StockKdataCommon):
    __tablename__ = 'stock_15m_hfq_kdata'

class Stock15mBfqKdata(KdataBase, StockKdataCommon):
    __tablename__ = 'stock_15m_bfq_kdata'


register_schema(regions=[Region.CHN, Region.US], 
                providers={Region.CHN: [Provider.JoinQuant, Provider.BaoStock], 
                           Region.US: [Provider.Yahoo]}, 
                db_name='stock_15m_kdata', schema_base=KdataBase)

register_schema(regions=[Region.CHN, Region.US], 
                providers={Region.CHN: [Provider.JoinQuant, Provider.BaoStock], 
                           Region.US: [Provider.Yahoo]}, 
                db_name='stock_15m_hfq_kdata', schema_base=KdataBase)

register_schema(regions=[Region.CHN, Region.US], 
                providers={Region.CHN: [Provider.JoinQuant, Provider.BaoStock], 
                           Region.US: [Provider.Yahoo]}, 
                db_name='stock_15m_bfq_kdata', schema_base=KdataBase)


__all__ = ['Stock15mKdata', 'Stock15mHfqKdata', 'Stock15mBfqKdata']
