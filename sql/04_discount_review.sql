-- Compare groups of reseller lines. An order can contain both types of lines.
WITH buckets AS (
  SELECT year,
         CASE WHEN revenue < gross THEN 'Discounted' ELSE 'Full price' END AS price_group,
         COUNT(*) AS lines, SUM(units) AS units, SUM(gross) AS gross,
         SUM(revenue) AS sales, SUM(profit) AS profit
  FROM scoped WHERE channel='Reseller' GROUP BY year, price_group
)
SELECT year, price_group, lines, units, ROUND(sales/10000.0,2) AS sales_usd,
       ROUND((gross-sales)/10000.0,2) AS discounts_usd,
       ROUND(profit/10000.0,2) AS profit_usd,
       ROUND(100.0*profit/NULLIF(sales,0),2) AS margin_pct,
       ROUND(100.0*sales/SUM(sales) OVER (PARTITION BY year),2) AS reseller_sales_share_pct
FROM buckets ORDER BY year, price_group;
