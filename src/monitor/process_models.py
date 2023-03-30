from multiprocessing import Process
from monitor.logger import Logger
from monitor.storage import BinanceStorage


class MultiStorageProcess(Process):
    def __init__(self, *args, **kwargs):
        self.coefficients = kwargs['coefficients']
        self.multi_storage_running_event = kwargs['multi_storage_running_event']
        del kwargs['coefficients']
        del kwargs['multi_storage_running_event']
        super().__init__(*args, **kwargs)

        self.multi_storage_running_event.clear()
        self.pearson_correlation: float
        self.history_market_data_df = None
        self.first_symbol = 'ethusdt'
        self.second_symbol = 'btcusdt'

    def run(self):
        eth_storage = BinanceStorage(market_type='futures', symbol=self.first_symbol, ticker_type='kline',
                                     interval='1m')
        btc_storage = BinanceStorage(market_type='spot', symbol=self.second_symbol, ticker_type='kline', interval='1m')
        eth_storage.fill_archive_data()
        btc_storage.fill_archive_data()
        eth_storage.start_websocket()
        btc_storage.start_websocket()
        eth_storage.timer_event.set()
        btc_storage.timer_event.set()

        while True:
            if eth_storage.timer_event.is_set() and btc_storage.timer_event.is_set():
                self.history_market_data_df = \
                    eth_storage.market_history_df.join(btc_storage.market_history_df,
                                                       how='inner', validate='1:1', lsuffix=f'_{self.first_symbol}',
                                                       rsuffix=f'_{self.second_symbol}')

                first_column = f'close_price_{self.first_symbol}'
                second_column = f'close_price_{self.second_symbol}'
                self.coefficients['pearson_correlation'] = \
                    float(self.history_market_data_df[first_column].corr(self.history_market_data_df[second_column],
                                                                         method='pearson'))

                self.coefficients['mean_eth_futures_price'] = \
                    float(self.history_market_data_df[first_column].iloc[-60:].mean())
                self.coefficients['mean_btc_price'] = \
                    float(self.history_market_data_df[second_column].iloc[-60:].mean())
                eth_storage.timer_event.clear()
                btc_storage.timer_event.clear()
                self.multi_storage_running_event.set()


class BTCWatcher(Process):
    def __init__(self, *args, **kwargs):
        self.coefficients = kwargs['coefficients']
        self.multi_storage_running_event = kwargs['multi_storage_running_event']
        self.btc_watcher_running_event = kwargs['btc_watcher_running_event']
        del kwargs['coefficients']
        del kwargs['multi_storage_running_event']
        del kwargs['btc_watcher_running_event']
        self.btc_watcher_running_event.clear()

        super().__init__(*args, **kwargs)
        self.symbol = 'btcusdt'

    def run(self):
        btc_rt_storage = BinanceStorage(market_type='spot', symbol=self.symbol, ticker_type='trade')
        btc_rt_storage.start_websocket()

        while True:
            try:
                if self.multi_storage_running_event.is_set() and btc_rt_storage.timer_event.is_set():
                    self.coefficients['deviation_btc_in_percent'] = \
                        (btc_rt_storage.real_time_price - self.coefficients['mean_btc_price']) \
                        / self.coefficients['mean_btc_price'] * 100
                    btc_rt_storage.timer_event.clear()
                    self.btc_watcher_running_event.set()

            except Exception as e:
                with Logger() as log_obj:
                    log_obj.logger.critical(e, exc_info=True)


class ETHWatcher(Process):
    def __init__(self, *args, **kwargs):
        self.coefficients = kwargs['coefficients']
        self.btc_watcher_running_event = kwargs['btc_watcher_running_event']
        del kwargs['coefficients']
        del kwargs['btc_watcher_running_event']
        super().__init__(*args, **kwargs)
        self.symbol = 'ethusdt'

    def start(self):
        eth_rt_storage = BinanceStorage(market_type='futures', symbol=self.symbol, ticker_type='trade')
        eth_rt_storage.start_websocket()

        while True:
            try:
                if self.btc_watcher_running_event.is_set() and eth_rt_storage.timer_event.is_set():
                    deviation_eth_in_percent = \
                        (eth_rt_storage.real_time_price - self.coefficients['mean_eth_futures_price']) \
                        / self.coefficients['mean_eth_futures_price'] * 100

                    real_deviation_eth_in_percent = \
                        deviation_eth_in_percent - (self.coefficients['deviation_btc_in_percent'] *
                                                    self.coefficients['pearson_correlation'])

                    with Logger() as log_obj:
                        log_obj.logger.info(f'{real_deviation_eth_in_percent=}')

                    if real_deviation_eth_in_percent > 1:
                        print('Real deviation of the ETH price without the influence of the BTC movement '
                              f'{real_deviation_eth_in_percent} percent')
                        with Logger() as log_obj:
                            log_obj.logger.info('Real deviation of the ETH price without'
                                                ' the influence of the BTC movement '
                                                f'{real_deviation_eth_in_percent} percent')

                    eth_rt_storage.timer_event.clear()

            except Exception as e:
                with Logger() as log_obj:
                    log_obj.logger.critical(e, exc_info=True)
