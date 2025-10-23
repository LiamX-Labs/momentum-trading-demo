"""
Position sizing logic for the strategy.

Risk Management Rules:
- 2% risk per trade (of account equity)
- 20% stop distance (trailing stop from peak)
- Position size = (Account * Risk%) / Stop%
- Max 5 concurrent positions
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class PositionSizer:
    """
    Position sizing calculator with risk management.

    Attributes:
        account_size: Total account equity
        risk_per_trade_pct: Risk percentage per trade (default: 0.02 for 2%)
        stop_loss_pct: Stop loss percentage (default: 0.20 for 20%)
        max_positions: Maximum concurrent positions (default: 5)
        max_position_size_pct: Maximum single position size (default: 0.20 for 20%)
    """

    account_size: float
    risk_per_trade_pct: float = 0.02  # 2% risk
    stop_loss_pct: float = 0.20  # 20% stop
    max_positions: int = 5
    max_position_size_pct: float = 0.20  # 20% max per position

    def calculate_position_size(
        self,
        entry_price: float,
        current_positions: int = 0
    ) -> Dict:
        """
        Calculate position size based on risk parameters.

        Args:
            entry_price: Entry price for the position
            current_positions: Number of currently open positions

        Returns:
            Dictionary with:
            - position_size_usd: Dollar amount to invest
            - position_size_pct: Percentage of account
            - num_contracts: Number of units/contracts
            - risk_usd: Dollar amount at risk
            - can_open: Boolean, whether position can be opened

        Formula:
            Position Size = (Account * Risk%) / Stop%
            Position Size = (Account * 0.02) / 0.20 = Account * 0.10 (10%)
        """
        # Check if can open new position
        can_open = current_positions < self.max_positions

        if not can_open:
            return {
                'position_size_usd': 0,
                'position_size_pct': 0,
                'num_contracts': 0,
                'risk_usd': 0,
                'can_open': False,
                'reason': f'Max positions ({self.max_positions}) reached'
            }

        # Calculate position size based on risk
        risk_usd = self.account_size * self.risk_per_trade_pct
        position_size_usd = risk_usd / self.stop_loss_pct
        position_size_pct = position_size_usd / self.account_size

        # Cap at max position size
        if position_size_pct > self.max_position_size_pct:
            position_size_pct = self.max_position_size_pct
            position_size_usd = self.account_size * self.max_position_size_pct
            risk_usd = position_size_usd * self.stop_loss_pct

        # Calculate number of contracts
        num_contracts = position_size_usd / entry_price

        return {
            'position_size_usd': position_size_usd,
            'position_size_pct': position_size_pct,
            'num_contracts': num_contracts,
            'risk_usd': risk_usd,
            'can_open': True,
            'reason': 'Position sizing calculated'
        }

    def update_account_size(self, new_size: float):
        """Update account size (after P&L)."""
        self.account_size = new_size

    def get_max_portfolio_risk(self) -> float:
        """
        Calculate maximum portfolio risk.

        Returns:
            Maximum risk in USD if all positions hit stops
        """
        max_risk = self.max_positions * (self.account_size * self.risk_per_trade_pct)
        return max_risk

    def get_max_portfolio_exposure(self) -> float:
        """
        Calculate maximum portfolio exposure.

        Returns:
            Maximum exposure in USD with all positions open
        """
        max_exposure = self.max_positions * (self.account_size * self.risk_per_trade_pct / self.stop_loss_pct)
        return max_exposure


def calculate_position_size(
    account_size: float,
    entry_price: float,
    risk_per_trade_pct: float = 0.02,
    stop_loss_pct: float = 0.20
) -> Dict:
    """
    Simple position size calculator.

    Args:
        account_size: Account equity
        entry_price: Entry price
        risk_per_trade_pct: Risk per trade (default: 0.02)
        stop_loss_pct: Stop loss percentage (default: 0.20)

    Returns:
        Dictionary with position sizing details
    """
    sizer = PositionSizer(
        account_size=account_size,
        risk_per_trade_pct=risk_per_trade_pct,
        stop_loss_pct=stop_loss_pct
    )

    return sizer.calculate_position_size(entry_price)


if __name__ == "__main__":
    # Test position sizer
    print("Testing Position Sizer...")

    # Initialize with $10,000 account
    sizer = PositionSizer(account_size=10000)

    print(f"\n{'='*60}")
    print("Position Sizer Configuration")
    print(f"{'='*60}")
    print(f"Account Size: ${sizer.account_size:,.2f}")
    print(f"Risk per Trade: {sizer.risk_per_trade_pct*100:.1f}%")
    print(f"Stop Loss: {sizer.stop_loss_pct*100:.1f}%")
    print(f"Max Positions: {sizer.max_positions}")
    print(f"\nMax Portfolio Risk: ${sizer.get_max_portfolio_risk():,.2f}")
    print(f"Max Portfolio Exposure: ${sizer.get_max_portfolio_exposure():,.2f}")

    # Calculate position size for entry at $0.25
    print(f"\n{'='*60}")
    print("Position Size Calculation")
    print(f"{'='*60}")

    entry_price = 0.25
    result = sizer.calculate_position_size(entry_price, current_positions=0)

    print(f"Entry Price: ${entry_price}")
    print(f"\nPosition Size:")
    print(f"  USD: ${result['position_size_usd']:,.2f}")
    print(f"  Percentage: {result['position_size_pct']*100:.1f}%")
    print(f"  Contracts: {result['num_contracts']:,.2f}")
    print(f"\nRisk:")
    print(f"  At Risk: ${result['risk_usd']:,.2f}")
    print(f"  As % of Account: {(result['risk_usd']/sizer.account_size)*100:.1f}%")

    # Test with multiple positions
    print(f"\n{'='*60}")
    print("Multiple Positions Test")
    print(f"{'='*60}")

    for i in range(6):
        result = sizer.calculate_position_size(0.25, current_positions=i)
        if result['can_open']:
            print(f"Position {i+1}: ${result['position_size_usd']:,.2f} ({result['position_size_pct']*100:.1f}%)")
        else:
            print(f"Position {i+1}: {result['reason']}")

    print("\n✓ Position sizer working correctly!")
