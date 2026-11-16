import nbformat as nbf
nb = nbf.v4.new_notebook()
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
c = []
c.append(md("""# GSA SmartPay purchase-card data

Monthly spend, transactions and card counts by agency, from GSA's SmartPay "Stats Tool" spreadsheet (smartpay.gsa.gov/about/statistics). The notebook downloads the file; nothing is stored in this repo.

This is all purchase-card activity, not only micro-purchases. There is no breakdown by transaction size, merchant, or individual purchase."""))
c.append(code("""import io, urllib.request
import pandas as pd
import matplotlib.pyplot as plt

URL = "https://smartpay.gsa.gov/files/StatsTool_FY26OCT.xlsx"  # check the statistics page for a newer file
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; data-research)"})
xlsx = urllib.request.urlopen(req).read()

raw = pd.read_excel(io.BytesIO(xlsx), sheet_name="RawData_ByMonth", header=None)
hdr = raw.index[raw.notna().sum(axis=1) >= 8][0]
df = raw.iloc[hdr + 1:].set_axis(raw.iloc[hdr], axis=1).dropna(how="all").reset_index(drop=True)
for col in ["CalendarYear", "CalendarMonth", "Cards", "Spend", "Transactions"]:
    df[col] = pd.to_numeric(df[col])
df["month"] = pd.to_datetime(dict(year=df.CalendarYear, month=df.CalendarMonth, day=1))
print(len(df), "rows,", df.month.min().date(), "to", df.month.max().date())
df.head()"""))
c.append(md("Columns: one row per agency × month × program (Purchase, Travel, Fleet) × bank."))
c.append(code("""print(df.Program.value_counts(), "\\n")
print(sorted(df.AgencyName.unique()))"""))
c.append(md("Check: October totals for all programs match GSA's own dashboard tab."))
c.append(code("""dash = {"FY24": 3014665434.28, "FY25": 3305496742.97, "FY26": 2814090103.33}  # 'GSA SmartPay Dashboard' tab, October
for fy, v in dash.items():
    s = df[(df.FiscalYear == fy) & (df.CalendarMonth == 10)].Spend.sum()
    assert abs(s - v) < 0.01, (fy, s, v)
print("matches")"""))
c.append(md("## Purchase cards, all agencies"))
c.append(code("""p = df[df.Program == "Purchase"]
nat = p.groupby("month")[["Spend", "Transactions", "Cards"]].sum()
nat["avg_purchase"] = nat.Spend / nat.Transactions
recent = nat[nat.index >= "2023-01-01"]

from matplotlib.ticker import FuncFormatter
fmt = {"Spend": FuncFormatter(lambda v, _: f"${v/1e9:.1f}B"), "Transactions": FuncFormatter(lambda v, _: f"{v/1e6:.1f}M"),
       "Cards": FuncFormatter(lambda v, _: f"{v/1e3:,.0f}K"), "avg_purchase": FuncFormatter(lambda v, _: f"${v:,.0f}")}
fig, axes = plt.subplots(4, 1, figsize=(9, 11), sharex=True)
for ax, col, label in zip(axes, ["Spend", "Transactions", "Cards", "avg_purchase"],
                          ["Spend ($)", "Transactions", "Cards", "Average purchase ($)"]):
    ax.plot(recent.index, recent[col], lw=2, color="#2a6f97")
    ax.yaxis.set_major_formatter(fmt[col])
    ax.set_ylim(bottom=0)
    ax.set_title(label, loc="left", fontsize=11)
    ax.axvline(pd.Timestamp("2025-02-26"), color="#999", lw=1, ls="--")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#eee")
axes[2].text(pd.Timestamp("2025-03-15"), 1.0e6, "card freeze order, 2025-02-26", fontsize=9, color="#666")
plt.tight_layout()"""))
c.append(md("Year-over-year change, same calendar month."))
c.append(code("""yoy = (nat / nat.shift(12) - 1).mul(100).round(1)
out = pd.DataFrame({"spend_$M": (nat.Spend / 1e6).round(0), "spend_yoy_%": yoy.Spend,
                    "transactions_K": (nat.Transactions / 1e3).round(0), "txn_yoy_%": yoy.Transactions,
                    "cards_K": (nat.Cards / 1e3).round(1), "avg_purchase_$": nat.avg_purchase.round(0)})
out[out.index >= "2024-07-01"]"""))
c.append(md("## By agency: March–August 2025 vs. March–August 2024"))
c.append(code("""def window(year, months=range(3, 9)):
    w = p[(p.CalendarYear == year) & (p.CalendarMonth.isin(months))]
    return w.groupby("AgencyName")[["Spend", "Transactions"]].sum()

a, b = window(2024), window(2025)
t = pd.DataFrame({"txn_2024": a.Transactions, "txn_2025": b.Transactions,
                  "spend_2024_$M": (a.Spend / 1e6).round(1), "spend_2025_$M": (b.Spend / 1e6).round(1)})
t["txn_change_%"] = (100 * (t.txn_2025 / t.txn_2024 - 1)).round(1)
t["spend_change_%"] = (100 * (b.Spend / a.Spend - 1)).round(1)
t.sort_values("txn_2024", ascending=False)"""))
c.append(code("""s = t.sort_values("txn_change_%")
fig, ax = plt.subplots(figsize=(8, 8))
ax.barh(s.index, s["txn_change_%"], color=["#b5651d" if v < 0 else "#2a6f97" for v in s["txn_change_%"]], height=0.7)
ax.axvline(0, color="#666", lw=1)
ax.set_title("Purchase-card transactions, Mar–Aug 2025 vs. 2024 (% change)", loc="left", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()"""))
c.append(md("## One agency"))
c.append(code("""def agency(name, program="Purchase", start="2023-01-01"):
    a = df[(df.AgencyName == name) & (df.Program == program)].groupby("month")[["Spend", "Transactions", "Cards"]].sum()
    return a[a.index >= start]

agency("Department of Interior").tail(18)"""))
c.append(md("""## Caveats

- Card counts have a break in August–September 2023 (about 203,000 fewer under "Small Agencies and Organizations" and 162,000 fewer at HHS, while their spend and transactions don't drop the same way). It looks like a counting change; don't compare card counts across it.
- January 2025's card count (about 730,000) is a one-month spike; December 2024 and February 2025 are both about 686,000. Cards limited to $1 still count as open.
- The government shutdown of Oct 1 – Nov 12, 2025 depresses October–November 2025.
- GSA changed its agency groupings in October 2024 (CFO Act agencies plus "Small Agencies and Organizations"); check that rollup before comparing across that date.
- Drops mix the card freeze with staff cuts and agency closures.
- The spreadsheet's intro sheet says "For Official Use Only," though GSA posts it publicly; this repo links to it rather than copying it."""))
nb["cells"] = c
nbf.write(nb, "smartpay_purchase_cards.ipynb")
