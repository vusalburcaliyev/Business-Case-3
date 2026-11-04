"""Generate the README preview from the published scorecard."""
from html import escape


def make(root, payload):
    rows = {r["channel"]: r for r in payload["01_channel_scorecard"] if r["year"] == "2013"}
    total = rows["All channels"]
    def text(x, y, value, size=16, fill="#202642", weight=500):
        return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}">{escape(value)}</text>'
    def money(n):
        return ("−" if n < 0 else "") + f"${abs(n):,.0f}"
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 320" font-family="system-ui,sans-serif" role="img">',
        '<title>2013 AdventureWorks U.S. sales and gross profit by channel</title>',
        '<rect x="1" y="1" width="898" height="318" rx="14" fill="#f4f5fa" stroke="#d9deec"/>',
        '<path d="M15 1H885Q899 1 899 15V88H1V15Q1 1 15 1" fill="#232b50"/>',
        text(23, 29, "BUSINESS CASE 03  /  2013 U.S. SALES", 13, "#d2caff", 750),
        text(23, 62, "Sales and gross profit tell different stories", 25, "#ffffff", 760),
    ]
    cards = [("Total sales",money(total["sales_usd"])),("Gross profit",money(total["profit_usd"])),
             ("Gross margin",f'{total["margin_pct"]:.2f}%')]
    for i, (label, value) in enumerate(cards):
        x=22+290*i
        svg.extend([f'<rect x="{x}" y="102" width="278" height="63" rx="8" fill="white" stroke="#d9deec"/>',
                    text(x+11, 126, label, 13, "#535f76", 650),text(x+11, 150, value, 22, weight=750)])
    svg.extend([text(24, 192, "Channel", 14, weight=750),text(258, 192, "Sales", 14, weight=750),
                text(518, 192, "Gross profit", 14, weight=750),text(735, 192, "Gross margin", 14, weight=750)])
    for i, channel in enumerate(("Internet","Reseller")):
        r=rows[channel]
        y=224+38*i
        svg.extend([f'<path d="M24 {y-19}H874" stroke="#d9deec"/>',text(24,y,channel,16,weight=650),
                    text(258,y,money(r["sales_usd"])),text(518,y,money(r["profit_usd"]),16,
                    "#af4838" if r["profit_usd"]<0 else "#5545a8",750),text(735,y,f'{r["margin_pct"]:.2f}%')])
    svg.extend([text(24, 300, "Source: Microsoft AdventureWorksDW · Fictitious sample · USD orders", 12, "#535f76"),"</svg>"])
    (root/"assets/sales_profit.svg").write_text("\n".join(svg)+"\n",encoding="utf-8")
