Profiling Report

customers.csv  
File size: 18,183 bytes  
Shape: 250 rows × 7 columns  
Column types: all strings  
Missing values: 3 in email, 2 in city  
Duplicate rows: 2  
Customer_id is not unique  

Observations:  
- Customer_id should be unique but duplicates exist, so deduplication is needed  
- Missing emails and cities show incomplete records  
- Signup_date must be validated to ensure dates are not in the future  

Candidate validation rules:  
1. Customer_id must be unique and non-null  
2. Email must contain @ and a valid domain  
3. Signup_date must be a valid date not in the future  

---

orders.json  
Root type: list  
Record count: 250  
Top-level keys: order_id, customer_id, shipping, order_timestamp, shipping_fee, status, total_amount, item_count, subtotal  
Nested fields: shipping object  
Timestamp fields: order_timestamp  
Numeric fields: item_count, subtotal, shipping_fee, total_amount  
Nulls: none  

Observations:  
- Shipping is a nested object, needs flattening or JSON storage  
- Numeric fields are consistent and non-null  
- Order_timestamp is a good candidate for watermarking  

Implications:  
- Flatten shipping for relational storage or keep JSON for flexibility  
- Enforce order_id as unique key  
- Use order_timestamp for incremental ingestion  

---

products.parquet  
File size: 14,652 bytes  
Shape: 200 rows × 7 columns  
Column types: product_id, product_name, category, brand (string), unit_price (float), stock_quantity (int), weight_kg (float)  
Missing values: none  

Observations:  
- Dataset is clean with no missing values  
- Schema preservation is stronger than CSV or JSON  
- Parquet is efficient for analytics but less common for operational feeds  

Implications:  
- Product_id can serve as primary key  
- Parquet’s columnar storage is ideal for queries and compression  
- Operational systems usually prefer row-oriented formats like CSV, JSON, or relational tables  

---

Summary  
Customers.csv requires deduplication and validation of emails and dates.  
Orders.json requires flattening of nested structures and enforcement of unique keys.  
Products.parquet is clean and schema-consistent, showing the difference between operational and analytical formats.  