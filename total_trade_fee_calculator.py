def calculate_total_trade_fee(r1, r2, r3, r4):
    """
    计算法币进出交易所全过程的总手续费率

    参数:
    r1: 法币从银行转入交易所的手续费率（如0.01表示1%）
    r2: 法币在交易所转为虚拟货币的手续费率
    r3: 虚拟货币转为法币的手续费率
    r4: 法币从交易所转入银行的手续费率

    返回:
    float: 总手续费率（百分比）
    """
    capital_left = (1 - r1) * (1 - r2) * (1 - r3) * (1 - r4)
    total_fee = 1 - capital_left
    return total_fee * 100  # 返回百分比形式


if __name__ == "__main__":
    # 默认手续费率定义（如需修改，改这里）
    r1 = 0.0000  # 银行 -> 交易所
    r2 = 0.0020  # 法币 -> 虚拟货币
    r3 = 0.0020  # 虚拟货币 -> 法币
    r4 = 0.0000  # 交易所 -> 银行

    total_fee_percent = calculate_total_trade_fee(r1, r2, r3, r4)

    print(f"总手续费率为: {total_fee_percent:.4f}%")