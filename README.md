# BATS (Binance Automated Trading System)

## Project Structure
- `src/`: Source code
  - `core/`: Exchange provider, Risk manager, Order executor
  - `strategies/`: Strategy implementations
  - `utils/`: Configuration and logging utilities
- `docs/`: Design and API documentation
- `config.yaml`: Runtime configuration

## Setup
1. Copy `.env.example` to `.env` and fill in your API keys.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the system: `python src/main.py` (Implementation in progress)
