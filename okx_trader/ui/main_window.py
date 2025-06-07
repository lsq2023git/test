import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import json
from datetime import datetime

import importlib
import pkgutil
import inspect
import okx_trader.strategies
from okx_trader.strategies.base_strategy import BaseStrategy
from okx_trader.core.trading_records import TradeRecord # New import

try:
    from okx_trader.core.okx_api import OKXAPI
except ImportError:
    print("Warning: OKXAPI could not be imported. API functionality will be disabled.")
    OKXAPI = None

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("OKX Quant Trader")
        self.root.geometry("1024x768") # Adjusted size for Treeview

        self.api_client = None
        self.available_strategies = {}
        self.strategy_param_entries = {}
        self.active_strategy_instance = None

        self.trade_records = [] # For storing TradeRecord objects
        self.current_pnl = 0.0 # Simple P&L tracking

        # Main container frame
        main_container_frame = ttk.Frame(self.root, padding="10")
        main_container_frame.pack(fill=tk.BOTH, expand=True)

        # Top part: API Credentials
        credentials_frame = ttk.LabelFrame(main_container_frame, text="API Credentials", padding="10")
        credentials_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(credentials_frame, text="API Key:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.api_key_entry = ttk.Entry(credentials_frame, width=40)
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        ttk.Label(credentials_frame, text="Secret Key:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.secret_key_entry = ttk.Entry(credentials_frame, width=40)
        self.secret_key_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)
        ttk.Label(credentials_frame, text="Passphrase:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.passphrase_entry = ttk.Entry(credentials_frame, width=40, show='*')
        self.passphrase_entry.grid(row=2, column=1, padx=5, pady=2, sticky=tk.EW)
        self.use_testnet_var = tk.BooleanVar(value=True)
        self.testnet_checkbutton = ttk.Checkbutton(credentials_frame, text="Use Testnet (Simulated Trading)", variable=self.use_testnet_var)
        self.testnet_checkbutton.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        credentials_frame.columnconfigure(1, weight=1)

        # Middle part: Strategy Management and Controls
        strategy_and_controls_frame = ttk.Frame(main_container_frame)
        strategy_and_controls_frame.pack(fill=tk.X, padx=5, pady=5)

        strategy_management_frame = ttk.LabelFrame(strategy_and_controls_frame, text="Strategy Management", padding="10")
        strategy_management_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        ttk.Label(strategy_management_frame, text="Select Strategy:").pack(pady=(0,2), anchor=tk.W)
        self.strategy_combobox = ttk.Combobox(strategy_management_frame, state="readonly", width=30)
        self.strategy_combobox.pack(fill=tk.X)
        self.strategy_combobox.bind("<<ComboboxSelected>>", self._on_strategy_selected)
        self.strategy_params_frame = ttk.Frame(strategy_management_frame, padding="5")
        self.strategy_params_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        controls_frame = ttk.LabelFrame(strategy_and_controls_frame, text="Strategy Controls", padding="10")
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5,0))
        self.btn_start_strategy = ttk.Button(controls_frame, text="Start Strategy", command=self._start_strategy_handler)
        self.btn_start_strategy.pack(pady=5, fill=tk.X)
        self.btn_stop_strategy = ttk.Button(controls_frame, text="Stop Strategy", command=self._stop_strategy_handler, state=tk.DISABLED)
        self.btn_stop_strategy.pack(pady=5, fill=tk.X)

        # Data Display Frame (Notebook)
        data_display_notebook = ttk.Notebook(main_container_frame)
        data_display_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Trading Log (Now a Treeview)
        log_tab_frame = ttk.Frame(data_display_notebook)
        data_display_notebook.add(log_tab_frame, text='Trading Log')

        log_columns = ("Timestamp", "Instrument", "Side", "Price", "Quantity", "Commission", "Notes")
        self.trade_log_tree = ttk.Treeview(log_tab_frame, columns=log_columns, show="headings", height=10)

        for col in log_columns:
            self.trade_log_tree.heading(col, text=col)
            self.trade_log_tree.column(col, width=100, anchor=tk.W) # Default width
        # Specific widths
        self.trade_log_tree.column("Timestamp", width=150)
        self.trade_log_tree.column("Instrument", width=120)
        self.trade_log_tree.column("Side", width=60, anchor=tk.CENTER)
        self.trade_log_tree.column("Price", width=90, anchor=tk.E)
        self.trade_log_tree.column("Quantity", width=90, anchor=tk.E)
        self.trade_log_tree.column("Commission", width=120, anchor=tk.E)
        self.trade_log_tree.column("Notes", width=200)

        log_vsb = ttk.Scrollbar(log_tab_frame, orient="vertical", command=self.trade_log_tree.yview)
        log_hsb = ttk.Scrollbar(log_tab_frame, orient="horizontal", command=self.trade_log_tree.xview)
        self.trade_log_tree.configure(yscrollcommand=log_vsb.set, xscrollcommand=log_hsb.set)

        self.trade_log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        log_hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Tab 2: General Log (Old Trading Log - ScrolledText for app messages)
        general_log_tab = ttk.Frame(data_display_notebook)
        data_display_notebook.add(general_log_tab, text='Application Log')
        self.app_log_text = ScrolledText(general_log_tab, state='disabled', wrap=tk.WORD, height=10)
        self.app_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 3: Profit/Loss
        pl_tab = ttk.Frame(data_display_notebook, padding="10")
        data_display_notebook.add(pl_tab, text='Profit/Loss')
        self.total_pnl_label_var = tk.StringVar(value="Total P/L: $0.00")
        self.total_pnl_label = ttk.Label(pl_tab, textvariable=self.total_pnl_label_var, font=("Arial", 18, "bold"))
        self.total_pnl_label.pack(padx=10, pady=20, anchor='center')
        # TODO: Add a Treeview for individual P&L entries if PnLEntry dataclass is used later

        # Tab 4: Account Info
        account_tab = ttk.Frame(data_display_notebook, padding="5")
        data_display_notebook.add(account_tab, text='Account Info')
        self.btn_fetch_balance = ttk.Button(account_tab, text="Fetch Account Balance", command=self._fetch_account_balance_handler)
        self.btn_fetch_balance.pack(pady=5, anchor=tk.NW)
        self.account_info_text = ScrolledText(account_tab, state='disabled', wrap=tk.WORD, height=10)
        self.account_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 5: Market Data
        market_data_tab = ttk.Frame(data_display_notebook, padding="5")
        data_display_notebook.add(market_data_tab, text='Market Data')
        market_controls_frame = ttk.Frame(market_data_tab)
        market_controls_frame.pack(fill=tk.X, pady=5)
        ttk.Label(market_controls_frame, text="Instrument ID:").pack(side=tk.LEFT, padx=5)
        self.inst_id_entry = ttk.Entry(market_controls_frame, width=20)
        self.inst_id_entry.insert(0, "BTC-USDT-SWAP")
        self.inst_id_entry.pack(side=tk.LEFT, padx=5)
        self.btn_fetch_ticker = ttk.Button(market_controls_frame, text="Fetch Ticker", command=self._fetch_ticker_handler)
        self.btn_fetch_ticker.pack(side=tk.LEFT, padx=5)
        self.market_data_text = ScrolledText(market_data_tab, state='disabled', wrap=tk.WORD, height=10)
        self.market_data_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status Bar
        self.status_bar_text = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_bar_text, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self._load_strategies()
        self._add_log_message("Application initialized. Select a strategy or fetch data.") # Goes to app_log_text
        self._set_account_info("Account information will be displayed here after fetching.")
        self._set_market_data_text("Ticker information will be displayed here.")
        self.status_bar_text.set("Status: Ready.")


    def _add_log_message(self, message, to_app_log=True): # General app/status messages
        if to_app_log:
            self.app_log_text.configure(state='normal')
            self.app_log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} | {message}\n")
            self.app_log_text.configure(state='disabled')
            self.app_log_text.see(tk.END)
        print(message) # Keep console log for debugging

    def log_strategy_message(self, message): # Messages from strategies
        self._add_log_message(f"[STRATEGY] {message}", to_app_log=True)

    def record_trade(self, trade_data: dict):
        """
        Records a trade, updates the UI, and calculates P&L.
        trade_data should be a dictionary with keys matching TradeRecord fields.
        """
        try:
            # Ensure required fields are present or provide defaults
            if 'timestamp' not in trade_data:
                trade_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create TradeRecord instance
            # This will fail if required fields in TradeRecord are missing in trade_data
            trade = TradeRecord(**trade_data)

            self.trade_records.append(trade)

            # Insert into Treeview, ensuring values are strings
            self.trade_log_tree.insert("", tk.END, values=trade.to_tuple())

            self._add_log_message(f"Trade Recorded: {trade.instrument_id} {trade.side} {trade.quantity} @ {trade.price}", to_app_log=True)
            self._calculate_and_update_pnl(trade)
        except TypeError as e: # Catches errors from missing args in TradeRecord(**trade_data)
            self._add_log_message(f"Error creating TradeRecord: {e}. Data: {trade_data}", to_app_log=True)
            messagebox.showerror("Trade Record Error", f"Could not record trade: {e}\nCheck strategy trade data.")
        except Exception as e:
            self._add_log_message(f"Error in record_trade: {e}", to_app_log=True)
            messagebox.showerror("Trade Record Error", f"An unexpected error occurred while recording trade: {e}")

    def _calculate_and_update_pnl(self, new_trade: TradeRecord):
        """
        Very basic P&L calculation. Assumes trades are for the same asset (e.g., USDT based pairs).
        This is a crude placeholder. A real P&L calculation needs to track positions.
        """
        # Crude P&L: Sum of (price * quantity), negative for BUYs, positive for SELLs
        # Ignores commissions for simplicity in this placeholder.
        trade_value = new_trade.price * new_trade.quantity

        if new_trade.side.upper() == "BUY":
            self.current_pnl -= trade_value
        elif new_trade.side.upper() == "SELL":
            self.current_pnl += trade_value

        # Subtract commission if any
        self.current_pnl -= new_trade.commission

        pnl_string = f"Total P/L: ${self.current_pnl:,.2f}" # Format with commas and 2 decimal places
        self.total_pnl_label_var.set(pnl_string)
        self._add_log_message(f"P&L Updated: {pnl_string}. Last trade: {new_trade.side} {new_trade.quantity} {new_trade.instrument_id} @ {new_trade.price}", to_app_log=True)


    def _set_text_widget_content(self, text_widget, content): # For ScrolledText widgets
        text_widget.configure(state='normal')
        text_widget.delete('1.0', tk.END)
        if isinstance(content, (dict, list)):
            try:
                content = json.dumps(content, indent=4)
            except Exception as e:
                content = f"Error formatting content: {e}\n\nRaw content: {str(content)}"
        text_widget.insert('1.0', str(content))
        text_widget.configure(state='disabled')

    def _set_account_info(self, info_text):
        self._set_text_widget_content(self.account_info_text, info_text)

    def _set_market_data_text(self, info_text):
        self._set_text_widget_content(self.market_data_text, info_text)

    def _initialize_api_client(self): # (implementation as before)
        if self.api_client: return True
        if not OKXAPI:
            self.status_bar_text.set("Status: Error - OKX API Library not loaded.")
            self._add_log_message("Error: OKXAPI module is not available.")
            messagebox.showerror("API Error", "OKX API support is not loaded.")
            return False
        api_key = self.api_key_entry.get()
        secret_key = self.secret_key_entry.get()
        passphrase = self.passphrase_entry.get()
        use_testnet = self.use_testnet_var.get()
        if not all([api_key, secret_key, passphrase]):
            self.status_bar_text.set("Status: Error - API credentials required.")
            self._add_log_message("API Init Error: Missing credentials.")
            messagebox.showerror("Credentials Error", "Please enter API Key, Secret Key, and Passphrase.")
            return False
        try:
            self._add_log_message(f"Initializing OKX API (Testnet: {use_testnet})...")
            self.api_client = OKXAPI(api_key, secret_key, passphrase, testnet=use_testnet)
            if self.api_client.account_api and self.api_client.market_api:
                self.status_bar_text.set(f"Status: OKX API Initialized (Testnet: {use_testnet})")
                self._add_log_message("OKX API Client initialized.")
                return True
            else:
                self.status_bar_text.set("Status: Error - Failed to initialize OKX API clients.")
                self._add_log_message("API Init Failed. Check OKXAPI logs.")
                self.api_client = None
                return False
        except Exception as e:
            self.api_client = None
            self.status_bar_text.set(f"Status: Error initializing API - {e}")
            self._add_log_message(f"API Initialization Exception: {e}")
            messagebox.showerror("API Error", f"Failed to initialize OKX API: {e}")
            return False

    def _fetch_account_balance_handler(self): # (implementation as before)
        if not self._initialize_api_client(): return
        self._add_log_message("Fetching account balance...")
        self.status_bar_text.set("Status: Fetching account balance...")
        try:
            balance_data = self.api_client.get_account_balance()
            if balance_data:
                self._set_account_info(balance_data)
                self.status_bar_text.set("Status: Account balance fetched.")
                self._add_log_message("Account balance fetched.")
            else:
                msg = "Failed to fetch account balance. See logs."
                self._set_account_info(msg); self.status_bar_text.set(f"Status: {msg}"); self._add_log_message(msg)
        except Exception as e:
            msg = f"Exception fetching balance: {e}"
            self._set_account_info(msg); self.status_bar_text.set(f"Status: {msg}"); self._add_log_message(msg)
            messagebox.showerror("Balance Error", msg)

    def _fetch_ticker_handler(self): # (implementation as before)
        if not self._initialize_api_client(): return
        inst_id = self.inst_id_entry.get()
        if not inst_id: messagebox.showerror("Input Error", "Instrument ID is required."); return
        self._add_log_message(f"Fetching ticker for {inst_id}...")
        self.status_bar_text.set(f"Status: Fetching ticker for {inst_id}...")
        try:
            ticker_data = self.api_client.get_ticker(instId=inst_id)
            if ticker_data:
                self._set_market_data_text(ticker_data[0] if isinstance(ticker_data, list) and ticker_data else ticker_data)
                self.status_bar_text.set(f"Status: Ticker for {inst_id} fetched.")
                self._add_log_message(f"Ticker for {inst_id} fetched.")
            else:
                msg = f"Failed to fetch ticker for {inst_id}. See logs."
                self._set_market_data_text(msg); self.status_bar_text.set(f"Status: {msg}"); self._add_log_message(msg)
        except Exception as e:
            msg = f"Exception fetching ticker: {e}"
            self._set_market_data_text(msg); self.status_bar_text.set(f"Status: {msg}"); self._add_log_message(msg)
            messagebox.showerror("Ticker Error", msg)

    def _load_strategies(self): # (implementation as before)
        self.available_strategies.clear(); strategy_names = []
        package_path = okx_trader.strategies.__path__; prefix = okx_trader.strategies.__name__ + "."
        for importer, modname, ispkg in pkgutil.iter_modules(package_path, prefix):
            try:
                module = importlib.import_module(modname)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
                        self.available_strategies[name] = obj; strategy_names.append(name)
            except Exception as e: self._add_log_message(f"Error loading strategy module {modname}: {e}")
        self.strategy_combobox['values'] = strategy_names
        if strategy_names: self.strategy_combobox.current(0); self._on_strategy_selected()
        else: self._add_log_message("No strategies found."); self._clear_strategy_params_frame()

    def _clear_strategy_params_frame(self): # (implementation as before)
        for widget in self.strategy_params_frame.winfo_children(): widget.destroy()
        self.strategy_param_entries.clear()

    def _on_strategy_selected(self, event=None): # (implementation as before)
        self._clear_strategy_params_frame()
        selected_strategy_name = self.strategy_combobox.get()
        if not selected_strategy_name: return
        strategy_class = self.available_strategies.get(selected_strategy_name)
        if not strategy_class: self._add_log_message(f"Error: Could not find class for {selected_strategy_name}"); return
        try: params_def = strategy_class.get_parameters_definition()
        except Exception as e: self._add_log_message(f"Error getting params for {selected_strategy_name}: {e}"); return
        for i, (param_name, definition) in enumerate(params_def.items()):
            label_text = definition.get('label', param_name)
            ttk.Label(self.strategy_params_frame, text=f"{label_text}:").grid(row=i, column=0, sticky=tk.W, padx=2, pady=2)
            param_type = definition.get('type', str); default_value = definition.get('default', '')
            if param_type == bool:
                var = tk.BooleanVar(value=default_value)
                entry = ttk.Checkbutton(self.strategy_params_frame, variable=var)
                self.strategy_param_entries[param_name] = {'widget': entry, 'type': param_type, 'var': var}
            else:
                entry = ttk.Entry(self.strategy_params_frame, width=25); entry.insert(0, str(default_value))
                self.strategy_param_entries[param_name] = {'widget': entry, 'type': param_type}
            entry.grid(row=i, column=1, sticky=tk.EW, padx=2, pady=2)
        self.strategy_params_frame.columnconfigure(1, weight=1)

    def _start_strategy_handler(self): # (implementation as before, minor logging change)
        if not self._initialize_api_client(): self._add_log_message("Strategy start failed: API client not initialized."); return
        selected_strategy_name = self.strategy_combobox.get()
        if not selected_strategy_name: messagebox.showerror("Strategy Error", "No strategy selected."); return
        strategy_class = self.available_strategies.get(selected_strategy_name)
        if not strategy_class: messagebox.showerror("Strategy Error", f"Could not find strategy class: {selected_strategy_name}"); return
        if self.active_strategy_instance: messagebox.showwarning("Strategy Info", "A strategy is already running. Stop it first."); return
        params = {}
        try:
            for name, entry_info in self.strategy_param_entries.items():
                if entry_info['type'] == bool: params[name] = entry_info['var'].get()
                else: value_str = entry_info['widget'].get(); params[name] = entry_info['type'](value_str)
        except ValueError as e: messagebox.showerror("Parameter Error", f"Invalid parameter value: {e}"); return
        except Exception as e: messagebox.showerror("Parameter Error", f"Error processing parameters: {e}"); return
        try:
            self.active_strategy_instance = strategy_class(api_client=self.api_client, strategy_manager=self, config=params)
            self.active_strategy_instance.start()
            self.status_bar_text.set(f"Status: Strategy '{selected_strategy_name}' started.")
            # Strategy itself should log its start via strategy_manager.log_strategy_message
            self.btn_start_strategy.config(state=tk.DISABLED); self.btn_stop_strategy.config(state=tk.NORMAL)
            self.strategy_combobox.config(state=tk.DISABLED)
            for info in self.strategy_param_entries.values(): info['widget'].config(state=tk.DISABLED)
        except Exception as e:
            self.active_strategy_instance = None
            self.status_bar_text.set(f"Status: Error starting strategy - {e}")
            self._add_log_message(f"Error starting strategy '{selected_strategy_name}': {e}")
            messagebox.showerror("Strategy Start Error", f"Failed to start strategy: {e}")

    def _stop_strategy_handler(self): # (implementation as before, minor logging change)
        if not self.active_strategy_instance: messagebox.showinfo("Strategy Info", "No strategy is currently running."); return
        strategy_name = self.active_strategy_instance.__class__.__name__
        self._add_log_message(f"Stopping strategy '{strategy_name}' (requesting stop)...", to_app_log=True)
        try:
            self.active_strategy_instance.stop()
            self.status_bar_text.set(f"Status: Strategy '{strategy_name}' stop requested.")
            # Strategy itself should log its stop via strategy_manager.log_strategy_message
        except Exception as e:
            self.status_bar_text.set(f"Status: Error stopping strategy - {e}")
            self._add_log_message(f"Error stopping strategy '{strategy_name}': {e}")
            messagebox.showerror("Strategy Stop Error", f"Error during strategy stop: {e}")
        finally: # This block will run regardless if stop() was successful or raised error
            self.active_strategy_instance = None # Assume it's stopped or we tried stopping
            self.btn_start_strategy.config(state=tk.NORMAL); self.btn_stop_strategy.config(state=tk.DISABLED)
            self.strategy_combobox.config(state="readonly")
            for info in self.strategy_param_entries.values():
                if isinstance(info['widget'], ttk.Checkbutton): info['widget'].config(state=tk.NORMAL)
                else: info['widget'].config(state=tk.NORMAL)
            self._add_log_message(f"UI unlocked after attempting to stop strategy '{strategy_name}'.", to_app_log=True)


if __name__ == '__main__': # (implementation as before)
    print("Running MainWindow directly for testing...")
    if OKXAPI is None:
        class MockOKXAPI:
            def __init__(self, api_key, secret_key, passphrase, testnet=True):
                print(f"MockOKXAPI initialized (Testnet: {testnet}) by {api_key}")
                self.account_api = True; self.market_api = True
            def get_account_balance(self, ccy=None): return [{"ccy": "USDT", "bal": "10000"}]
            def get_ticker(self, instId): return [{"instId": instId, "last": "50000"}]
        OKXAPI = MockOKXAPI
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
