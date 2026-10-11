# -*- coding: utf-8 -*-
"""
Step 7: 中国发展切入点分析

数据可得性说明（重要）:
  中国(WB_LPI)     : 有, 2007-2023 双年度, 6 项子指标齐备 -> 定量对标
  中国(Eurostat)   : 数字化强度、H49/H52 碳排放、生物燃料渗透率均不覆盖中国
                     -> 该两个维度以文献定性论证, 并明确标注数据边界
  分析口径: LPI 定量对标(可验证) + 技术/碳维度定性推论(标注为推论)

输出: 物流/figures/fig10-12_*.png, 物流/output/china_report.txt
"""
import sys
import warnings
from pathlib import Path

try:                              # Windows 控制台默认 GBK, 无法输出 € 等字符
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

from plot_style import save, COLORS, MARKERS

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"
OUT = HERE / "output"
OUT.mkdir(exist_ok=True)

CN = {"NLD": "荷兰", "DEU": "德国", "ESP": "西班牙", "CHN": "中国"}
DIMS = ["lpi_customs", "lpi_infrastructure", "lpi_international",
        "lpi_logistics", "lpi_tracking", "lpi_timeliness"]
DIM_CN = ["海关效率", "基础设施", "国际货运", "物流能力", "追踪能力", "时效性"]


