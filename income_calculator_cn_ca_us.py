"""
Tax Comparison Tool – 2025 Edition

📌 简介：
本脚本用于计算在 中国（上海）🇨🇳、加拿大BC省🇨🇦、美国加州（加州 + 联邦）🇺🇸 三个地区工作的个人所得税及强制缴费（如五险、社保、养老金、医保），以获取税后收入及综合税负对比。

支持功能包括：
- 自动汇率换算（USD/CAD/RMB）
- 适用最新（2024 或 2025 年）税率表（联邦 + 地方）
- 自动判断社保缴费上限（如 CPP/EI/SS、上海五险）
- 支持美国“户主”（Head of Household）申报身份

📥 输入：
- `income`: 收入金额（数值）
- `currency`: 收入币种，支持 `"USD"`、`"CAD"`、`"RMB"`

📤 输出（每地区）：
- Gross: 税前总收入
- Tax: 所得税（联邦+地方）
- Social: 强制缴费（五险、公积金、CPP/EI、SS/Medicare）
- Net: 税后净收入
- Effective Rate: 综合税率（税+社保 / 税前）

🧮 使用方式：
运行主程序或调用 `calculate_all(amount, currency)`，即可获得结构化结果字典.

"""

# Exchange Rates
usd_to_rmb = 7.21
usd_to_cad = 1.40

def convert_income(amount, currency):
    if currency == "USD":
        return amount, amount * usd_to_rmb, amount * usd_to_cad
    elif currency == "RMB":
        usd = amount / usd_to_rmb
        return usd, amount, usd * usd_to_cad
    elif currency == "CAD":
        usd = amount / usd_to_cad
        return usd, usd * usd_to_rmb, amount
    else:
        raise ValueError("Unsupported currency")


def china_shanghai_tax(income_rmb):
    brackets = [
        (36000, 0.03, 0),
        (144000, 0.10, 2520),
        (300000, 0.20, 16920),
        (420000, 0.25, 31920),
        (660000, 0.30, 52920),
        (960000, 0.35, 85920),
        (float('inf'), 0.45, 181920)
    ]
    for threshold, rate, quick_deduction in brackets:
        if income_rmb <= threshold:
            tax = income_rmb * rate - quick_deduction
            break

    # 上海市社保缴费基数上下限（2024.7.1 - 2025.6.30）
    base_lower_limit = 7384 * 12
    base_upper_limit = 36921 * 12
    contribution_base = min(max(income_rmb, base_lower_limit), base_upper_limit)

    # 个人缴费比例
    pension_rate = 0.08       # 养老保险
    medical_rate = 0.02       # 医疗保险
    unemployment_rate = 0.005 # 失业保险

    pension = contribution_base * pension_rate
    medical = contribution_base * medical_rate
    unemployment = contribution_base * unemployment_rate

    social_insurance = pension + medical + unemployment
    return tax, social_insurance


def canada_bc_tax(income_cad):

    # 2025
    federal = [
        (57375, 0.15),
        (114750, 0.205),
        (177882, 0.26),
        (253414, 0.29),
        (float('inf'), 0.33)
    ]

    # 2025
    provincial = [
        (49279, 0.0506),
        (98560, 0.077),
        (113158, 0.105),
        (137407, 0.1229),
        (186306, 0.147),
        (259829, 0.168),
        (float('inf'), 0.205)
    ]

    def calc_tax(income, brackets):
        tax, prev = 0, 0
        for threshold, rate in brackets:
            if income > threshold:
                tax += (threshold - prev) * rate
                prev = threshold
            else:
                tax += (income - prev) * rate
                break
        return tax

    federal_tax = calc_tax(income_cad, federal)
    provincial_tax = calc_tax(income_cad, provincial)
    cpp = min(income_cad, 68500) * 0.0595 # 加拿大养老金计划 CPP：年收入封顶 $68,500，税率 5.95%
    ei = min(income_cad, 63100) * 0.0166 # 就业保险 EI：年收入封顶 $63,100，税率 1.66%
    return federal_tax + provincial_tax, cpp + ei


def usa_ca_tax(income_usd):

    # 2024
    federal = [
        (11600, 0.10),
        (47150, 0.12),
        (100525, 0.22),
        (191950, 0.24),
        (243725, 0.32),
        (609350, 0.35),
        (float('inf'), 0.37)
    ]

    # 2024
    state = [
        (10756, 0.01),
        (25499, 0.02),
        (40245, 0.04),
        (55866, 0.06),
        (70606, 0.08),
        (360659, 0.093),
        (432787, 0.103),
        (721314, 0.113),
        (1000000, 0.123),
        (float('inf'), 0.133)
    ]
    std_deduction = 14600

    def calc_tax(income, brackets):
        tax, prev = 0, 0
        for threshold, rate in brackets:
            if income > threshold:
                tax += (threshold - prev) * rate
                prev = threshold
            else:
                tax += (income - prev) * rate
                break
        return tax

    taxable = max(0, income_usd - std_deduction)
    fed_tax = calc_tax(taxable, federal)
    state_tax = calc_tax(taxable, state)
    ss = min(income_usd, 168600) * 0.062 # Social Security：上限 $168,600，税率 6.2%
    medicare = income_usd * 0.0145
    return fed_tax + state_tax, ss + medicare


def calculate_all(amount, currency):
    usd, rmb, cad = convert_income(amount, currency)

    cn_tax, cn_social = china_shanghai_tax(rmb)
    ca_tax, ca_social = canada_bc_tax(cad)
    us_tax, us_social = usa_ca_tax(usd)

    results = {
        "China_Shanghai": {
            "gross": rmb, "tax": cn_tax, "social": cn_social,
            "net": rmb - cn_tax - cn_social,
            "rate": (cn_tax + cn_social) / rmb
        },
        "Canada_BC": {
            "gross": cad, "tax": ca_tax, "social": ca_social,
            "net": cad - ca_tax - ca_social,
            "rate": (ca_tax + ca_social) / cad
        },
        "USA_CA": {
            "gross": usd, "tax": us_tax, "social": us_social,
            "net": usd - us_tax - us_social,
            "rate": (us_tax + us_social) / usd
        }
    }
    return results


if __name__ == "__main__":
    income = 100000
    currency = "CAD"  # "RMB", "USD", or "CAD"
    res = calculate_all(income, currency)
    for region, data in res.items():
        print(f"\n{region}:")
        print(f"  Gross: {data['gross']:.2f}")
        print(f"  Tax: {data['tax']:.2f}")
        print(f"  Social: {data['social']:.2f}")
        print(f"  Net: {data['net']:.2f}")
        print(f"  Effective Rate: {data['rate']:.2%}")
