from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.contract import ContractDetails
import datetime
import pytz

class Forexdatastream(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.orderId = 0
        self.active_requests = set()
        self.reqId_to_symbol = {}  # Map to store request IDs to symbols
        self.prices = []  # Store close prices for analysis
        self.position = 0  # Track current position (1 = long, -1 = short, 0 = flat)
        self.entry_price = None  # Store the entry price of the current position
        self.entry_time = None  # Store the time of entry
        self.min_tick_size = 0.0001  # Default tick size, dynamically updated later

    def nextValidId(self, orderId: int):
        self.orderId = orderId
        print(f"Next valid order ID: {orderId}")
        self.req_contract_details("USDJPY")  # Request contract details to fetch tick size
        self.setup_contracts()

    def setup_contracts(self):
        # Define the currency pairs to stream
        self.pairs_to_stream = ["USDJPY"]

        reqId = 10000
        for pair in self.pairs_to_stream:
            # Set up the contract for each currency pair
            contract = Contract()
            contract.symbol = pair[:3]  # Base currency
            contract.secType = "CASH"
            contract.currency = pair[3:]  # Quote currency
            contract.exchange = "IDEALPRO"  # Forex exchange

            # Request real-time bars for the contract
            self.reqRealTimeBars(reqId, contract, 5, "MIDPOINT", 0, [])
            self.active_requests.add(reqId)
            self.reqId_to_symbol[reqId] = pair
            print(f"Streaming data for {pair} with request ID {reqId}")
            reqId += 1

    def realtimeBar(self, reqId: int, time_stamp: int, open_: float, high: float, low: float, close: float, volume: int, wap: float, count: int):
        # Map the request ID to the currency pair
        symbol = self.reqId_to_symbol.get(reqId, "Unknown")
        timezone = pytz.timezone('America/New_York')
        current_datetime = datetime.datetime.fromtimestamp(time_stamp).astimezone(timezone)

        # Log the received bar data
        print(f"Received bar data for Ticker: {symbol}, Time: {current_datetime}, Open: {open_}, High: {high}, Low: {low}, Close: {close}")

        # Add the close price to the price list
        self.prices.append(close)
        if len(self.prices) > 3:
            self.prices.pop(0)  # Keep only the last 3 prices for analysis

        # Check for exit conditions first
        self.check_exit_conditions(symbol, close, current_datetime)
        # Then check for new entry conditions
        self.check_scalping_strategy(symbol, close, current_datetime)

    def check_scalping_strategy(self, symbol: str, close: float, current_datetime: datetime.datetime):
        if len(self.prices) < 3:
            return  # Not enough data yet

        # Simple scalping logic: Buy on a dip, sell on a peak
        if self.prices[-2] < self.prices[-3] and self.prices[-1] > self.prices[-2]:
            if self.position == 0:  # No position
                self.place_order(symbol, "BUY", 100000, close, current_datetime)
                self.position = 1
        elif self.prices[-2] > self.prices[-3] and self.prices[-1] < self.prices[-2]:
            if self.position == 0:  # No position
                self.place_order(symbol, "SELL", 100000, close, current_datetime)
                self.position = -1

    def check_exit_conditions(self, symbol: str, close: float, current_datetime: datetime.datetime):
        if self.position == 0 or self.entry_price is None or self.entry_time is None:
            return  # No position to exit

        time_elapsed = (current_datetime - self.entry_time).total_seconds()

        # Exit long position
        if self.position == 1:
            if close > self.entry_price or time_elapsed > 60:
                self.place_order(symbol, "SELL", 100000, close, current_datetime)  # Exit long position
                print(f"Exited long position for {symbol} at {close}")
                self.position = 0
                self.entry_price = None
                self.entry_time = None

        # Exit short position
        elif self.position == -1:
            if close < self.entry_price or time_elapsed > 60:
                self.place_order(symbol, "BUY", 100000, close, current_datetime)  # Exit short position
                print(f"Exited short position for {symbol} at {close}")
                self.position = 0
                self.entry_price = None
                self.entry_time = None

    def req_contract_details(self, symbol: str):
        contract = Contract()
        contract.symbol = symbol[:3]
        contract.secType = "CASH"
        contract.currency = symbol[3:]
        contract.exchange = "IDEALPRO"

        self.reqContractDetails(self.orderId, contract)

    def contractDetails(self, reqId, contractDetails: ContractDetails):
        tick_size = contractDetails.minTick
        print(f"Tick size for {contractDetails.contract.symbol}/{contractDetails.contract.currency}: {tick_size}")
        self.min_tick_size = tick_size

    def place_order(self, symbol: str, action: str, quantity: int, close: float, current_datetime: datetime.datetime):
        contract = Contract()
        contract.symbol = symbol[:3]  # Base currency
        contract.secType = "CASH"
        contract.currency = symbol[3:]  # Quote currency
        contract.exchange = "IDEALPRO"

        # Use the dynamically fetched tick size or default to 0.0001
        tick_size = self.min_tick_size
        rounded_price = round(close / tick_size) * tick_size

        order = Order()
        order.action = action
        order.orderType = "LMT"  # Use limit order
        order.totalQuantity = quantity
        order.lmtPrice = rounded_price  # Use the rounded limit price
        order.orderId = self.orderId
        order.eTradeOnly = False
        order.firmQuoteOnly = False

        # Place the order
        self.placeOrder(contract, order)
        print(f"Placed {action} limit order for {quantity} of {symbol} at {rounded_price} with order ID {self.orderId} at {current_datetime}")
        self.orderId += 1

        # Track entry price and time for new positions
        if action == "BUY" and self.position == 0:
            self.entry_price = rounded_price
            self.entry_time = current_datetime
        elif action == "SELL" and self.position == 0:
            self.entry_price = rounded_price
            self.entry_time = current_datetime

    def placeOrder(self, contract, order):
        """
        Place an order through the IB API.
        """
        order.eTradeOnly = False
        order.firmQuoteOnly = False
        super().placeOrder(order.orderId, contract, order)

if __name__ == "__main__":
    try:
        # Instantiate the Forexdatastream class
        app = Forexdatastream()
        app.connect("127.0.0.1", 7497, 321)  # Connect to TWS or IB Gateway

        # Run the client
        app.run()
    except KeyboardInterrupt:
        print("Streaming stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
