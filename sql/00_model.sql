PRAGMA foreign_keys = ON;
CREATE TABLE category(id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE subcategory(id INTEGER PRIMARY KEY, category_id INTEGER NOT NULL REFERENCES category(id));
CREATE TABLE product(id INTEGER PRIMARY KEY, subcategory_id INTEGER REFERENCES subcategory(id), name TEXT NOT NULL);
CREATE TABLE territory(id INTEGER PRIMARY KEY, region TEXT NOT NULL, country TEXT NOT NULL);
CREATE TABLE currency(id INTEGER PRIMARY KEY, code TEXT NOT NULL);
CREATE TABLE sale(
  channel TEXT NOT NULL, order_no TEXT NOT NULL, line_no INTEGER NOT NULL,
  day TEXT NOT NULL, product_id INTEGER NOT NULL REFERENCES product(id),
  territory_id INTEGER NOT NULL REFERENCES territory(id),
  currency_id INTEGER NOT NULL REFERENCES currency(id),
  units INTEGER NOT NULL CHECK(units > 0),
  gross INTEGER NOT NULL CHECK(gross > 0),
  revenue INTEGER NOT NULL CHECK(revenue > 0 AND revenue <= gross),
  cost INTEGER NOT NULL CHECK(cost >= 0),
  PRIMARY KEY(channel, order_no, line_no)
);
-- Amounts remain in ten-thousandths of a dollar until presentation.
CREATE VIEW scoped AS
SELECT s.*, substr(day,1,4) AS year, substr(day,1,7) AS month,
       COALESCE(c.name,'Unclassified') AS category,
       t.region, s.revenue - s.cost AS profit
FROM sale s
JOIN currency fx ON fx.id=s.currency_id
JOIN territory t ON t.id=s.territory_id
JOIN product p ON p.id=s.product_id
LEFT JOIN subcategory sub ON sub.id=p.subcategory_id
LEFT JOIN category c ON c.id=sub.category_id
WHERE t.country='United States' AND fx.code='USD'
  AND day >= '2012-01-01' AND day < '2014-01-01';
