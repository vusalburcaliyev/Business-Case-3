WITH category_totals AS (
  SELECT year, category, SUM(revenue) AS sales, SUM(profit) AS profit, SUM(units) AS units
  FROM scoped GROUP BY year, category
)
SELECT year, category, units, ROUND(sales/10000.0,2) AS sales_usd,
       ROUND(profit/10000.0,2) AS profit_usd,
       ROUND(100.0*profit/NULLIF(sales,0),2) AS margin_pct,
       DENSE_RANK() OVER (PARTITION BY year ORDER BY sales DESC) AS sales_rank,
       DENSE_RANK() OVER (PARTITION BY year ORDER BY profit DESC) AS profit_rank,
       ROUND(100.0*profit/SUM(profit) OVER (PARTITION BY year),2) AS profit_share_pct
FROM category_totals ORDER BY year, sales_rank, category;
