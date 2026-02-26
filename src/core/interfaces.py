from abc import ABC, abstractmethod

class ExchangeProviderInterface(ABC):
    @abstractmethod
    def get_market_data(self, symbol: str, interval: str, limit: int = 100):
        pass

    @abstractmethod
    def get_realtime_price(self, symbol: str) -> float:
        pass

    @abstractmethod
    def get_asset_balance(self, asset: str) -> float:
        pass

class TechnicalAnalysisInterface(ABC):
    @abstractmethod
    def calculate_indicators(self, df):
        """Calculates N (ATR), Donchian Channels, EMA, etc."""
        pass

class SignalManagerInterface(ABC):
    @abstractmethod
    def generate_signal(self, df, current_price: float, state: dict) -> str:
        """Returns BUY, SELL, EXIT, or HOLD."""
        pass

class RiskManagerInterface(ABC):
    @abstractmethod
    def calculate_unit_size(self, balance: float, n_value: float, price: float) -> float:
        pass

    @abstractmethod
    def can_entry(self, current_heat: float, max_heat: float) -> bool:
        pass

class ExecutionEngineInterface(ABC):
    @abstractmethod
    def execute_order(self, symbol: str, side: str, quantity: float):
        pass
