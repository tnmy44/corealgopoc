-- Source: deterministic match from union_by_type (adapted: UNION collapsed to CASE on pay_type discriminator)
WITH
computed AS (
  SELECT emp_id, name,
         CASE
           WHEN pay_type = 'salaried' THEN pay_rate / 12.0
           WHEN pay_type = 'hourly' THEN pay_rate * hours_per_week * 4.33
         END AS monthly_pay,
         dept AS department
  FROM employees
)
SELECT * FROM computed