def main():
    rep = []
    def p(s=""):
        print(s); rep.append(str(s))

    panel = pd.read_csv(DATA / "panel_master.csv")
    sel = pd.read_csv(DATA / "selected_countries.csv", index_col=0)
    codes = list(sel.index)
    all4 = codes + ["CHN"]

    p("=" * 78)
    p("Step 7: 中国发展切入点分析")
    p("=" * 78)
    p("数据边界: 中国仅 WB_LPI 覆盖; Eurostat 数字化强度与 NACE 碳排放均不含中国。")
    p("         故 LPI 维度做定量对标, 技术与碳维度做定性推论并显式标注。\n")

    # ---------------------------------------------------- 1. 中国 LPI 轨迹
    chn = panel[(panel.iso3 == "CHN") & panel.lpi_overall.notna()].sort_values("year")
    p("-" * 78)
    p("一、中国 LPI 历史轨迹与子指标结构")
    p("-" * 78)
    p(f"  {'年份':<8}{'总分':>8}{'海关':>8}{'基础设施':>10}{'国际货运':>10}"
      f"{'物流能力':>10}{'追踪':>8}{'时效':>8}")
    for _, r in chn.iterrows():
        p(f"  {int(r.year):<8}{r.lpi_overall:>8.3f}{r.lpi_customs:>8.3f}"
          f"{r.lpi_infrastructure:>10.3f}{r.lpi_international:>10.3f}"
          f"{r.lpi_logistics:>10.3f}{r.lpi_tracking:>8.3f}{r.lpi_timeliness:>8.3f}")

    first, last = chn.iloc[0], chn.iloc[-1]
    p(f"\n  {int(first.year)}→{int(last.year)} 提升幅度:")
    gains = {d: last[d] - first[d] for d in DIMS}
    for d, g in sorted(gains.items(), key=lambda x: -x[1]):
        p(f"    {dict(zip(DIMS, DIM_CN))[d]:<10} {first[d]:.3f} → {last[d]:.3f}  "
          f"({g:+.3f})")
    p(f"    {'总分':<10} {first.lpi_overall:.3f} → {last.lpi_overall:.3f}  "
      f"({last.lpi_overall - first.lpi_overall:+.3f})")
    p("\n  >>> 结构特征: 基础设施提升最快(+{:.3f}), 时效性几乎停滞(+{:.3f})"
      .format(gains["lpi_infrastructure"], gains["lpi_timeliness"]))

    # ---------------------------------------------------- 2. 2023 横向差距
    y23 = panel[(panel.year == 2023) & panel.lpi_overall.notna()].set_index("iso3")
    p("\n" + "-" * 78)
    p("二、2023 年中国的横向差距（相对三国均值的缺口）")
    p("-" * 78)
    p(f"  {'维度':<10}{'中国':>8}{'荷兰':>8}{'德国':>8}{'西班牙':>8}"
      f"{'三国均值':>10}{'缺口':>9}")
    gaps = {}
    for d, cn in zip(DIMS, DIM_CN):
        avg = np.mean([y23.loc[c, d] for c in codes])
        gap = y23.loc["CHN", d] - avg
        gaps[cn] = gap
        p(f"  {cn:<10}{y23.loc['CHN', d]:>8.3f}"
          + "".join(f"{y23.loc[c, d]:>8.3f}" for c in codes)
          + f"{avg:>10.3f}{gap:>+9.3f}")
    avg_tot = np.mean([y23.loc[c, "lpi_overall"] for c in codes])
    p(f"  {'总分':<10}{y23.loc['CHN', 'lpi_overall']:>8.3f}"
      + "".join(f"{y23.loc[c, 'lpi_overall']:>8.3f}" for c in codes)
      + f"{avg_tot:>10.3f}{y23.loc['CHN', 'lpi_overall'] - avg_tot:>+9.3f}")
    worst = min(gaps, key=gaps.get)
    best = max(gaps, key=gaps.get)
    p(f"\n  >>> 最大短板: {worst} (缺口 {gaps[worst]:+.3f})"
      f" | 最接近: {best} (缺口 {gaps[best]:+.3f})")

    # ---------------------------------------------------- 3. 德国结构转移
    de = panel[(panel.iso3 == "DEU") & panel.co2_logistics.notna()].sort_values("year")
    p("\n" + "-" * 78)
    p("三、德国内部结构转移: 口径断点识别与真实趋势")
    p("-" * 78)
    p("  重要: 2014 年德国 NACE 分类口径调整, 断点前后不可直接比较。")
    p("")
    for _, r in de[de.year.isin([2006, 2013, 2014, 2019, 2024])].iterrows():
        tag = "   ← 口径调整" if r.year == 2014 else ""
        p(f"  {int(r.year)}: H49={r.co2_h49:>6.2f} Mt  H52={r.co2_h52:>5.2f} Mt  "
          f"H52占比={100 * r.co2_h52 / r.co2_logistics:>5.1f}%{tag}")

    a = de[de.year == 2013].iloc[0]
    b = de[de.year == 2014].iloc[0]
    d0 = de[de.year == 2014].iloc[0]
    d1 = de[de.year == 2024].iloc[0]
    p(f"\n  断点年 (2013→2014): H49 {b.co2_h49 - a.co2_h49:+.2f} Mt  "
      f"H52 {b.co2_h52 - a.co2_h52:+.2f} Mt  "
      f"合计 {b.co2_logistics - a.co2_logistics:+.2f} Mt")
    p(f"  >>> H49 降幅中约 "
      f"{100 * abs((b.co2_h52 - a.co2_h52) / (b.co2_h49 - a.co2_h49)):.0f}% "
      f"由 H52 的等量增加抵消, 属分类归属调整而非减排")

    p(f"\n  口径稳定期 (2014→2024): H49 {d1.co2_h49 - d0.co2_h49:+.2f} Mt  "
      f"H52 {d1.co2_h52 - d0.co2_h52:+.2f} Mt  "
      f"合计 {d1.co2_logistics - d0.co2_logistics:+.2f} Mt")
    p(f"  >>> H52 占比由 {100 * d0.co2_h52 / d0.co2_logistics:.1f}% 升至 "
      f"{100 * d1.co2_h52 / d1.co2_logistics:.1f}%, 固定源设施占比缓慢上升;")
    p(f"      H49 同期下降 {abs(d1.co2_h49 - d0.co2_h49):.2f} Mt, 未再被 H52 抵消。")
    p("  >>> 结论修正: 原『由移动源向固定源大幅迁移』的判断主要源于口径调整,")
    p("      真实趋势是断点后 H49 持续下降、H52 缓慢上升的温和结构变化。")

    # ---------------------------------------------------- 4. 碳强度与数字化
    p("\n" + "-" * 78)
    p("四、碳强度与数字化强度的非线性关系（关键反证）")
    p("-" * 78)
    p(f"  {'国家':<8}{'数字化强度2023(%)':>18}{'碳强度2024(t/百万€)':>20}{'生物燃料2024(%)':>18}")
    for c in codes:
        s = panel[panel.iso3 == c]
        d23 = s[s.year == 2023].digital_basic.values
        r24 = s[s.year == 2024]
        ci = (r24.co2_logistics * 1e6 / r24.gdp_meur).values
        bs = r24.biofuel_share.values
        p(f"  {CN[c]:<8}{d23[0] if len(d23) else np.nan:>18.1f}"
          f"{ci[0] if len(ci) else np.nan:>20.2f}{bs[0] if len(bs) else np.nan:>18.2f}")
    p("\n  >>> 德国数字化强度最低(44.3%)却碳强度最低(4.63);")
    p("      西班牙数字化强度居中(54.5%)却碳强度最高(13.09, 为德国的2.8倍)。")
    p("      说明数字化强度并非脱碳的充分条件, 运输结构(铁路/内河占比)与")
    p("      能源结构(生物燃料渗透率)才是直接中介变量。")

    with open(OUT / "china_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(rep))

    # ==================================================== 可视化
    # 图10: 2023 年四国 LPI 子指标雷达图
    angles = np.linspace(0, 2 * np.pi, len(DIMS), endpoint=False).tolist()
    angles += angles[:1]
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4),
                             subplot_kw=dict(polar=True))
    for ax, (title, series) in zip(axes, [
        ("2023年四国LPI六维子指标对比", None),
        ("中国LPI子指标相对欧洲三国均值的差距", None)]):
        for c in all4:
            v = [y23.loc[c, d] for d in DIMS]
            if ax is axes[0]:
                vals = v + v[:1]
            else:
                avg = [np.mean([y23.loc[cc, d] for cc in codes]) for d in DIMS]
                vals = [100 * a / b for a, b in zip(v, avg)]
                vals = vals + vals[:1]
            ax.plot(angles, vals, marker=MARKERS[c], color=COLORS[c],
                    lw=2.4 if c == "CHN" else 1.8, ms=6,
                    alpha=1.0 if c == "CHN" else 0.75,
                    label=CN[c])
            if c == "CHN":
                ax.fill(angles, vals, color=COLORS["CHN"], alpha=0.14)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(DIM_CN, fontsize=10)
        ax.set_title(title, fontsize=12, pad=20)
        if ax is axes[1]:
            ax.set_ylim(80, 110)
    axes[0].set_ylim(3.0, 4.5)
    axes[0].legend(loc="upper right", bbox_to_anchor=(1.28, 1.12),
                   frameon=False, fontsize=9)
    save(fig, "fig10_中国雷达图.png")

    # 图11: 中国提升幅度 + 2023 缺口
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.6))
    ax = axes[0]
    order = sorted(DIMS, key=lambda d: gains[d])
    vals = [gains[d] for d in order]
    cols = ["#d62728" if d == "lpi_timeliness" else "#1f77b4" for d in order]
    ax.barh([dict(zip(DIMS, DIM_CN))[d] for d in order], vals, color=cols, alpha=0.88)
    for i, v in enumerate(vals):
        ax.text(v + 0.012, i, f"{v:+.3f}", va="center", fontsize=9)
    ax.set_xlabel("LPI 得分提升 (2007 → 2023)")
    ax.set_title("中国LPI子指标提升幅度", fontsize=12)
    ax.set_xlim(0, max(vals) * 1.22)

    ax = axes[1]
    order2 = sorted(DIMS, key=lambda d: gaps[dict(zip(DIMS, DIM_CN))[d]])
    gv = [gaps[dict(zip(DIMS, DIM_CN))[d]] for d in order2]
    cols2 = ["#d62728" if g < -0.4 else "#ff7f0e" if g < -0.25 else "#2ca02c"
             for g in gv]
    ax.barh([dict(zip(DIMS, DIM_CN))[d] for d in order2], gv, color=cols2, alpha=0.88)
    for i, v in enumerate(gv):
        ax.text(v - 0.03 if v < 0 else v + 0.02, i, f"{v:+.3f}",
                va="center", ha="right" if v < 0 else "left", fontsize=9)
    ax.axvline(0, color="black", lw=1)
    ax.set_xlabel("相对三国均值的缺口 (2023)")
    ax.set_title("中国相对欧洲三国的维度缺口", fontsize=12)
    ax.set_xlim(min(gv) * 1.35, 0.12)
    save(fig, "fig11_中国差距.png")

    # 图12: 德国结构转移 + 三国碳强度
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.6))
    ax = axes[0]
    de2 = de[de.year >= 2006]
    ax.stackplot(de2.year, de2.co2_h49, de2.co2_h52,
                 labels=["陆路运输", "仓储与运输辅助"],
                 colors=["#9ecae1", "#d62728"], alpha=0.88)
    ax.plot(de2.year, de2.co2_logistics, color="black", lw=1.8, label="物流合计")
    ax.set_title("德国物流碳排放结构转移", fontsize=12)
    ax.set_xlabel("年份"); ax.set_ylabel("CO₂ (Mt)")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(frameon=False, fontsize=9, loc="upper right")

    ax = axes[1]
    for c in codes:
        s = panel[(panel.iso3 == c) & panel.co2_logistics.notna() & panel.gdp_meur.notna()]
        s = s[s.year >= 2008].copy()
        s["ci"] = s.co2_logistics * 1e6 / s.gdp_meur
        ax.plot(s.year, s.ci, marker=MARKERS[c], color=COLORS[c], lw=2.2, ms=4,
                label=CN[c])
    ax.set_title("三国物流碳强度对比", fontsize=12)
    ax.set_xlabel("年份"); ax.set_ylabel("t CO₂ / 百万欧元")
    ax.legend(frameon=False)
    save(fig, "fig12_结构转移.png")

    p(f"\n[保存] fig10-12 与 {OUT / 'china_report.txt'}")
    return rep


if __name__ == "__main__":
    main()
