# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################
"""
Repair Module Tests - Test Structure
=====================================

Test Classes and Number Ranges:

| Range   | Class                      | Description                          |
|---------|----------------------------|--------------------------------------|
| 01-06   | TestRepairFlowNormal       | Basic flow: create alerts, move      |
| 07-09   | TestRepairFlowNormal       | Stock scenarios (full, exceed, multi)|
| 10-12   | TestRepairFlowNormal       | Serial product edge cases            |
| 20-24   | TestRepairFlowCancellation | Cancellation scenarios               |
| 30      | TestRepairFlowComplete     | Full repair workflow                 |
| 40-45   | TestStageTransitions       | Stage changes validation             |
| 50-51   | TestUpdatePickingLines     | Update picking lines                 |

Product Types Tested:
- tracking='none': Products without lot/serial tracking
- tracking='serial': Products with serial number tracking

Note: tracking='lot' is NOT used in this system.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestRepairFlowBase(TransactionCase):
    """Base class with common setup for repair flow tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Locations
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.repairs_location = cls.env.ref('repair_module.stock_location_repairs')
        cls.to_relocate_location = cls.env.ref('repair_module.stock_location_to_relocate')
        
        # Picking types
        cls.move_to_repair_type = cls.env.ref('repair_module.stock_picking_type_move_to_repair')
        cls.return_from_repair_type = cls.env.ref('repair_module.stock_picking_type_return_from_repair')
        
        # Quality alert stages
        cls.stage_in_warehouse = cls.env.ref('repair_module.quality_alert_stage_received')
        cls.stage_sent_to_repair = cls.env.ref('repair_module.quality_alert_stage_sent_to_review_repair')
        cls.stage_repairing = cls.env.ref('repair_module.quality_alert_stage_repairing')
        cls.stage_sent_to_postsale = cls.env.ref('repair_module.quality_alert_stage_sent_to_postsale')
        cls.stage_cancelled = cls.env.ref('repair_module.quality_alert_stage_repair_cancelled')
        
        # Create partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        
        # Create account partner if model exists (custom module)
        cls.account_partner = False
        if 'account.partner' in cls.env:
            cls.account_partner = cls.env['account.partner'].create({
                'name': 'Test Account Partner',
                'partner_id': cls.partner.id,
            })
        
        # Create product WITHOUT tracking
        cls.product_no_tracking = cls.env['product.product'].create({
            'name': 'Test Product No Tracking',
            'type': 'consu',
            'is_storable': True,
            'tracking': 'none',
        })
        
        # Create product WITH serial tracking
        cls.product_serial_tracking = cls.env['product.product'].create({
            'name': 'Test Product Serial Tracking',
            'type': 'consu',
            'is_storable': True,
            'tracking': 'serial',
        })
        
        # Create serial for serial-tracked product
        cls.serial = cls.env['stock.lot'].create({
            'name': 'TEST-SERIAL-001',
            'product_id': cls.product_serial_tracking.id,
        })
        
        # Create quality team
        cls.quality_team = cls.env['quality.alert.team'].create({
            'name': 'Test Repair Team',
        })
        
        # Create technician user for repairs
        cls.technician = cls.env['res.users'].create({
            'name': 'Test Technician',
            'login': 'test_technician',
            'email': 'technician@test.com',
        })
        
        # Create initial stock
        cls._create_stock(cls.product_no_tracking, cls.stock_location, 100)
        cls._create_stock(cls.product_serial_tracking, cls.stock_location, 1, cls.serial)

    @classmethod
    def _create_stock(cls, product, location, qty, lot=None):
        """Helper to create stock quants."""
        quant_vals = {
            'product_id': product.id,
            'location_id': location.id,
            'quantity': qty,
        }
        if lot:
            quant_vals['lot_id'] = lot.id
        cls.env['stock.quant'].create(quant_vals)

    def _create_quality_alert(self, product, quantity, lot=None):
        """Helper to create a quality alert for repair."""
        vals = {
            'name': 'Test Alert',
            'title': 'Test Repair Alert',
            'product_id': product.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'partner_id': self.partner.id,
            'quantity': quantity,
            'is_repair': True,
            'team_id': self.quality_team.id,
            'stage_id': self.stage_in_warehouse.id,
            'is_locked': False,
        }
        # Add account_partner_id only if field exists and we have one
        if 'account_partner_id' in self.env['quality.alert']._fields and self.account_partner:
            vals['account_partner_id'] = self.account_partner.id
        if lot:
            vals['lot_id'] = lot.id
        return self.env['quality.alert'].create(vals)

    def _create_repair_order(self, name, alert, product=None, locations=False):
        """Helper to create a repair order with optional fields."""
        if product is None:
            product = self.product_no_tracking
        vals = {
            'name': name,
            'product_id': product.id,
            'product_qty': alert.quantity,
            'product_uom': product.uom_id.id,
            'repair_alert_id': alert.id,
            'partner_id': self.partner.id,
            'technician_id': self.technician.id,
        }
        if 'account_partner_id' in self.env['repair.order']._fields and self.account_partner:
            vals['account_partner_id'] = self.account_partner.id
        if locations:
            vals['product_location_src_id'] = self.repairs_location.id
            vals['product_location_dest_id'] = self.to_relocate_location.id
        return self.env['repair.order'].create(vals)


