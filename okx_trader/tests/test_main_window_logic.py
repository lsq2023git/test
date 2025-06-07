import unittest
from unittest.mock import MagicMock, patch, call
import tkinter as tk # Required for tk.StringVar if not fully mocked

from okx_trader.ui.main_window import MainWindow
from okx_trader.core.trading_records import TradeRecord
# OKXAPI is imported in main_window, so it might be needed for patching context
# from okx_trader.core.okx_api import OKXAPI

# It's good practice to mock tk.Tk() for all MainWindow tests if it's passed to __init__
class MockTkRoot(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title_called_with = None
        self.geometry_called_with = None

    def title(self, title_string):
        self.title_called_with = title_string

    def geometry(self, geometry_string):
        self.geometry_called_with = geometry_string

    # Mock other tk root methods if MainWindow calls them during init (e.g., protocol)
    def protocol(self, name, func):
        pass


class TestMainWindowLogic(unittest.TestCase):

    def setUp(self):
        """Setup a MainWindow instance with a mocked Tk root and other UI mocks."""
        self.mock_root = MockTkRoot()

        # To fully isolate MainWindow, we should prevent it from creating actual UI widgets.
        # This can be done by patching ttk.Frame, ttk.Label, etc., if __init__ is complex.
        # For now, we focus on methods not heavily dependent on full UI build in __init__.
        # If __init__ itself becomes too complex to mock out, then testing these units
        # becomes harder without a live Tk instance (which we want to avoid in unit tests).

        # Patch external dependencies that MainWindow uses directly
        with patch('okx_trader.ui.main_window.OKXAPI', MagicMock()) as self.MockOKXAPI_class, \
             patch('okx_trader.ui.main_window.pkgutil.iter_modules', return_value=[]) as self.mock_iter_modules, \
             patch('okx_trader.ui.main_window.importlib.import_module') as self.mock_import_module, \
             patch('okx_trader.ui.main_window.inspect.getmembers', return_value=[]) as self.mock_getmembers:

            # Mock parts of the UI that are directly accessed by the logic we're testing
            # This assumes MainWindow's __init__ can run without a full UI tree if these are mocked.
            self.main_window = MainWindow(self.mock_root)

            # Mock UI elements that are directly used by the methods under test
            self.main_window.total_pnl_label_var = MagicMock(spec=tk.StringVar)
            self.main_window.trade_log_tree = MagicMock() # Mock the Treeview
            self.main_window.app_log_text = MagicMock() # Mock ScrolledText for app logs
            self.main_window.status_bar_text = MagicMock(spec=tk.StringVar) # Mock status bar text var

            # For _initialize_api_client tests
            self.main_window.api_key_entry = MagicMock()
            self.main_window.secret_key_entry = MagicMock()
            self.main_window.passphrase_entry = MagicMock()
            self.main_window.use_testnet_var = MagicMock(spec=tk.BooleanVar)


    def test_calculate_and_update_pnl(self):
        """Test the P&L calculation logic."""
        self.main_window.current_pnl = 100.0 # Initial P&L

        # Test BUY trade
        buy_trade = TradeRecord(instrument_id="BTC-USDT", side="BUY", price=30000, quantity=0.1, commission=3.0)
        self.main_window._calculate_and_update_pnl(buy_trade)
        # Expected P&L = 100.0 - (30000 * 0.1) - 3.0 = 100.0 - 3000.0 - 3.0 = -2903.0
        self.assertAlmostEqual(self.main_window.current_pnl, -2903.0)
        self.main_window.total_pnl_label_var.set.assert_called_with("Total P/L: $-2,903.00")

        # Test SELL trade
        sell_trade = TradeRecord(instrument_id="BTC-USDT", side="SELL", price=31000, quantity=0.05, commission=1.5)
        self.main_window._calculate_and_update_pnl(sell_trade)
        # Expected P&L = -2903.0 + (31000 * 0.05) - 1.5 = -2903.0 + 1550.0 - 1.5 = -1354.5
        self.assertAlmostEqual(self.main_window.current_pnl, -1354.5)
        self.main_window.total_pnl_label_var.set.assert_called_with("Total P/L: $-1,354.50")

        # Test trade with zero commission
        buy_trade_no_comm = TradeRecord(instrument_id="ETH-USDT", side="BUY", price=2000, quantity=1, commission=0.0)
        self.main_window._calculate_and_update_pnl(buy_trade_no_comm)
        # Expected P&L = -1354.5 - (2000*1) - 0 = -3354.5
        self.assertAlmostEqual(self.main_window.current_pnl, -3354.5)
        self.main_window.total_pnl_label_var.set.assert_called_with("Total P/L: $-3,354.50")


    @patch('okx_trader.ui.main_window.datetime') # Mock datetime to control timestamp
    def test_record_trade(self, mock_datetime):
        """Test the record_trade method."""
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2023-01-01 10:00:00"
        mock_datetime.now.return_value = mock_now

        # Mock _calculate_and_update_pnl to isolate record_trade logic
        self.main_window._calculate_and_update_pnl = MagicMock()

        trade_data = {
            "instrument_id": "BTC-USDT-SWAP",
            "side": "BUY",
            "price": 30000.0,
            "quantity": 0.01,
            "notes": "Test trade"
            # timestamp will be auto-generated
        }
        self.main_window.record_trade(trade_data)

        self.assertEqual(len(self.main_window.trade_records), 1)
        recorded_trade = self.main_window.trade_records[0]
        self.assertIsInstance(recorded_trade, TradeRecord)
        self.assertEqual(recorded_trade.instrument_id, "BTC-USDT-SWAP")
        self.assertEqual(recorded_trade.timestamp, "2023-01-01 10:00:00")
        self.assertEqual(recorded_trade.notes, "Test trade")

        # Check if tree.insert and _calculate_and_update_pnl were called
        self.main_window.trade_log_tree.insert.assert_called_once_with("", tk.END, values=recorded_trade.to_tuple())
        self.main_window._calculate_and_update_pnl.assert_called_once_with(recorded_trade)
        self.main_window.app_log_text.insert.assert_any_call(tk.END, unittest.mock.ANY) # Check if logged

    def test_record_trade_missing_required_fields(self):
        """Test record_trade when essential data is missing for TradeRecord."""
        self.main_window._calculate_and_update_pnl = MagicMock()

        trade_data_missing_price = { # price is required by TradeRecord
            "instrument_id": "BTC-USDT-SWAP",
            "side": "BUY",
            "quantity": 0.01,
        }
        with patch('okx_trader.ui.main_window.messagebox.showerror') as mock_showerror:
            self.main_window.record_trade(trade_data_missing_price)

        self.assertEqual(len(self.main_window.trade_records), 0) # No trade should be recorded
        self.main_window.trade_log_tree.insert.assert_not_called()
        self.main_window._calculate_and_update_pnl.assert_not_called()
        mock_showerror.assert_called_once() # Check if error message was shown to user

    def test_initialize_api_client_success(self):
        """Test successful API client initialization."""
        self.main_window.api_key_entry.get.return_value = "test_api_key"
        self.main_window.secret_key_entry.get.return_value = "test_secret_key"
        self.main_window.passphrase_entry.get.return_value = "test_passphrase"
        self.main_window.use_testnet_var.get.return_value = True

        mock_api_instance = MagicMock()
        mock_api_instance.account_api = True # Simulate successful client internal init
        mock_api_instance.market_api = True
        self.MockOKXAPI_class.return_value = mock_api_instance

        result = self.main_window._initialize_api_client()

        self.assertTrue(result)
        self.MockOKXAPI_class.assert_called_once_with(
            "test_api_key", "test_secret_key", "test_passphrase", testnet=True
        )
        self.assertIs(self.main_window.api_client, mock_api_instance)
        self.main_window.status_bar_text.set.assert_any_call("Status: OKX API Initialized (Testnet: True)")

    def test_initialize_api_client_missing_credentials(self):
        """Test API client initialization with missing credentials."""
        self.main_window.api_key_entry.get.return_value = "" # Missing API key
        # ... (other fields can be valid or not, one missing is enough)

        with patch('okx_trader.ui.main_window.messagebox.showerror') as mock_showerror:
            result = self.main_window._initialize_api_client()

        self.assertFalse(result)
        self.assertIsNone(self.main_window.api_client)
        mock_showerror.assert_called_once_with("Credentials Error", "Please enter API Key, Secret Key, and Passphrase.")
        self.main_window.status_bar_text.set.assert_any_call("Status: Error - API credentials required.")

    def test_initialize_api_client_exception_during_init(self):
        """Test API client initialization when OKXAPI constructor raises an exception."""
        self.main_window.api_key_entry.get.return_value = "key"
        self.main_window.secret_key_entry.get.return_value = "secret"
        self.main_window.passphrase_entry.get.return_value = "pass"
        self.main_window.use_testnet_var.get.return_value = True

        self.MockOKXAPI_class.side_effect = Exception("Constructor Boom!")

        with patch('okx_trader.ui.main_window.messagebox.showerror') as mock_showerror:
            result = self.main_window._initialize_api_client()

        self.assertFalse(result)
        self.assertIsNone(self.main_window.api_client)
        mock_showerror.assert_called_once_with("API Error", "Failed to initialize OKX API: Constructor Boom!")
        self.main_window.status_bar_text.set.assert_any_call("Status: Error initializing API - Constructor Boom!")


    # Note: Testing _load_strategies, _on_strategy_selected, _start_strategy_handler,
    # _stop_strategy_handler is more complex due to their heavy UI interaction and
    # dynamic nature. They would require more intricate mocking of UI elements (Combobox,
    # dynamically created Entries/Checkbuttons) and potentially helper methods in MainWindow
    # to make them more testable. For this subtask, we've focused on more data-oriented logic.

if __name__ == '__main__':
    unittest.main()
