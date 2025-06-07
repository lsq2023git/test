# OKX Trader

This is a Python-based trading application for the OKX cryptocurrency exchange.

## Features

*   Real-time market data display
*   Order placement and management
*   Customizable trading strategies
*   User-friendly interface

## Getting Started

### Prerequisites

*   Python 3.x
*   OKX API Key, Secret Key, and Passphrase

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/okx_trader.git
    cd okx_trader
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure API credentials (details to be added).

### Usage

```bash
python main.py
```

## Testing

To run the automated tests, navigate to the project root directory and run:

```bash
python -m unittest discover -s okx_trader/tests -p "test_*.py"
```

Ensure that any necessary dependencies for testing (like `unittest.mock` which is standard in Python 3.3+) are available in your environment.

## Project Structure

```
okx_trader/
├── core/                 # Core logic (API interaction, etc.)
│   ├── __init__.py
│   └── okx_api.py
├── ui/                   # User interface components
│   ├── __init__.py
│   └── main_window.py
├── strategies/           # Trading strategies
│   ├── __init__.py
│   └── base_strategy.py
├── tests/                # Unit and integration tests
│   └── __init__.py
├── main.py               # Main application entry point
├── requirements.txt      # Project dependencies
└── README.md             # This file
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details (to be added).
