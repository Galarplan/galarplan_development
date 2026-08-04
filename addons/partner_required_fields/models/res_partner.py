from odoo import models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    REQUIRED_FIELDS = {
        'name': _("Nombre"),
        'vat': _("Identificación"),
        'street': _("Dirección"),
        'email': _("Correo electrónico"),
    }

    def _validate_required_fields(self, values):
        """
        Valida que todos los campos obligatorios tengan valor.
        Se acepta teléfono fijo o celular.
        """
        missing = []

        for field, label in self.REQUIRED_FIELDS.items():
            value = values.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                missing.append(label)

        phone = values.get('phone')
        mobile = values.get('mobile')

        if (not phone or not str(phone).strip()) and (not mobile or not str(mobile).strip()):
            missing.append(_("Teléfono o celular"))

        if missing:
            raise ValidationError(_(
                "No se puede guardar el contacto.\n\n"
                "Complete los siguientes campos obligatorios:\n\n• %s"
            ) % "\n• ".join(missing))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._validate_required_fields(vals)

        return super().create(vals_list)

    def write(self, vals):
        for partner in self:
            values = {
                'name': vals.get('name', partner.name),
                'vat': vals.get('vat', partner.vat),
                'street': vals.get('street', partner.street),
                'email': vals.get('email', partner.email),
                'phone': vals.get('phone', partner.phone),
                'mobile': vals.get('mobile', partner.mobile),
            }

            partner._validate_required_fields(values)

        return super().write(vals)