import unittest

from services.payment_split import (
    INSTRUCTOR_SPLIT_PERCENT,
    PLATFORM_FEE_PERCENT,
    build_asaas_split,
    estimate_instructor_share,
)


class PaymentSplitTests(unittest.TestCase):
    def test_platform_and_instructor_shares_are_fixed_at_15_85(self):
        self.assertEqual(PLATFORM_FEE_PERCENT, 15)
        self.assertEqual(INSTRUCTOR_SPLIT_PERCENT, 85)
        self.assertEqual(PLATFORM_FEE_PERCENT + INSTRUCTOR_SPLIT_PERCENT, 100)
        self.assertEqual(
            build_asaas_split("wallet_123"),
            [{"walletId": "wallet_123", "percentualValue": 85}],
        )

    def test_estimates_instructor_share_rounded_to_cents(self):
        self.assertEqual(estimate_instructor_share(100), 85)
        self.assertEqual(estimate_instructor_share(105), 89.25)
        self.assertEqual(estimate_instructor_share(0.10), 0.09)


if __name__ == "__main__":
    unittest.main()