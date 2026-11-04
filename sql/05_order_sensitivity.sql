WITH orders AS (
  SELECT year, channel, order_no, SUM(revenue) AS sales
  FROM scoped GROUP BY year, channel, order_no
), ranked AS (
  SELECT sales, ROW_NUMBER() OVER (ORDER BY sales, channel, order_no) AS pos,
         COUNT(*) OVER () AS n FROM orders
), cutoff AS (
  SELECT sales AS threshold FROM ranked WHERE pos=(99*n+99)/100
)
SELECT year, ROUND(threshold/10000.0,2) AS threshold_usd,
       COUNT(*) AS orders, SUM(sales>threshold) AS above_cutoff,
       ROUND(SUM(sales)/10000.0,2) AS sales_usd,
       ROUND(SUM(CASE WHEN sales<=threshold THEN sales ELSE 0 END)/10000.0,2) AS sales_below_or_at_cutoff_usd
FROM cutoff CROSS JOIN orders GROUP BY year, threshold ORDER BY year;
