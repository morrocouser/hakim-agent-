"""Pricing Engine — automated tarification rules."""

from typing import Literal
from decimal import Decimal, ROUND_HALF_UP


class PricingEngine:
    """Automated pricing rules with margin formulas."""

    RuleType = Literal["fixed_margin", "percent_margin"]

    def compute_for_shop(
        self,
        shop_id: str,
        rule_type: RuleType = "fixed_margin",
        margin_value: float = 10.0,
        cost_price: float = 0.0,
        shipping: float = 0.0,
        round_to_99: bool = True,
    ) -> dict:
        """Compute selling price for a shop using a fixed margin rule."""
        return self.compute_for_product(
            cost_price=cost_price,
            shipping=shipping,
            rule_type=rule_type,
            margin=0.0,
            fixed_value=margin_value,
            round_to_99=round_to_99,
        )

    def compute_for_product(
        self,
        cost_price: float,
        shipping: float = 0.0,
        rule_type: RuleType = "percent_margin",
        margin: float = 0.3,
        fixed_value: float = 0.0,
        round_to_99: bool = True,
    ) -> dict:
        """Compute selling price based on rule."""
        subtotal = cost_price + shipping

        if rule_type == "fixed_margin":
            raw_price = subtotal + fixed_value
        elif rule_type == "percent_margin":
            raw_price = subtotal * (1 + margin)
        else:
            raise ValueError(f"Unknown rule type: {rule_type}")

        if round_to_99:
            # Commercial rounding to .99
            whole_dollars = int(raw_price)
            price_minus_whole = raw_price - whole_dollars
            if price_minus_whole < 0.99:
                selling_price = whole_dollars + 0.99
            else:
                selling_price = raw_price
            selling_price = float(Decimal(str(selling_price)).quantize(Decimal("0.99"), rounding=ROUND_HALF_UP))
        else:
            selling_price = raw_price

        margin_amount = selling_price - cost_price
        margin_percent = (margin_amount / cost_price * 100) if cost_price > 0 else 0

        return {
            "cost_price": cost_price,
            "shipping": shipping,
            "subtotal": subtotal,
            "margin_type": rule_type,
            "margin_value": margin,
            "raw_price": raw_price,
            "selling_price": round(selling_price, 2),
            "margin_amount": round(margin_amount, 2),
            "margin_percent": round(margin_percent, 2),
        }

    def convert_currency(
        self,
        amount: float,
        from_currency: str = "EUR",
        to_currency: str = "EUR",
    ) -> float:
        """Convert currency using daily exchange rates."""
        if from_currency == to_currency:
            return amount

        # Default rates (stub - replace with API integration)
        rates = {
            "EUR": {"EUR": 1, "USD": 1.08, "GBP": 0.85},
            "USD": {"EUR": 0.93, "USD": 1, "GBP": 0.79},
            "GBP": {"EUR": 1.18, "USD": 1.27, "GBP": 1},
        }

        if from_currency in rates and to_currency in rates[from_currency]:
            return amount * rates[from_currency][to_currency]

        # Try reverse rate
        if to_currency in rates and from_currency in rates[to_currency]:
            return amount / rates[to_currency][from_currency]

        return amount  # fallback to same currency