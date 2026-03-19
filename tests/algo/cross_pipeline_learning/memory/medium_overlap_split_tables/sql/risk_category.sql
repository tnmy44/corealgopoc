SELECT
  d.deal_grade AS risk_category
FROM deals d
LEFT JOIN contacts c ON d.contact_id = c.contact_id
