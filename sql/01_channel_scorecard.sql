WITH groups AS (
  SELECT year, channel, SUM(revenue) AS sales, SUM(profit) AS profit,
         COUNT(DISTINCT order_no) AS orders, SUM(units) AS units
  FROM scoped GROUP BY year, channel
), totals AS (
  SELECT year, channel, sales, profit, orders, units FROM groups
  UNION ALL
  SELECT year, 'All channels', SUM(sales), SUM(profit), SUM(orders), SUM(units)
  FROM groups GROUP BY year
), compared AS (
  SELECT *, LAG(sales) OVER (PARTITION BY channel ORDER BY year) AS prev_sales,
            LAG(profit) OVER (PARTITION BY channel ORDER BY year) AS prev_profit
  FROM totals
)
SELECT year, channel, ROUND(sales/10000.0,2) AS sales_usd,
       ROUND(profit/10000.0,2) AS profit_usd, orders, units,
       ROUND(100.0 * profit/NULLIF(sales,0),2) AS margin_pct,
       ROUND(sales/10000.0/NULLIF(orders,0),2) AS aov_usd,
       ROUND((sales-prev_sales)/10000.0,2) AS sales_change_usd,
       ROUND((profit-prev_profit)/10000.0,2) AS profit_change_usd,
       ROUND(100.0 * (sales-prev_sales)/NULLIF(prev_sales,0),2) AS sales_yoy_pct
FROM compared ORDER BY year, channel;
