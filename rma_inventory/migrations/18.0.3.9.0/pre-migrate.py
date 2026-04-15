# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Respalda la antigua Many2one antes de que el ORM elimine la columna al actualizar el módulo."""
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'res_company' AND column_name = 'rma_move_desk_root_location_id'
        """
    )
    if not cr.fetchone():
        return
    cr.execute("DROP TABLE IF EXISTS _rma_m2m_root_loc_mig")
    cr.execute(
        """
        CREATE TABLE _rma_m2m_root_loc_mig AS
        SELECT id AS company_id, rma_move_desk_root_location_id AS location_id
        FROM res_company
        WHERE rma_move_desk_root_location_id IS NOT NULL
        """
    )
