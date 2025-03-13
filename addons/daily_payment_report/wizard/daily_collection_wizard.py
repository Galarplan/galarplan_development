from odoo import models, fields, api

class DailyCollectionWizard(models.TransientModel):
    _name = 'daily.collection.wizard'
    _description = 'Wizard para Recaudación Diaria'

    date = fields.Date(string='Fecha', required=True)
    journal_ids = fields.Many2many('account.journal', string='Diarios', required=True)
    collection_lines = fields.One2many(
        'daily.collection.line.wizard', 
        'wizard_id', 
        string='Líneas de Recaudación'
    )

    @api.onchange('date', 'journal_ids')
    def _onchange_date_journals(self):
        """Traer los registros asociados a los diarios y la fecha."""
        if self.date and self.journal_ids:
            payments = self.env['account.payment'].search([
                ('date', '=', self.date),
                ('journal_id', 'in', self.journal_ids.ids),
                ('state', '=', 'posted') , # Solo los pagos validados
                ('payment_type','=','inbound')#entrantes
            ])
            lines = [(5,)]
            for payment in payments:
                lines.append((0, 0, {
                    'journal_id': payment.journal_id.id,
                    'partner_id': payment.partner_id.id,
                    'amount': payment.amount,
                    'payment_name': payment.name
                }))
            self.collection_lines = lines

    def action_print_report(self):
        self.ensure_one()
        """Imprimir el reporte con los datos seleccionados."""
        return self.env.ref('daily_payment_report.report_collection').report_action(self)


class DailyCollectionLineWizard(models.TransientModel):
    _name = 'daily.collection.line.wizard'
    _description = 'Línea de Recaudación Diaria'

    wizard_id = fields.Many2one('daily.collection.wizard', string='Wizard')
    journal_id = fields.Many2one('account.journal', string='Diario')
    partner_id = fields.Many2one('res.partner', string='Socio')
    amount = fields.Float(string='Monto')
    payment_name = fields.Char(string='Recibo')
