SELECT
  d.deal_value AS loan_amount_usd
FROM deals d
LEFT JOIN contacts c ON d.contact_id = c.contact_id
