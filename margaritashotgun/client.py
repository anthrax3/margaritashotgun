import sys
import random
import logging
import margaritashotgun
import margaritashotgun.remote_host
from margaritashotgun.cli import Cli
from margaritashotgun.exceptions import NoConfigurationError
from margaritashotgun.workers import Workers


class Client():
    """
    Client for parallel memory capture with LiME
    """

    def __init__(self, config=None, library=True, name=None, verbose=False):
        """
        :type library: bool
        :param library: Toggle for command line features
        :type config: dict
        :param config: Client configuration
        """

        self.name = name
        self.verbose = verbose
        self.cli = Cli()
        self.library = library
        if self.library is False:
            args = self.cli.parse_args(sys.argv[1:])
            self.config = self.cli.configure(arguments=args)
            if args.verbose is True:
                self.verbose = True
        else:
            if config is None:
                raise NoConfigurationError
            self.config = self.cli.configure(config=config)

        if self.verbose is True:
            margaritashotgun.set_stream_logger(name=self.name, level=logging.DEBUG)
        else:
            margaritashotgun.set_stream_logger(name=self.name, level=logging.INFO)



    def run(self):
        """
        Captures remote hosts memory
        """
        logger = logging.getLogger(__name__)
        try:
            conf = self.map_config()
            workers = Workers(conf, self.config['workers'], name=self.name, library=self.library)
            description = 'memory capture action'
            results = workers.spawn(description)

            self.statistics(results)
            if self.library is True:
                return dict([('total', self.total),
                             ('completed', self.completed_addresses),
                             ('failed', self.failed_addresses)])
            else:
                logger.info(("{0} hosts processed. completed: {1} "
                             "failed {2}".format(self.total, self.completed,
                                                 self.failed)))
                logger.info("completed_hosts: {0}".format(self.completed_addresses))
                logger.info("failed_hosts: {0}".format(self.failed_addresses))
                quit()
        except KeyboardInterrupt:
            workers.cleanup(terminate=True)
            if self.library:
                raise
            else:
                quit(1)

    def map_config(self):
        config_list = []
        keys = ['aws', 'host', 'logging', 'repository']
        for host in self.config['hosts']:
            values = [self.config['aws'], host, self.config['logging'],
                      self.config['repository']]
            conf = dict(zip(keys, values))
            config_list.append(conf)
        return config_list

    def statistics(self, results):
        self.total = len(results)
        self.completed = 0
        self.completed_addresses = []
        self.failed = 0
        self.failed_addresses = []

        for result in results:
            if result[1] is False:
                self.failed += 1
                self.failed_addresses.append(result[0])
            else:
                self.completed += 1
                self.completed_addresses.append(result[0])
