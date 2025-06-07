import unittest
from unittest.mock import patch, MagicMock
from okx_trader.core.okx_api import OKXAPI # Ensure this path is correct

# Define a common structure for successful API responses
MOCK_SUCCESS_RESPONSE = {"code": "0", "msg": "", "data": [{"key": "value"}]}
MOCK_SUCCESS_BALANCE_RESPONSE = {"code": "0", "msg": "", "data": [{"details": [{"ccy": "BTC", "availBal": "1"}]}]}
MOCK_SUCCESS_TICKER_RESPONSE = {"code": "0", "msg": "", "data": [{"instId": "BTC-USDT", "last": "30000"}]}

# Define a common structure for failed API responses
MOCK_ERROR_RESPONSE = {"code": "1", "msg": "An error occurred", "data": []}


class TestOKXAPI(unittest.TestCase):

    @patch('okx_trader.core.okx_api.Market.MarketAPI')
    @patch('okx_trader.core.okx_api.Account.AccountAPI')
    def test_init_testnet(self, MockAccountAPI, MockMarketAPI):
        """Test OKXAPI initialization with testnet=True."""
        api = OKXAPI(api_key="test_key", secret_key="test_secret", passphrase="test_pass", testnet=True)
        MockAccountAPI.assert_called_once_with("test_key", "test_secret", "test_pass", False, '1')
        MockMarketAPI.assert_called_once_with("test_key", "test_secret", "test_pass", False, '1')
        self.assertIsNotNone(api.account_api)
        self.assertIsNotNone(api.market_api)

    @patch('okx_trader.core.okx_api.Market.MarketAPI')
    @patch('okx_trader.core.okx_api.Account.AccountAPI')
    def test_init_mainnet(self, MockAccountAPI, MockMarketAPI):
        """Test OKXAPI initialization with testnet=False."""
        api = OKXAPI(api_key="live_key", secret_key="live_secret", passphrase="live_pass", testnet=False)
        MockAccountAPI.assert_called_once_with("live_key", "live_secret", "live_pass", False, '0')
        MockMarketAPI.assert_called_once_with("live_key", "live_secret", "live_pass", False, '0')

    @patch('okx_trader.core.okx_api.Market.MarketAPI')
    @patch('okx_trader.core.okx_api.Account.AccountAPI')
    def test_init_api_exception(self, MockAccountAPI, MockMarketAPI):
        """Test OKXAPI initialization when one of the API clients raises an exception."""
        MockAccountAPI.side_effect = Exception("Account API Init Failed")
        MockMarketAPI.return_value = MagicMock() # MarketAPI inits fine

        # We expect print statements, but the object should still be created with None for the failed API
        api = OKXAPI(api_key="key", secret_key="secret", passphrase="pass", testnet=True)
        self.assertIsNone(api.account_api) # Failed initialization
        self.assertIsNotNone(api.market_api) # Successful initialization

    @patch('okx_trader.core.okx_api.Account.AccountAPI')
    def test_get_account_balance_success_all(self, MockAccountAPI):
        """Test get_account_balance successfully fetching all currencies."""
        mock_account_instance = MockAccountAPI.return_value
        mock_account_instance.get_account_balance.return_value = MOCK_SUCCESS_BALANCE_RESPONSE

        api = OKXAPI("k", "s", "p")
        api.account_api = mock_account_instance # Ensure the instance is the mock

        balance = api.get_account_balance()
        mock_account_instance.get_account_balance.assert_called_once_with() # No ccy
        self.assertEqual(balance, MOCK_SUCCESS_BALANCE_RESPONSE['data'])

    @patch('okx_trader.core.okx_api.Account.AccountAPI')
    def test_get_account_balance_success_specific_ccy(self, MockAccountAPI):
        """Test get_account_balance successfully fetching a specific currency."""
        mock_account_instance = MockAccountAPI.return_value
        mock_account_instance.get_account_balance.return_value = MOCK_SUCCESS_BALANCE_RESPONSE

        api = OKXAPI("k", "s", "p")
        api.account_api = mock_account_instance

        balance = api.get_account_balance(ccy="BTC")
        mock_account_instance.get_account_balance.assert_called_once_with(ccy="BTC")
        self.assertEqual(balance, MOCK_SUCCESS_BALANCE_RESPONSE['data'])

    @patch('okx_trader.core.okx_api.Account.AccountAPI')
    def test_get_account_balance_api_error(self, MockAccountAPI):
        """Test get_account_balance handling an API error (code != '0')."""
        mock_account_instance = MockAccountAPI.return_value
        mock_account_instance.get_account_balance.return_value = MOCK_ERROR_RESPONSE

        api = OKXAPI("k", "s", "p")
        api.account_api = mock_account_instance

        balance = api.get_account_balance()
        self.assertIsNone(balance)

    @patch('okx_trader.core.okx_api.Account.AccountAPI')
    def test_get_account_balance_exception(self, MockAccountAPI):
        """Test get_account_balance handling an exception during API call."""
        mock_account_instance = MockAccountAPI.return_value
        mock_account_instance.get_account_balance.side_effect = Exception("Network error")

        api = OKXAPI("k", "s", "p")
        api.account_api = mock_account_instance

        balance = api.get_account_balance()
        self.assertIsNone(balance)

    @patch('okx_trader.core.okx_api.Account.AccountAPI') # Need this for OKXAPI constructor
    def test_get_account_balance_no_api_client(self, MockAccountAPI):
        """Test get_account_balance when account_api is None."""
        api = OKXAPI("k", "s", "p")
        api.account_api = None # Simulate failed initialization

        balance = api.get_account_balance()
        self.assertIsNone(balance)


    @patch('okx_trader.core.okx_api.Market.MarketAPI')
    def test_get_ticker_success(self, MockMarketAPI):
        """Test get_ticker successfully."""
        mock_market_instance = MockMarketAPI.return_value
        mock_market_instance.get_ticker.return_value = MOCK_SUCCESS_TICKER_RESPONSE

        api = OKXAPI("k", "s", "p") # AccountAPI will be mocked by default test behavior if not specified here
        api.market_api = mock_market_instance

        ticker_data = api.get_ticker(instId="BTC-USDT")
        mock_market_instance.get_ticker.assert_called_once_with(instId="BTC-USDT")
        self.assertEqual(ticker_data, MOCK_SUCCESS_TICKER_RESPONSE['data'])

    @patch('okx_trader.core.okx_api.Market.MarketAPI')
    def test_get_ticker_api_error(self, MockMarketAPI):
        """Test get_ticker handling an API error."""
        mock_market_instance = MockMarketAPI.return_value
        mock_market_instance.get_ticker.return_value = MOCK_ERROR_RESPONSE

        api = OKXAPI("k", "s", "p")
        api.market_api = mock_market_instance

        ticker_data = api.get_ticker(instId="BTC-USDT")
        self.assertIsNone(ticker_data)

    @patch('okx_trader.core.okx_api.Market.MarketAPI')
    def test_get_ticker_exception(self, MockMarketAPI):
        """Test get_ticker handling an exception."""
        mock_market_instance = MockMarketAPI.return_value
        mock_market_instance.get_ticker.side_effect = Exception("Timeout")

        api = OKXAPI("k", "s", "p")
        api.market_api = mock_market_instance

        ticker_data = api.get_ticker(instId="BTC-USDT")
        self.assertIsNone(ticker_data)

    @patch('okx_trader.core.okx_api.Market.MarketAPI') # Need this for OKXAPI constructor
    def test_get_ticker_no_api_client(self, MockMarketAPI):
        """Test get_ticker when market_api is None."""
        api = OKXAPI("k", "s", "p")
        api.market_api = None # Simulate failed initialization

        ticker_data = api.get_ticker("BTC-USDT")
        self.assertIsNone(ticker_data)

if __name__ == '__main__':
    unittest.main()
