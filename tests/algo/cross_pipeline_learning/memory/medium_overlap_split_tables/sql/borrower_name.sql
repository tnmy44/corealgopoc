SELECT
  c.contact_name AS borrower_name
FROM deals d
LEFT JOIN contacts c ON d.contact_id = c.contact_id
