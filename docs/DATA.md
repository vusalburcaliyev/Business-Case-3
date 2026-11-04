# Data preparation and reproducibility

Source: Microsoft's [AdventureWorks sample databases](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/adventure-works). The database is fictitious. This portfolio links to the upstream distribution and publishes summarized outputs only.

| Source | What I used |
|---|---|
| FactInternetSales and FactResellerSales | Order date, order number, line number, units, currency and territory keys, extended value, sales amount, and recorded product cost |
| DimProduct, DimProductSubcategory, DimProductCategory | Product-to-category relationships |
| DimSalesTerritory and DimCurrency | United States and USD scope |

I read seven pipe-delimited files using the upstream install script's column order. I checked the order date against its date key and used integer amounts at the source's four-decimal precision. The recorded discount is a float, so I checked that extended value less discount matched sales amount within roughly one ten-thousandth of a dollar. I prevented duplicate order lines within each channel, checked lookup keys, and kept valid negative-profit lines. The source checks found no duplicate order lines and no uncategorized lines in scope; **11,376** scoped lines had negative gross profit.

Sales measure = source SalesAmount (after recorded discount, before tax and freight). Gross profit = SalesAmount − TotalProductCost. Gross margin = gross profit ÷ sales. Average order value = sales ÷ distinct orders (channel + order number). Years are assigned by order date. I did not estimate operating profit or infer promotion effects.

## Rebuild

1. Download [AdventureWorksDW-data-warehouse-install-script.zip](https://github.com/microsoft/sql-server-samples/releases/download/adventureworks/AdventureWorksDW-data-warehouse-install-script.zip). Use the install ZIP rather than a database backup.
2. Run the following from the repository root:

```bash
python scripts/build.py path/to/AdventureWorksDW-data-warehouse-install-script.zip
node --test tests/dashboard.test.cjs
```

Python 3.10+ with SQLite 3.25+ is sufficient; no Python packages or SQL Server install are needed. Node.js is only needed for the dashboard tests. The build recreates the model in memory, reconciles the annual totals to the channel, month, category, and discount outputs, and regenerates the dashboard and preview. The tested ZIP SHA-256 was `73c27309d17cd30bf5351665401106abf649d9f9a9ecb0c770682f6be965aba8`.
