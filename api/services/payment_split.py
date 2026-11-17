PLATFORM_FEE_PERCENT = 15
INSTRUCTOR_SPLIT_PERCENT = 100 - PLATFORM_FEE_PERCENT


def build_asaas_split(wallet_id):
    return [{"walletId": wallet_id, "percentualValue": INSTRUCTOR_SPLIT_PERCENT}]


def estimate_instructor_share(total_price):
    return round(float(total_price) * INSTRUCTOR_SPLIT_PERCENT / 100, 2)