SELECT
  d.deal_id AS loan_id
FROM deals d
LEFT JOIN contacts c ON d.contact_id = c.contact_id
