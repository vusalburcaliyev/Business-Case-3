WITH monthly AS (
  SELECT month, SUM(revenue) AS sales, SUM(profit) AS profit
  FROM scoped GROUP BY month
), compared AS (
  SELECT *, LAG(sales,12) OVER (ORDER BY month) AS prior_year_sales
  FROM monthly
)
SELECT month, ROUND(sales/10000.0,2) AS sales_usd,
       ROUND(profit/10000.0,2) AS profit_usd,
       ROUND(100.0*profit/NULLIF(sales,0),2) AS margin_pct,
       ROUND(100.0*(sales-prior_year_sales)/NULLIF(prior_year_sales,0),2) AS sales_yoy_pct
FROM compared ORDER BY month;
