def calculate_returns(principal: float, days: int, profit: float) -> dict:
    """
    根据本金、收益天数和利润金额计算不同周期的收益率和收益金额。

    参数:
    principal (float): 本金金额，必须大于 0
    days (int): 投资天数，必须大于 0
    profit (float): 指定天数内的总利润

    返回:
    dict: 包含收益率（%）和各周期收益金额的字典
    """
    if principal <= 0 or days <= 0:
        raise ValueError("Principal and days must be positive numbers.")

    # 日化收益率
    daily_rate = profit / principal / days

    # 各周期化收益率
    weekly_rate = daily_rate * 7
    monthly_rate = daily_rate * 30
    annual_rate = daily_rate * 365

    # 不同周期的收益金额
    daily_profit = principal * daily_rate
    weekly_profit = principal * weekly_rate
    monthly_profit = principal * monthly_rate
    annual_profit = principal * annual_rate

    return {
        "收益率 (%)": {
            "日化收益率": round(daily_rate * 100, 4),
            "周化收益率": round(weekly_rate * 100, 4),
            "月化收益率": round(monthly_rate * 100, 4),
            "年化收益率": round(annual_rate * 100, 4),
        },
        "收益金额": {
            "每日收益": round(daily_profit, 2),
            "每周收益": round(weekly_profit, 2),
            "每月收益": round(monthly_profit, 2),
            "每年收益": round(annual_profit, 2),
        }
    }


if __name__ == "__main__":
    principal = 6000.0
    days = 1
    profit = 1.25

    result = calculate_returns(principal, days, profit)

    print("=== 收益率 (%) ===")
    for label, value in result["收益率 (%)"].items():
        print(f"{label}: {value:.4f}%")

    print("\n=== 不同周期收益金额 ===")
    for label, value in result["收益金额"].items():
        print(f"{label}: {value:.2f} 元")