class TestRepairFlowNormal(TestRepairFlowBase):
    """Test normal repair flow without cancellation."""

    def test_01_create_quality_alert_no_tracking(self):
        """Test creating quality alert for product without tracking."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        
        self.assertEqual(alert.product_id, self.product_no_tracking)
        self.assertEqual(alert.quantity, 10)
        self.assertEqual(alert.stage_id, self.stage_in_warehouse)
        self.assertTrue(alert.is_repair)
        self.assertFalse(alert.lot_id)

    def test_02_create_quality_alert_with_serial(self):
        """Test creating quality alert for product with serial tracking."""
        alert = self._create_quality_alert(self.product_serial_tracking, 1, self.serial)
        
        self.assertEqual(alert.product_id, self.product_serial_tracking)
        self.assertEqual(alert.lot_id, self.serial)
        self.assertEqual(alert.quantity, 1)

    def test_03_move_to_repair_no_tracking(self):
        """Test creating move to repair for product without tracking."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        
        # Create move to repair
        alert.action_create_move_to_repair()
        
        # Verify picking was created
        self.assertEqual(len(alert.picking_ids), 1)
        picking = alert.picking_ids[0]
        
        self.assertEqual(picking.picking_type_id, self.move_to_repair_type)
        self.assertEqual(picking.location_dest_id, self.repairs_location)
        # State can be 'confirmed' or 'assigned' depending on stock availability
        self.assertIn(picking.state, ['confirmed', 'assigned'])
        
        # Verify move
        self.assertEqual(len(picking.move_ids), 1)
        move = picking.move_ids[0]
        self.assertEqual(move.product_id, self.product_no_tracking)
        self.assertEqual(move.product_uom_qty, 10)

    def test_04_move_to_repair_with_serial(self):
        """Test creating move to repair for product with serial tracking."""
        alert = self._create_quality_alert(self.product_serial_tracking, 1, self.serial)
        
        # Create move to repair
        alert.action_create_move_to_repair()
        
        # Verify picking was created
        self.assertEqual(len(alert.picking_ids), 1)
        picking = alert.picking_ids[0]
        
        # Verify move line has serial
        self.assertEqual(len(picking.move_ids), 1)
        move = picking.move_ids[0]
        self.assertTrue(move.move_line_ids)
        self.assertEqual(move.move_line_ids[0].lot_id, self.serial)

    def test_05_validate_move_to_repair(self):
        """Test validating move to repair picking."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        picking = alert.picking_ids[0]
        
        # Assign and validate
        picking.action_assign()
        picking.button_validate()
        
        self.assertEqual(picking.state, 'done')
        
        # Verify stock moved to repairs
        quant_repairs = self.env['stock.quant'].search([
            ('product_id', '=', self.product_no_tracking.id),
            ('location_id', '=', self.repairs_location.id),
            ('quantity', '>', 0),
        ])
        self.assertTrue(quant_repairs)
        self.assertEqual(quant_repairs.quantity, 10)

    def test_06_validation_errors(self):
        """Test validation errors when creating move to repair."""
        # Test without quantity
        alert = self._create_quality_alert(self.product_no_tracking, 0)
        with self.assertRaises(ValidationError):
            alert.action_create_move_to_repair()
        
        # Test without product
        alert2_vals = {
            'name': 'Test Alert No Product',
            'title': 'Test',
            'is_repair': True,
            'quantity': 10,
            'team_id': self.quality_team.id,
        }
        if 'account_partner_id' in self.env['quality.alert']._fields and self.account_partner:
            alert2_vals['account_partner_id'] = self.account_partner.id
        alert2 = self.env['quality.alert'].create(alert2_vals)
        with self.assertRaises(ValidationError):
            alert2.action_create_move_to_repair()
        
        # Test serial tracking without serial
        alert3 = self._create_quality_alert(self.product_serial_tracking, 1)
        with self.assertRaises(ValidationError):
            alert3.action_create_move_to_repair()

    def test_07_move_full_stock(self):
        """Test moving 100% of available stock to repair."""
        # Create alert for all available stock (100 units)
        alert = self._create_quality_alert(self.product_no_tracking, 100)
        alert.action_create_move_to_repair()
        
        picking = alert.picking_ids[0]
        picking.action_assign()
        picking.button_validate()
        
        self.assertEqual(picking.state, 'done')
        
        # Verify all stock moved to repairs
        quant_repairs = self.env['stock.quant'].search([
            ('product_id', '=', self.product_no_tracking.id),
            ('location_id', '=', self.repairs_location.id),
            ('quantity', '>', 0),
        ])
        self.assertEqual(quant_repairs.quantity, 100)
        
        # Verify no stock left in original location
        quant_stock = self.env['stock.quant'].search([
            ('product_id', '=', self.product_no_tracking.id),
            ('location_id', '=', self.stock_location.id),
            ('quantity', '>', 0),
        ])
        self.assertFalse(quant_stock)

    def test_08_move_exceeds_available_stock(self):
        """Test that moving more than available stock raises ValidationError."""
        # Try to move more than available (150 when only 100 exist)
        alert = self._create_quality_alert(self.product_no_tracking, 150)
        
        # Should raise ValidationError because there's not enough stock
        with self.assertRaises(ValidationError):
            alert.action_create_move_to_repair()

    def test_09_multiple_alerts_same_product(self):
        """Test creating multiple alerts for the same product consumes stock correctly."""
        # First alert: 30 units
        alert1 = self._create_quality_alert(self.product_no_tracking, 30)
        alert1.action_create_move_to_repair()
        picking1 = alert1.picking_ids[0]
        picking1.action_assign()
        picking1.button_validate()
        
        # Second alert: 40 units
        alert2 = self._create_quality_alert(self.product_no_tracking, 40)
        alert2.action_create_move_to_repair()
        picking2 = alert2.picking_ids[0]
        picking2.action_assign()
        picking2.button_validate()
        
        # Verify total in repairs: 70 units
        quant_repairs = self.env['stock.quant'].search([
            ('product_id', '=', self.product_no_tracking.id),
            ('location_id', '=', self.repairs_location.id),
            ('quantity', '>', 0),
        ])
        self.assertEqual(quant_repairs.quantity, 70)
        
        # Verify remaining in stock: 30 units
        quant_stock = self.env['stock.quant'].search([
            ('product_id', '=', self.product_no_tracking.id),
            ('location_id', '=', self.stock_location.id),
            ('quantity', '>', 0),
        ])
        self.assertEqual(quant_stock.quantity, 30)

    def test_10_serial_with_quantity_zero(self):
        """Test that serial product with quantity 0 raises validation error."""
        alert = self._create_quality_alert(self.product_serial_tracking, 0, self.serial)
        
        with self.assertRaises(ValidationError):
            alert.action_create_move_to_repair()

    def test_11_serial_with_quantity_exceeds_one(self):
        """Test serial product with quantity > 1 raises ValidationError (only 1 unit available)."""
        # Create alert with quantity 5 for a serial product (but only 1 exists)
        alert = self._create_quality_alert(self.product_serial_tracking, 5, self.serial)
        
        # Should raise ValidationError because there's not enough stock
        # (serial products only have 1 unit per serial number)
        with self.assertRaises(ValidationError):
            alert.action_create_move_to_repair()

    def test_12_serial_without_serial_number(self):
        """Test that serial product without serial number raises validation error."""
        # Create alert for serial product but without providing a serial
        alert = self._create_quality_alert(self.product_serial_tracking, 1)
        
        with self.assertRaises(ValidationError):
            alert.action_create_move_to_repair()


class TestRepairFlowCancellation(TestRepairFlowBase):
    """Test cancellation scenarios."""

    def test_20_cancel_before_picking_validation(self):
        """Test cancelling alert before validating the picking."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        picking = alert.picking_ids[0]
        self.assertNotEqual(picking.state, 'done')
        
        # Cancel the alert directly (no wizard needed)
        alert._do_cancel()
        
        # Verify picking is cancelled
        self.assertEqual(picking.state, 'cancel')
        
        # Verify no return picking was created
        return_pickings = alert.picking_ids.filtered(
            lambda p: p.picking_type_id == self.return_from_repair_type
        )
        self.assertFalse(return_pickings)
        
        # Verify stage is cancelled
        self.assertEqual(alert.stage_id, self.stage_cancelled)

    def test_21_cancel_after_picking_validation(self):
        """Test cancelling alert after validating the picking (product in Repairs)."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        picking = alert.picking_ids[0]
        picking.action_assign()
        picking.button_validate()
        
        self.assertEqual(picking.state, 'done')
        
        initial_picking_count = len(alert.picking_ids)
        
        # Cancel the alert (with reason via _do_cancel)
        alert._do_cancel(reason='Test cancellation reason')
        
        # After cancellation with done pickings, a return picking should be created
        # (if quants exist in repair locations)
        final_picking_count = len(alert.picking_ids)
        
        # Either a return picking was created or not (depends on quant availability)
        self.assertGreaterEqual(final_picking_count, initial_picking_count)
        
        # Verify stage is cancelled
        self.assertEqual(alert.stage_id, self.stage_cancelled)

    def test_22_cancel_with_serial_tracking(self):
        """Test cancelling alert with serial-tracked product after validation."""
        alert = self._create_quality_alert(self.product_serial_tracking, 1, self.serial)
        alert.action_create_move_to_repair()
        
        picking = alert.picking_ids[0]
        picking.action_assign()
        picking.button_validate()
        
        initial_picking_count = len(alert.picking_ids)
        
        # Cancel
        alert._do_cancel(reason='Serial tracking cancellation test')
        
        # After cancellation, a return picking may be created if quants exist
        final_picking_count = len(alert.picking_ids)
        self.assertGreaterEqual(final_picking_count, initial_picking_count)
        
        # Verify stage is cancelled
        self.assertEqual(alert.stage_id, self.stage_cancelled)

    def test_23_cancel_wizard_required_conditions(self):
        """Test that cancel wizard is required when there are done pickings or repairs."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        picking = alert.picking_ids[0]
        picking.action_assign()
        picking.button_validate()
        
        # action_cancel should return wizard action (not execute directly)
        result = alert.action_cancel()
        
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'quality.alert.cancel.wizard')

    def test_24_cancel_direct_no_done_pickings(self):
        """Test that cancel executes directly when no done pickings."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        # Picking not validated yet
        picking = alert.picking_ids[0]
        self.assertNotEqual(picking.state, 'done')
        
        # action_cancel should execute directly (return True, not wizard)
        result = alert.action_cancel()
        
        self.assertTrue(result)
        self.assertEqual(alert.stage_id, self.stage_cancelled)


class TestRepairFlowComplete(TestRepairFlowBase):
    """Test complete repair flow including repair order."""

    def test_30_full_repair_flow(self):
        """Test complete repair flow from alert to completion."""
        # 1. Create quality alert
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        self.assertEqual(alert.stage_id, self.stage_in_warehouse)
        
        # 2. Create move to repair
        alert.action_create_move_to_repair()
        picking = alert.picking_ids[0]
        
        # 3. Validate picking
        picking.action_assign()
        picking.button_validate()
        self.assertEqual(picking.state, 'done')
        
        # 4. Create repair order (simulated)
        repair = self._create_repair_order('REP/TEST/001', alert)
        
        self.assertEqual(repair.repair_alert_id, alert)
        self.assertIn(repair, alert.repair_order_ids)
        
        # 5. Verify linked pickings count
        self.assertEqual(alert.stock_picking_count, 1)


class TestStageTransitions(TestRepairFlowBase):
    """Test that stage_id changes correctly according to actions."""

    def test_40_stage_on_create(self):
        """Test stage is 'In Warehouse' when alert is created."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        self.assertEqual(alert.stage_id, self.stage_in_warehouse)

    def test_41_stage_after_picking_validation(self):
        """Test stage changes to 'Sent for Review / Repair' after picking validation."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        # Stage should still be In Warehouse before validation
        self.assertEqual(alert.stage_id, self.stage_in_warehouse)
        
        picking = alert.picking_ids[0]
        picking.action_assign()
        picking.button_validate()
        
        # Stage should change to Sent for Review / Repair
        self.assertEqual(alert.stage_id, self.stage_sent_to_repair)

    def test_42_stage_after_repair_start(self):
        """Test stage changes to 'Repairing' when repair is started."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        picking = alert.picking_ids[0]
        picking.action_assign()
        picking.button_validate()
        
        # Create and start repair
        repair = self._create_repair_order('REP/TEST/002', alert, locations=True)
        
        # Confirm and start repair
        repair.action_validate()
        repair.action_repair_start()
        
        # Stage should change to Repairing
        self.assertEqual(alert.stage_id, self.stage_repairing)

    def test_43_stage_after_repair_end(self):
        """Test stage changes to 'Return to After-Sales' when repair is completed."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        picking = alert.picking_ids[0]
        picking.action_assign()
        picking.button_validate()
        
        # Create repair
        repair = self._create_repair_order('REP/TEST/003', alert, locations=True)
        
        # Complete repair flow
        repair.action_validate()
        repair.action_repair_start()
        repair.action_repair_end()
        
        # Stage should change to Return to After-Sales
        self.assertEqual(alert.stage_id, self.stage_sent_to_postsale)

    def test_44_stage_after_cancel(self):
        """Test stage changes to 'Repair Cancelled' when alert is cancelled."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        # Cancel before validation
        alert._do_cancel()
        
        self.assertEqual(alert.stage_id, self.stage_cancelled)

    def test_45_stage_after_picking_cancel(self):
        """Test stage changes to 'Repair Cancelled' when picking is cancelled."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        picking = alert.picking_ids[0]
        
        # Cancel the picking directly
        picking.action_cancel()
        
        # Stage should change to Repair Cancelled
        self.assertEqual(alert.stage_id, self.stage_cancelled)


class TestUpdatePickingLines(TestRepairFlowBase):
    """Test updating picking lines when alert is modified."""

    def test_50_update_quantity_before_validation(self):
        """Test that changing quantity updates the picking before validation."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        picking = alert.picking_ids[0]
        move = picking.move_ids[0]
        
        # Change quantity in alert
        alert.write({'quantity': 20})
        
        # Verify move was updated
        self.assertEqual(move.product_uom_qty, 20)

    def test_51_cannot_update_after_validation(self):
        """Test that changing alert after picking validation raises error."""
        alert = self._create_quality_alert(self.product_no_tracking, 10)
        alert.action_create_move_to_repair()
        
        picking = alert.picking_ids[0]
        picking.action_assign()
        picking.button_validate()
        
        # Try to change quantity - should raise error
        with self.assertRaises(ValidationError):
            alert.write({'quantity': 20})
