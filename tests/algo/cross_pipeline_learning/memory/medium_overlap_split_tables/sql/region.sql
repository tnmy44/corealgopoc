SELECT
  d.territory AS region
FROM deals d
LEFT JOIN contacts c ON d.contact_id = c.contact_id
