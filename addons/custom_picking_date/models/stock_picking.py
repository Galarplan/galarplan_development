from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    scheduled_date = fields.Datetime(
        string='Fecha Programada',
        required=True,
    )

    def write(self, vals):
        for record in self:
            # Control para cambiar la fecha programada
            if 'scheduled_date' in vals and record.state in ['done', 'cancel']:
                if self.env.user.has_group('custom_picking_date.group_edit_picking_date'):
                    old_date = record.scheduled_date
                    new_date = fields.Datetime.to_datetime(vals['scheduled_date'])
                    if old_date != new_date:
                        super(StockPicking, record).write({'is_locked': False})
                        super(StockPicking, record).write({'scheduled_date': new_date})
                        record.message_post(
                            body=_("La *fecha programada* fue modificada de %s a %s por %s.") % (
                                old_date.strftime("%Y-%m-%d %H:%M:%S") if old_date else 'N/A',
                                new_date.strftime("%Y-%m-%d %H:%M:%S"),
                                self.env.user.name
                            )
                        )
                    vals.pop('scheduled_date')  # Ya lo procesamos

            # Control para cambiar la fecha efectiva (date_done)
            if 'date_done' in vals and record.state in ['done', 'cancel']:
                if self.env.user.has_group('custom_picking_date.group_edit_picking_date'):
                    old_date = record.date_done
                    new_date = fields.Datetime.to_datetime(vals['date_done'])
                    if old_date != new_date:
                        super(StockPicking, record).write({'date_done': new_date})
                        record.message_post(
                            body=_("La *fecha efectiva* fue modificada de %s a %s por %s.") % (
                                old_date.strftime("%Y-%m-%d %H:%M:%S") if old_date else 'N/A',
                                new_date.strftime("%Y-%m-%d %H:%M:%S"),
                                self.env.user.name
                            )
                        )
                    vals.pop('date_done')  # Ya lo procesamos

        return super().write(vals)


    user_has_group_custom_picking_date = fields.Boolean(
        compute='_compute_user_group_edit_date',
        store=False
    )

    def _compute_user_group_edit_date(self):
        for rec in self:
            rec.user_has_group_custom_picking_date = self.env.user.has_group('custom_picking_date.group_edit_picking_date')


    def _set_scheduled_date(self):
        for picking in self:
            # ⚠️ Solo bloquea si el usuario NO tiene el grupo
            if picking.state in ('done', 'cancel') and not self.env.user.has_group('custom_picking_date.group_edit_picking_date'):
                raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))

            # Ejecuta la lógica normal
            picking.move_ids.write({'date': picking.scheduled_date})