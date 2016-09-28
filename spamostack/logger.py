import logging


class SpamFileHandler(logging.FileHandler):

    def __init__(self):
        logging.FileHandler.__init__(self, "RM.log")
        fmt = '%(asctime)s %(filename)s %(levelname)s: %(message)s'
        fmt_date = '%Y-%m-%dT%T%Z'
        formatter = logging.Formatter(fmt, fmt_date)
        self.setFormatter(formatter)


class SpamStreamHandler(logging.StreamHandler):

    def __init__(self):
        logging.StreamHandler.__init__(self)
        fmt = '%(asctime)s %(filename)s %(levelname)s: %(message)s'
        fmt_date = '%Y-%m-%dT%T%Z'
        formatter = logging.Formatter(fmt, fmt_date)
        self.setFormatter(formatter)
