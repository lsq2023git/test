import abc

class BaseStrategy(abc.ABC):
    """
    Abstract base class for all trading strategies.
    """

    @abc.abstractmethod
    def __init__(self, api_client, strategy_manager, config=None):
        """
        Initialize the strategy.
        :param api_client: An instance of the OKXAPI client.
        :param strategy_manager: A reference to the strategy manager (e.g., MainWindow instance)
                                  for logging or other interactions.
        :param config: A dictionary of strategy-specific parameters.
        """
        self.api_client = api_client
        self.strategy_manager = strategy_manager
        self.config = config if config is not None else {}
        self.running = False

    @abc.abstractmethod
    def start(self):
        """
        Start the strategy's execution.
        This could involve starting a new thread for continuous operation.
        """
        pass

    @abc.abstractmethod
    def stop(self):
        """
        Stop the strategy's execution.
        This should handle cleanup and ensure any running threads are stopped.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def get_parameters_definition(cls):
        """
        Returns a dictionary defining the parameters this strategy requires.
        Example:
        {
            'instrument': {'type': str, 'default': 'BTC-USDT-SWAP', 'label': 'Instrument ID'},
            'quantity': {'type': float, 'default': 0.01, 'label': 'Order Quantity'}
        }
        Supported types: str, float, int, bool
        """
        pass

    @abc.abstractmethod
    def on_tick(self, market_data):
        """
        Called when new market data (a "tick") is received.
        :param market_data: A dictionary containing the market data.
        """
        pass

    def log(self, message):
        """Helper method to log messages via the strategy manager."""
        if self.strategy_manager and hasattr(self.strategy_manager, 'log_strategy_message'):
            self.strategy_manager.log_strategy_message(f"[{self.__class__.__name__}] {message}")
        else:
            print(f"[{self.__class__.__name__}] (no logger): {message}")
