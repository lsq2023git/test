import unittest
from datetime import datetime
from okx_trader.core.trading_records import TradeRecord

class TestTradeRecord(unittest.TestCase):

    def test_trade_record_instantiation_defaults(self):
        """Test TradeRecord instantiation with default values."""
        record = TradeRecord(
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            price=30000.0,
            quantity=0.01
        )
        self.assertEqual(record.instrument_id, "BTC-USDT-SWAP")
        self.assertEqual(record.side, "BUY")
        self.assertEqual(record.price, 30000.0)
        self.assertEqual(record.quantity, 0.01)
        self.assertIsInstance(record.timestamp, str)
        # Check if timestamp is recent (e.g., within the last few seconds)
        record_time = datetime.strptime(record.timestamp, "%Y-%m-%d %H:%M:%S")
        self.assertTrue((datetime.now() - record_time).total_seconds() < 5)
        self.assertEqual(record.commission, 0.0)
        self.assertEqual(record.commission_asset, "USDT")
        self.assertEqual(record.notes, "")
        self.assertEqual(record.order_id, "")
        self.assertEqual(record.trade_id, "")

    def test_trade_record_instantiation_provided_values(self):
        """Test TradeRecord instantiation with all values provided."""
        custom_timestamp = "2023-01-01 10:00:00"
        record = TradeRecord(
            instrument_id="ETH-USDT-SWAP",
            side="SELL",
            price=2000.0,
            quantity=0.5,
            timestamp=custom_timestamp,
            commission=1.5,
            commission_asset="ETH",
            notes="Test sell order",
            order_id="ord123",
            trade_id="trd456"
        )
        self.assertEqual(record.instrument_id, "ETH-USDT-SWAP")
        self.assertEqual(record.side, "SELL")
        self.assertEqual(record.price, 2000.0)
        self.assertEqual(record.quantity, 0.5)
        self.assertEqual(record.timestamp, custom_timestamp)
        self.assertEqual(record.commission, 1.5)
        self.assertEqual(record.commission_asset, "ETH")
        self.assertEqual(record.notes, "Test sell order")
        self.assertEqual(record.order_id, "ord123")
        self.assertEqual(record.trade_id, "trd456")

    def test_trade_record_to_tuple(self):
        """Test the to_tuple method for correct output format and order."""
        record = TradeRecord(
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            price=30000.1234567,
            quantity=0.01234567,
            timestamp="2023-01-01 12:00:00",
            commission=0.00123456,
            commission_asset="BTC",
            notes="Tuple test"
        )
        expected_tuple = (
            "2023-01-01 12:00:00",
            "BTC-USDT-SWAP",
            "BUY",
            "30000.1235",  # Formatted price
            "0.012346",  # Formatted quantity
            "0.001235 BTC", # Formatted commission
            "Tuple test"
        )
        self.assertEqual(record.to_tuple(), expected_tuple)

    def test_trade_record_to_tuple_default_commission_asset(self):
        """Test to_tuple with default commission asset."""
        record = TradeRecord(
            instrument_id="LTC-USDT-SWAP",
            side="SELL",
            price=100.0,
            quantity=1.0,
            timestamp="2023-01-02 12:00:00",
            commission=0.1,
            # commission_asset uses default "USDT"
            notes="Default asset test"
        )
        expected_tuple = (
            "2023-01-02 12:00:00",
            "LTC-USDT-SWAP",
            "SELL",
            "100.0000",
            "1.000000",
            "0.100000 USDT", # Default commission asset
            "Default asset test"
        )
        self.assertEqual(record.to_tuple(), expected_tuple)

if __name__ == '__main__':
    unittest.main()
