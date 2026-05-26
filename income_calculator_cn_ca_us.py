"""
Tax Comparison Tool – 2026 Edition

📌 简介：
本脚本用于计算在 中国（上海）🇨🇳、加拿大BC省🇨🇦、美国加州（加州 + 联邦）🇺🇸 三个地区工作的个人所得税及强制缴费（如五险、社保、养老金、医保），以获取税后收入及综合税负对比。

支持功能包括：
- 自动汇率换算（USD/CAD/RMB）
- 适用 2026 年税率表（联邦 + 地方）
- 中国：从应纳税所得额中正确扣除 60,000 基本减除费用、三险一金
- 加拿大：BPA（按 net income phase-out）、Canada Employment Amount、CPP/EI 抵免
- 美国：联邦/加州各自标准扣除分开计算；含加州 SDI 1.2%、Additional Medicare 0.9%、CA Personal Exemption Credit
- 自动判断社保缴费上限（如 CPP/CPP2/EI/SS、上海五险）

📥 输入：
- `income`: 收入金额（数值）
- `currency`: 收入币种，支持 `"USD"`、`"CAD"`、`"RMB"`

📤 输出（每地区）：
- Gross: 税前总收入
- Tax: 所得税（联邦+地方，已扣除标准扣除/抵免）
- Social: 强制社保缴费（三险/CPP+EI/SS+Medicare+SDI）
- Housing Fund: 中国住房公积金（仅中国 > 0）
- Net: 税后净收入（= Gross - Tax - Social - Housing Fund）
- Effective Rate: 综合税率（税+社保+公积金 / 税前）

🧮 使用方式：
运行主程序或调用 `calculate_all(amount, currency)`，即可获得结构化结果字典.

📚 数据来源（2026 年）：
- 中国（上海）：上海市人社局；个人所得税综合所得税率表（2018 改革至今未变）
- 加拿大联邦 / BC 省：CRA 官方 2026 税率表；BC 2026 预算（最低档由 5.06% → 5.60%）
- 美国联邦：IRS Revenue Procedure 2025-32（含 OBBBA 调整）
- 美国加州：FTB 2025 官方税档（FTB 通常在年底/次年初才公布 2026 档，当前先沿用 2025）
- SSA / CRA / CFIB：2026 年 Social Security / CPP / EI 上限

⚠️ 注意：上海社保 2025.7.1-2026.6.30 基数；2026.7.1 起的新基数预计 2026 年 7-9 月公布。

"""

# Exchange Rates (as of mid-May 2026)
usd_to_rmb = 6.80   # 2026-05-23 ≈ 6.7953（NimbusCalc）
usd_to_cad = 1.38   # 2026-05-25 ≈ 1.3809（Yahoo Finance / Xe）

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
    # 综合所得税 7 级超额累进（年度应纳税所得额）
    brackets = [
        (36000, 0.03, 0),
        (144000, 0.10, 2520),
        (300000, 0.20, 16920),
        (420000, 0.25, 31920),
        (660000, 0.30, 52920),
        (960000, 0.35, 85920),
        (float('inf'), 0.45, 181920)
    ]

    # 上海市社保缴费基数上下限（2025.7.1 - 2026.6.30；2026.7.1 起新基数尚未公布）
    base_lower_limit = 7460 * 12
    base_upper_limit = 37302 * 12
    contribution_base = min(max(income_rmb, base_lower_limit), base_upper_limit)

    # 个人三险一金缴费比例（工伤纯雇主，生育已并入医疗，故个人只交三险 + 公积金）
    pension_rate = 0.08          # 养老保险
    medical_rate = 0.02          # 医疗保险（含生育）
    unemployment_rate = 0.005    # 失业保险
    housing_fund_rate = 0.07     # 住房公积金（上海个人 5%-7%，此处取常见 7%）

    pension = contribution_base * pension_rate
    medical = contribution_base * medical_rate
    unemployment = contribution_base * unemployment_rate
    housing_fund = contribution_base * housing_fund_rate

    social_insurance = pension + medical + unemployment  # 三险个人合计 10.5%

    # 应纳税所得额 = 综合所得 - 基本减除费用(60,000/年) - 三险一金 - 专项附加扣除(此处=0)
    basic_deduction = 60000
    taxable_income = max(0, income_rmb - basic_deduction - social_insurance - housing_fund)

    tax = 0
    for threshold, rate, quick_deduction in brackets:
        if taxable_income <= threshold:
            tax = max(0, taxable_income * rate - quick_deduction)
            break

    return tax, social_insurance, housing_fund


