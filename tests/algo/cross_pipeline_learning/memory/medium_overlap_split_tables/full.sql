SELECT
  d.deal_id AS loan_id,
  c.contact_name AS borrower_name,
  d.deal_value AS loan_amount_usd,
  d.deal_grade AS risk_category,
  d.territory AS region
FROM deals d
LEFT JOIN contacts c ON d.contact_id = c.contact_id
