import json
import uuid
import random
import requests
import threading
import websocket
import pandas as pd
from typing import Dict
from monitor.logger import Logger


class BinanceStorage:
    def __init__(self, *, market_type: str = 'spot', symbol: str, ticker_type: str, interval: str = ''):
        self.__doc__ = ''' https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams 
                            https://github.com/binance/binance-signature-examples'''
        FUTURES_HOST = 'fstream.binance.com'
        MAIN_HOST = 'data-stream.binance.com'

        valid_ticker_type = ('ticker', 'aggTrade', 'depth', 'kline',
                             'bookTicker', 'miniTicker', 'markPrice', 'indexPrice', 'trade')
        if ticker_type not in valid_ticker_type:
            raise ValueError(f'ticker_type is not correct. Possible values: {valid_ticker_type}')

        valid_interval = ('1s', '1m', '3m', '5m', '15m', '30m', '1h',
                          '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M')
        if ticker_type == 'kline' and interval not in valid_interval:
            raise ValueError(f'Wrong interval value. Possible values: {valid_interval}')

        valid_market_type = ('futures', 'spot')
        if market_type not in valid_market_type:
            raise ValueError(f'Wrong market type. Possible values: {valid_market_type}')

        if market_type == 'futures':
            self.host = FUTURES_HOST
        else:
            self.host = MAIN_HOST

        self.symbol = symbol.lower()
        self.LIMIT_ARCHIVE_DATA = 1000
        self.ARCHIVE_INTERVAL_CANDLE = '1m'
        self.market_type = market_type
        self.ticker_type = ticker_type
        self.interval = interval
        self.session_id = uuid.uuid4()
        self.real_time_price = None
        self.timer_event = threading.Event()
        self.market_history_df = pd.DataFrame({'epoch_time': [], 'close_price': []})

    def start_websocket(self):
        ws = websocket.WebSocketApp(f'wss://{self.host}/ws/{self.session_id}',
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)

        thread = threading.Thread(target=ws.run_forever)
        thread.start()

    def on_message(self, ws, message):
        try:
            stream_as_dict = json.loads(message)
            if stream_as_dict.get('ping'):
                ws.send(json.dumps({'pong': stream_as_dict.get('ping')}))

            if stream_as_dict.get('e') == 'kline' and \
                    stream_as_dict['s'] == self.symbol.upper() and \
                    stream_as_dict['k']['x']:
                self.append_history_market_data(stream_as_dict)

            if stream_as_dict.get('e') == 'trade' and \
                    stream_as_dict['s'] == self.symbol.upper():
                self.real_time_price = float(stream_as_dict['p'])
                self.timer_event.set()

        except Exception as e:
            with Logger() as log_obj:
                log_obj.logger.critical(e, exc_info=True)

    def append_history_market_data(self, fresh_data: Dict):
        try:
            last_epoch_time = self.market_history_df.index.values.tolist()[-1]
            if fresh_data['k']['t'] > last_epoch_time:
                epoch_time = fresh_data['k']['t']
                close_price = fresh_data['k']['c']
                new_row_df = pd.DataFrame({'epoch_time': [epoch_time], f'close_price': [float(close_price)]})
                new_row_df.set_index(['epoch_time'], inplace=True, verify_integrity=True)
                self.market_history_df = \
                    pd.concat([self.market_history_df, new_row_df], join='inner', verify_integrity=True)
                self.timer_event.set()

        except Exception as e:
            with Logger() as log_obj:
                log_obj.logger.critical(e, exc_info=True)

    def on_open(self, ws):
        request = {"method": "SUBSCRIBE",
                   "params": [
                       f"{self.symbol}@{self.ticker_type}{'_' if self.interval else ''}{self.interval}"],
                   "id": self.randint()}
        ws.send(json.dumps(request))

    @staticmethod
    def on_error(ws, error):
        with Logger() as log_obj:
            log_obj.logger.error(f'Websocket error: {error}')
        ws.close()

    @staticmethod
    def on_close(ws, code_close, close_message):
        with Logger() as log_obj:
            log_obj.logger.debug(f'Websocket close: code_close={code_close}, message={close_message}')

    def fill_archive_data(self):
        try:
            data = self.get_archive_data_from_binance()
            pretty_dict = {'epoch_time': [], f'close_price': []}
            for item in data[:-1]:
                pretty_dict['epoch_time'].append(item[0])
                pretty_dict[f'close_price'].append(float(item[4]))
            new_data = pd.DataFrame(pretty_dict)
            new_data.set_index(['epoch_time'], inplace=True, verify_integrity=True)
            self.market_history_df = pd.concat([self.market_history_df, new_data], join='inner', verify_integrity=True)
        except Exception as e:
            with Logger() as log_obj:
                log_obj.logger.critical(e, exc_info=True)

    def get_archive_data_from_binance(self) -> Dict:
        if self.market_type == 'futures':
            url = f"https://fapi.binance.com/fapi/v1/klines?" \
                  f"symbol={self.symbol}&interval={self.ARCHIVE_INTERVAL_CANDLE}&limit={self.LIMIT_ARCHIVE_DATA}"
        else:
            url = f"https://api1.binance.com/api/v3/klines?" \
                  f"symbol={self.symbol.upper()}&interval={self.ARCHIVE_INTERVAL_CANDLE}&limit={self.LIMIT_ARCHIVE_DATA}"
        response = requests.get(url)

        if 200 <= response.status_code < 300:
            return json.loads(response.text)
        else:
            with Logger() as log_obj:
                log_obj.logger.error(f'Http request error. Code={response.status_code}. {response.content}')

    @staticmethod
    def randint(start_value=0, end_value=999):
        a = random.randint(start_value, end_value)
        return a
