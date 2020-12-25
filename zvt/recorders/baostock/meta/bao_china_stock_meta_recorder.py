# -*- coding: utf-8 -*-
import pandas as pd
from jqdatasdk import finance

from zvt.contract.api import df_to_db, get_entity_exchange, get_entity_code
from zvt.contract.recorder import Recorder, TimeSeriesDataRecorder
from zvt.api.quote import china_stock_code_to_id, portfolio_relate_stock
from zvt.domain import EtfStock, Stock, Etf, StockDetail
from zvt.contract.common import Region, Provider, EntityType
from zvt.recorders.baostock.common import to_entity_id, to_bao_entity_type
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.request_utils import bao_get_all_securities


class BaseBaoChinaMetaRecorder(Recorder):
    provider = Provider.BaoStock

    def __init__(self, batch_size=10, force_update=True, sleeping_time=10, share_para=None) -> None:
        super().__init__(batch_size, force_update, sleeping_time)


    def to_zvt_entity(self, df, entity_type: EntityType, category=None):
        # 上市日期
        df.rename(columns={'ipoDate': 'list_date', 'outDate': 'end_date', 'code_name': 'name'}, inplace=True)
        df['end_date'].replace(r'^\s*$', '2200-01-01', regex=True, inplace=True)
        
        df['list_date'] = pd.to_datetime(df['list_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])
        df['timestamp'] = df['list_date']

        df['entity_id'] = df['code'].apply(lambda x: to_entity_id(entity_type=entity_type, bao_code=x))
        df['id'] = df['entity_id']
        df['entity_type'] = entity_type.value
        df[['exchange','code']] = df['code'].str.split('.',expand=True)

        if category:
            df['category'] = category

        return df


class BaoChinaStockRecorder(BaseBaoChinaMetaRecorder):
    data_schema = Stock
    region = Region.CHN

    def run(self):
        # 抓取股票列表
        df_stock = self.to_zvt_entity(bao_get_all_securities(to_bao_entity_type(EntityType.Stock)), entity_type=EntityType.Stock)
        df_to_db(df_stock, region=Region.CHN, data_schema=Stock, provider=self.provider, force_update=self.force_update)
        # persist StockDetail too
        df_to_db(df=df_stock, region=Region.CHN, data_schema=StockDetail, provider=self.provider, force_update=self.force_update)

        # self.logger.info(df_stock)
        self.logger.info("persist stock list success")


class BaoChinaEtfRecorder(BaseBaoChinaMetaRecorder):
    data_schema = Etf
    region = Region.CHN

    def run(self):
        # 抓取etf列表
        df_index = self.to_zvt_entity(bao_get_all_securities(to_bao_entity_type(EntityType.ETF)), entity_type=EntityType.ETF, category='etf')
        df_to_db(df_index, region=Region.CHN, data_schema=Etf, provider=self.provider, force_update=self.force_update)

        # self.logger.info(df_index)
        self.logger.info("persist etf list success")


class BaoChinaStockEtfPortfolioRecorder(TimeSeriesDataRecorder):
    entity_provider = Provider.JoinQuant
    entity_schema = Etf

    # 数据来自jq
    provider = Provider.BaoStock

    data_schema = EtfStock

    def __init__(self, entity_type=EntityType.ETF, exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0, share_para=None) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, share_para=share_para)


    def on_finish(self):
        super().on_finish()


    def record(self, entity, start, end, size, timestamps, http_session):
        q = jq_query(finance.FUND_PORTFOLIO_STOCK).filter(finance.FUND_PORTFOLIO_STOCK.pub_date >= start).filter(
            finance.FUND_PORTFOLIO_STOCK.code == entity.code)
        df = finance.run_query(q)
        if pd_is_not_null(df):
            #          id    code period_start  period_end    pub_date  report_type_id report_type  rank  symbol  name      shares    market_cap  proportion
            # 0   8640569  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     1  601318  中国平安  19869239.0  1.361043e+09        7.09
            # 1   8640570  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     2  600519  贵州茅台    921670.0  6.728191e+08        3.50
            # 2   8640571  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     3  600036  招商银行  18918815.0  5.806184e+08        3.02
            # 3   8640572  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     4  601166  兴业银行  22862332.0  3.646542e+08        1.90
            df['timestamp'] = pd.to_datetime(df['pub_date'])

            df.rename(columns={'symbol': 'stock_code', 'name': 'stock_name'}, inplace=True)
            df['proportion'] = df['proportion'] * 0.01

            df = portfolio_relate_stock(df, entity)

            df['stock_id'] = df['stock_code'].apply(lambda x: china_stock_code_to_id(x))
            df['id'] = df[['entity_id', 'stock_id', 'pub_date', 'id']].apply(lambda x: '_'.join(x.astype(str)), axis=1)
            df['report_date'] = pd.to_datetime(df['period_end'])
            df['report_period'] = df['report_type'].apply(lambda x: jq_to_report_period(x))

            df_to_db(df=df, region=Region.CHN, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

            # self.logger.info(df.tail())
            self.logger.info(f"persist etf {entity.code} portfolio success")

        return None


__all__ = ['BaoChinaStockRecorder', 'BaoChinaEtfRecorder', 'BaoChinaStockEtfPortfolioRecorder']

if __name__ == '__main__':
    # BaoChinaStockRecorder().run()
    BaoChinaStockEtfPortfolioRecorder(codes=['510050']).run()
