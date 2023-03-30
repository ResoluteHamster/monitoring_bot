from multiprocessing import Manager, Event
from monitor.process_models import MultiStorageProcess, ETHWatcher, BTCWatcher

if __name__ == '__main__':
    with Manager() as manager:
        coefficients = manager.dict()
        multi_storage_running_event = Event()
        btc_watcher_running_event = Event()
        multi_storage_process = MultiStorageProcess(daemon=True, coefficients=coefficients,
                                                    multi_storage_running_event=multi_storage_running_event)

        btc_watcher = BTCWatcher(daemon=True, coefficients=coefficients,
                                 multi_storage_running_event=multi_storage_running_event,
                                 btc_watcher_running_event=btc_watcher_running_event)

        eth_watcher = ETHWatcher(daemon=True, coefficients=coefficients,
                                 btc_watcher_running_event=btc_watcher_running_event)

        multi_storage_process.start()
        btc_watcher.start()
        eth_watcher.start()
        eth_watcher.join()
