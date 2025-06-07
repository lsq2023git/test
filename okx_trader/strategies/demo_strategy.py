from okx_trader.strategies.base_strategy import BaseStrategy
import threading
import time
from datetime import datetime # For trade timestamp

class DemoStrategy(BaseStrategy):
    """
    A demonstration strategy that logs messages and simulates trades periodically.
    """

    def __init__(self, api_client, strategy_manager, config=None):
        super().__init__(api_client, strategy_manager, config)
        self.thread = None
        self.trade_counter = 0 # Initialize trade counter
        self.log(f"Initialized with config: {self.config}")

    @classmethod
    def get_parameters_definition(cls):
        return {
            'instrument': {'type': str, 'default': 'BTC-USDT-SWAP', 'label': 'Instrument ID'},
            'quantity': {'type': float, 'default': 0.01, 'label': 'Order Quantity'},
            'log_interval_seconds': {'type': int, 'default': 5, 'label': 'Activity Interval (s)'} # Renamed for clarity
        }

    def start(self):
        if self.running:
            self.log("Attempted to start already running strategy.")
            return

        self.running = True
        self.trade_counter = 0 # Reset counter on start
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        # Log is now done by the strategy itself using self.log() which uses strategy_manager
        self.log(f"Started. Thread: {self.thread.name}. Config: {self.config}")


    def _run_loop(self):
        self.log("Run loop started.")
        # Use log_interval_seconds from config, default to 5 if not found or invalid
        activity_interval = self.config.get('log_interval_seconds', 5)
        if not isinstance(activity_interval, (int, float)) or activity_interval <= 0:
            self.log(f"Invalid log_interval_seconds: {activity_interval}, defaulting to 5 seconds.")
            activity_interval = 5

        try:
            while self.running:
                self.log(f"Is running... Instrument: {self.config.get('instrument', 'N/A')}, Next trade simulation in {activity_interval - (self.trade_counter % activity_interval) if activity_interval else 0} ticks (approx secs).")

                # Simulate a trade every 'activity_interval' seconds (approximately)
                # The self.trade_counter itself increments every loop, and the loop sleeps for 1 second.
                # So, a trade happens when self.trade_counter is a multiple of activity_interval.
                if self.trade_counter > 0 and self.trade_counter % activity_interval == 0:
                    sim_price = 30000.0 + (self.trade_counter * 10) # Simulate price changing
                    # Alternate BUY/SELL based on how many times activity_interval has passed
                    trade_side = "BUY" if (self.trade_counter // activity_interval) % 2 == 0 else "SELL"

                    trade_data = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "instrument_id": self.config.get('instrument', 'BTC-USDT-SWAP'),
                        "side": trade_side,
                        "price": sim_price,
                        "quantity": self.config.get('quantity', 0.01),
                        "commission": round(sim_price * self.config.get('quantity', 0.01) * 0.001, 6), # Simulate 0.1% commission
                        "commission_asset": "USDT", # Assuming USDT based pair
                        "notes": f"Simulated trade cycle {(self.trade_counter // activity_interval)}"
                    }
                    if hasattr(self.strategy_manager, 'record_trade'):
                        self.strategy_manager.record_trade(trade_data)
                        self.log(f"Simulated trade: {trade_side} {trade_data['quantity']} {trade_data['instrument_id']} @ {trade_data['price']}")
                    else:
                        self.log("Error: strategy_manager does not have record_trade method.")

                self.trade_counter += 1

                # Sleep for 1 second at a time to allow faster stopping
                time.sleep(1)

        except Exception as e:
            self.log(f"Exception in run_loop: {e}")
        finally:
            self.log("Run loop ended.")

    def stop(self):
        if not self.running:
            self.log("Attempted to stop an already stopped strategy.")
            return

        self.log("Stopping...") # Log intent to stop
        self.running = False # Signal thread to stop

        if self.thread and self.thread.is_alive():
            self.log(f"Waiting for thread {self.thread.name} to join...")
            self.thread.join(timeout=self.config.get('log_interval_seconds', 5) + 2) # Give thread time to finish current loop + buffer
            if self.thread.is_alive():
                self.log(f"Warning: Thread {self.thread.name} did not join in time.")
        else:
            self.log("No active thread to join or thread already finished.")
        self.log("Stopped.") # Confirm stop process finished

    def on_tick(self, market_data):
        """
        Called when new market data (a "tick") is received.
        """
        self.log(f"Received tick: {market_data}")
        pass