def canada_bc_tax(income_cad):

    # 2026 联邦税档（CRA 官方；最低档自 2026 起永久降至 14%）
    federal = [
        (58523, 0.14),
        (117045, 0.205),
        (181440, 0.26),
        (258482, 0.29),
        (float('inf'), 0.33)
    ]

    # 2026 BC 省税档（BC 2026 预算：最低档由 5.06% → 5.60%；阈值按 CPI 2.2% 上调）
    provincial = [
        (50363, 0.056),
        (100728, 0.077),
        (115648, 0.105),
        (140430, 0.1229),
        (190405, 0.147),
        (265545, 0.168),
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

    # ── 强制缴费 ──
    # CPP1 2026：基本豁免 $3,500；YMPE $74,600；总税率 5.95%（基础 4.95% + 增强 1%）
    cpp_contributory = max(0, min(income_cad, 74600) - 3500)
    cpp1_base = cpp_contributory * 0.0495        # 基础部分 → 走非可退抵免
    cpp1_enhanced = cpp_contributory * 0.0100    # 增强部分 → 走收入扣除
    cpp1_total = cpp_contributory * 0.0595
    # CPP2 2026：$74,600 - $85,000 区间按 4%；最高 $416 → 走收入扣除
    cpp2 = max(0, min(income_cad, 85000) - 74600) * 0.04
    # EI 2026：上限 $68,900；雇员税率 1.63%；最高 $1,123.07 → 走非可退抵免
    ei = min(income_cad, 68900) * 0.0163

    # ── 应纳税所得额（Net income, T1 Line 23600）──
    # 普通雇员：从收入中扣除 CPP 增强部分 + CPP2（其余如 RRSP 等可扣项此处忽略）
    net_income = max(0, income_cad - cpp1_enhanced - cpp2)
    federal_tax = calc_tax(net_income, federal)
    provincial_tax = calc_tax(net_income, provincial)

    # ── 非可退抵免（按各自最低档税率折抵）──
    # 联邦 BPA 2026：$16,452，**按 net income** 自 $181,440 起线性递减至 $14,829（$258,482+ 起最低）
    if net_income <= 181440:
        fed_bpa = 16452
    elif net_income >= 258482:
        fed_bpa = 14829
    else:
        fed_bpa = 16452 - (16452 - 14829) * (net_income - 181440) / (258482 - 181440)

    # BC BPA 2026：$13,216（无 phase-out）
    bc_bpa = 13216

    # Canada Employment Amount 2026：$1,501（**仅联邦**，BC 无对应省级版本，只 Yukon 有）
    canada_employment_amount = min(max(income_cad, 0), 1501)

    # 抵免基数（按各自最低档税率折抵）
    # 联邦：BPA + Canada Employment Amount + CPP1 基础部分 + EI
    federal_credits = (fed_bpa + canada_employment_amount + cpp1_base + ei) * 0.14
    # BC：BPA + CPP1 基础部分 + EI（无 Canada Employment Amount）
    bc_credits = (bc_bpa + cpp1_base + ei) * 0.056

    federal_tax = max(0, federal_tax - federal_credits)
    provincial_tax = max(0, provincial_tax - bc_credits)

    return federal_tax + provincial_tax, cpp1_total + cpp2 + ei


def usa_ca_tax(income_usd):

    # 2026 联邦税档 Single（IRS Rev. Proc. 2025-32，含 OBBBA 调整）
    federal = [
        (12400, 0.10),
        (50400, 0.12),
        (105700, 0.22),
        (201775, 0.24),
        (256225, 0.32),
        (640600, 0.35),
        (float('inf'), 0.37)
    ]

    # 加州 2025 单身税档 Single（FTB 2026 税档尚未公布，沿用 2025 官方值）
    # 注：>$1M 部分含 1% Behavioral Health Services Tax（2026 起由 MHST 更名）→ 最高 13.3%
    state = [
        (11079, 0.01),
        (26264, 0.02),
        (41452, 0.04),
        (57542, 0.06),
        (72724, 0.08),
        (371479, 0.093),
        (445771, 0.103),
        (742953, 0.113),
        (1000000, 0.123),
        (float('inf'), 0.133)
    ]
    # 标准扣除：联邦与加州各自不同
    federal_std_deduction = 16100   # 2026 IRS Single（IRS Rev. Proc. 2025-32）
    ca_std_deduction = 5706         # 加州 FTB 2025 Single（FTB 2026 尚未公布）

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

    federal_taxable = max(0, income_usd - federal_std_deduction)
    state_taxable = max(0, income_usd - ca_std_deduction)
    fed_tax = calc_tax(federal_taxable, federal)
    state_tax = calc_tax(state_taxable, state)

    # 加州 Personal Exemption Credit（Single）：2025 = $153（2026 FTB 尚未公布，沿用 2025）
    # 直接抵减州税额（非可退）
    ca_personal_exemption_credit = 153
    state_tax = max(0, state_tax - ca_personal_exemption_credit)

    # ── 强制缴费 ──
    # Social Security 2026：上限 $184,500，税率 6.2%（SSA）
    ss = min(income_usd, 184500) * 0.062
    # Medicare：1.45%，无上限
    medicare = income_usd * 0.0145
    # Additional Medicare 0.9%：单身 wages > $200,000 部分（阈值不随通胀指数化）
    addl_medicare = max(0, income_usd - 200000) * 0.009
    # 加州 SDI（State Disability Insurance）：2024 起取消上限；2026 税率 1.3%（EDD 官方 DE44）
    sdi = income_usd * 0.013
    return fed_tax + state_tax, ss + medicare + addl_medicare + sdi


def calculate_all(amount, currency):
    usd, rmb, cad = convert_income(amount, currency)

    cn_tax, cn_social, cn_housing = china_shanghai_tax(rmb)
    ca_tax, ca_social = canada_bc_tax(cad)
    us_tax, us_social = usa_ca_tax(usd)

    # 注：公积金属于强制缴费且离开了当月工资条，因此计入"social"和"net 减项"以保证跨地区可比；
    # 但单列 housing_fund 字段，方便用户区分"真税"与"强制储蓄"。
    results = {
        "China_Shanghai": {
            "gross": rmb, "tax": cn_tax, "social": cn_social,
            "housing_fund": cn_housing,
            "net": rmb - cn_tax - cn_social - cn_housing,
            "rate": (cn_tax + cn_social + cn_housing) / rmb
        },
        "Canada_BC": {
            "gross": cad, "tax": ca_tax, "social": ca_social,
            "housing_fund": 0,
            "net": cad - ca_tax - ca_social,
            "rate": (ca_tax + ca_social) / cad
        },
        "USA_CA": {
            "gross": usd, "tax": us_tax, "social": us_social,
            "housing_fund": 0,
            "net": usd - us_tax - us_social,
            "rate": (us_tax + us_social) / usd
        }
    }
    return results


if __name__ == "__main__":
    income = 1300000
    currency = "RMB"  # "RMB", "USD", or "CAD"
    res = calculate_all(income, currency)
    for region, data in res.items():
        print(f"\n{region}:")
        print(f"  Gross: {data['gross']:.2f}")
        print(f"  Tax: {data['tax']:.2f}")
        print(f"  Social: {data['social']:.2f}")
        if data['housing_fund'] > 0:
            print(f"  Housing Fund: {data['housing_fund']:.2f}")
        print(f"  Net: {data['net']:.2f}")
        print(f"  Effective Rate: {data['rate']:.2%}")
