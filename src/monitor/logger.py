import logging

PATH_TO_LOG = '.'


class Logger:
    def __init__(self, name="Logger"):
        self.log_path = f'{PATH_TO_LOG}\\logs\\monitor_errors.log'
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.stream_handler = logging.StreamHandler()
        self.stream_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        self.stream_handler.setFormatter(self.stream_format)
        self.stream_handler.setLevel(logging.DEBUG)

        self.file_handler = logging.FileHandler(self.log_path)
        self.file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.file_handler.setFormatter(self.file_format)
        self.file_handler.setLevel(logging.ERROR)

    def __enter__(self):
        logger = Logger()
        logger.logger.addHandler(self.file_handler)
        logger.logger.addHandler(self.stream_handler)
        return logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
