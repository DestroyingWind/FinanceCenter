# -*- coding: utf-8 -*-
import logging
import time
from http import client
import requests
from requests.adapters import HTTPAdapter
from retrying import retry
from functools import wraps
# import asyncio

import pandas as pd
from jqdatasdk import is_auth, auth, query, logout, \
                      get_fundamentals, get_mtss, get_fundamentals_continuously, \
                      get_all_securities, get_trade_days, get_bars, get_query_count
# from baostock import query_history_k_data_plus
import baostock as bs
import yfinance as yf
import finnhub

bs.login()

from zvt import zvt_env
from zvt.utils.time_utils import to_pd_timestamp, now_timestamp, to_time_int, to_time_str

logger = logging.getLogger(__name__)

client.HTTPConnection._http_vsn=11
client.HTTPConnection._http_vsn_str='HTTP/1.1'

def get_http_session():
    http_session = requests.Session()
    http_session.mount('http://', HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=3))
    http_session.mount('https://', HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=3))
    return http_session

def request_get(http_session, url, headers=None):
    # logger.info("HTTP GET: {}".format(url))
    return http_session.get(url, headers=headers, timeout=(5, 15))

def request_post(http_session, url, data=None, json=None):
    # logger.info("HTTP POST: {}".format(url))
    return http_session.post(url=url, data=data, json=json, timeout=(5, 15))


jq_index = 1

def jq_auth():
    try:
        global jq_index
        account = 'jq_username{}'.format(jq_index)
        password = 'jq_password{}'.format(jq_index)
        if not is_auth():    
            logger.info("auth with {}:{}".format(zvt_env[account], zvt_env[password]))
            auth(zvt_env[account], zvt_env[password])
        else:
            logger.info("already auth, attempt with {}:{}".format(zvt_env[account], zvt_env[password]))
        return True
    except Exception as e:
        logger.warning(f'joinquant account not ok,the timestamp(publish date) for finance would be not correct', e)
    return False

def jq_logout():
    pass

def jq_swap_account(error):
    if not (str(error)[:6] == "您当天的查询" or str(error)[:4] == "帐号过期"):
        return False

    logger.exception("auth failed, {}".format(error))
    raise error

    # it is not allowed to swap account, thus the code below is no use anymore.

    # global jq_index
    # jq_index = 1 if jq_index > 4 else jq_index + 1
    # account = 'jq_username{}'.format(jq_index)
    # password = 'jq_password{}'.format(jq_index) 
    # try:
    #     if is_auth():
    #         logout()
    #     logger.info("swap auth with {}:{}".format(zvt_env[account], zvt_env[password]))
    #     if auth(zvt_env[account], zvt_env[password]):
    #         logger.info("swap auth done")
    # except Exception as e:
    #     logger.exception("auth failed, {}".format(e))
    # time.sleep(10)
    # return True

# def swap_wrapper(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         while True:
#             try:
#                 return func(*args, **kwargs)
#             except Exception as e:
#                 if not jq_swap_account(e):
#                     logger.exception("func.__name__ failed, {}".format(e))
#                     raise e
#     return wrapper 


def jq_get_query_count():
    if is_auth():
        count = get_query_count()
        return count['spare']
    return 0

# @swap_wrapper    
def jq_query(*args, **kwargs):
    logger.info("HTTP QUERY, with args={}, kwargs={}".format(args, kwargs))
    return query(*args, **kwargs)

# @swap_wrapper
def jq_get_fundamentals(query_object, date=None, statDate=None):
    logger.info("HTTP GET: fundamentals, with date={}, statDate={}".format(date, statDate))
    return get_fundamentals(query_object, date=date, statDate=statDate)

# @swap_wrapper
def jq_get_mtss(security_list, start_date=None, end_date=None, fields=None, count=None):
    logger.info("HTTP GET: mtss, with security_list={}, start_date={}, end_date={}, \
        fields={}, count={}".format(security_list, start_date, end_date, fields, count))
    return get_mtss(security_list, start_date=start_date, end_date=end_date, fields=fields, count=count)
    
# @swap_wrapper
def jq_get_fundamentals_continuously(query_object, end_date=None, count=1, panel=True):
    logger.info("HTTP GET: fundamentals_continuously, with end_date={}, count={}".format(end_date, count))
    return get_fundamentals_continuously(query_object, end_date=end_date, count=count, panel=panel)
    
# @swap_wrapper
def jq_get_all_securities(types=[], date=None):
    logger.info("HTTP GET: all_securities, with types={}, date={}".format(types, date))
    return get_all_securities(types=types, date=date)
    
# @swap_wrapper
def jq_get_trade_days(start_date=None, end_date=None, count=None):
    logger.info("HTTP GET: trade_days, with start_date={}, end_date={}, count={}".format(start_date, end_date, count))
    return get_trade_days(start_date=start_date, end_date=end_date, count=count)
    
# @swap_wrapper
def jq_get_bars(security, count, unit="1d", fields=("date", "open", "high", "low", "close"), include_now=False, end_dt=None,
             fq_ref_date=None, df=True):
    # logger.info("HTTP GET: bars, with unit={}, fq_ref_date={}".format(unit, fq_ref_date))
    return get_bars(security, count, unit=unit, fields=fields, include_now=include_now, 
                    end_dt=end_dt, fq_ref_date=fq_ref_date, df=df)

def bao_get_trade_days(start_date=None, end_date=None):
    # logger.info("HTTP GET: trade_days, with start_date={}, end_date={}".format(start_date, end_date))
    k_rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
    return k_rs.get_data()

def bao_get_bars(security, start, end, frequency="d", adjustflag="3",
                 fields="date, code, open, high, low, close, preclose, volume, amount, adjustflag, turn, tradestatus, pctChg, isST"):
    k_rs = bs.query_history_k_data_plus(security, start_date=start, end_date=end, frequency=frequency, adjustflag=adjustflag, fields=fields)
    return k_rs.get_data()

def retry_if_connection_error(exception):
    """ Specify an exception you need. or just True"""
    return True
    # return isinstance(exception, ConnectionError)

# if exception retry with 0.5 second wait  
# @retry(retry_on_exception=retry_if_connection_error, stop_max_attempt_number=3, wait_fixed=2000)
def yh_get_bars(code, interval, start=None, end=None, actions=True):
    logger.info("HTTP GET: bars, with code={}, unit={}, start={}, end={}".format(code, interval, start, end))
    return yf.Ticker(code).history(interval=interval, start=start, end=end, actions=actions, debug=False)
    # return asyncio.run()
    # return yf.Ticker(code).history(interval=interval, start=start, end=end, debug=False)

def fh_auth():
    return finnhub.Client(api_key=zvt_env['finnhub_key'])

def fh_get_bars(client, code, interval, start, end):    
    logger.info("HTTP GET: bars, with code={}, unit={}, start={}, end={}".format(code, interval, start, end))
    _from = to_time_int(start)
    _to = now_timestamp() if end is None else to_time_int(end)
    res = client.stock_candles(code, interval, _from, _to)
    df = pd.DataFrame(res)
    df.rename(columns={'o':'open', 'c':'close', 'h':'high', 'l':'low', 'v':'volume', 't':'timestamp'}, inplace=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('timestamp', drop=True, inplace=True)
    return df

def tg_get_bars(http_session, code, interval, start, end):
    headers = {'Content-Type': 'application/json'}
    end = '' if end is None else end
    url = "https://api.tiingo.com/tiingo/daily/{}/prices?startDate={}{}&token={}".format(code, start, end, zvt_env['tiingo_key'])
    return request_get(http_session, url=url, headers=headers)