import dataclasses
from datetime import datetime

@dataclasses.dataclass
class TradeRecord:
    """
    Represents a single executed trade.
    """
    instrument_id: str
    side: str  # "BUY" or "SELL"
    price: float
    quantity: float
    timestamp: str = dataclasses.field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    commission: float = 0.0
    commission_asset: str = "USDT" # Asset in which commission is paid
    notes: str = ""
    order_id: str = "" # Optional: associated order ID from exchange
    trade_id: str = "" # Optional: associated trade ID from exchange

    # For Treeview display
    def to_tuple(self):
        return (
            self.timestamp,
            self.instrument_id,
            self.side,
            f"{self.price:.4f}", # Format price
            f"{self.quantity:.6f}", # Format quantity
            f"{self.commission:.6f} {self.commission_asset}",
            self.notes
        )

# Optional: PnLEntry can be defined later if more detailed P&L tracking is needed.
# @dataclasses.dataclass
# class PnLEntry:
#     timestamp: str
#     instrument_id: str
#     realized_pnl: float
#     notes: str = ""
#     closing_trade_id: str = "" # Link to the trade that realized this P&L
#     opening_trade_id: str = "" # Link to the trade(s) that this P&L is based on
