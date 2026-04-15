# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Copia la raíz única antigua a la tabla relacional Many2many."""
    cr.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_name = '_rma_m2m_root_loc_mig'
        """
    )
    if not cr.fetchone():
        return
    cr.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'res_company_rma_move_desk_root_loc_rel'
        """
    )
    if not cr.fetchone():
        cr.execute("DROP TABLE IF EXISTS _rma_m2m_root_loc_mig")
        return
    cr.execute(
        """
        INSERT INTO res_company_rma_move_desk_root_loc_rel (company_id, location_id)
        SELECT m.company_id, m.location_id
        FROM _rma_m2m_root_loc_mig m
        WHERE NOT EXISTS (
            SELECT 1 FROM res_company_rma_move_desk_root_loc_rel r
            WHERE r.company_id = m.company_id AND r.location_id = m.location_id
        )
        """
    )
    cr.execute("DROP TABLE IF EXISTS _rma_m2m_root_loc_mig")
