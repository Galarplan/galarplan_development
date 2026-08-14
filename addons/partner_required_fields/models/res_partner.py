from odoo import models, api, _
from odoo.exceptions import ValidationError
import re


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
        # ALEX CODE
        if self.env.context.get('from_user_copy'):
            return   
        # FIN ALEX CODE
             
        missing = []

        for field, label in self.REQUIRED_FIELDS.items():
            value = values.get(field)

            if not value or (isinstance(value, str) and not value.strip()):
                missing.append(label)

        phone = values.get('phone')
        mobile = values.get('mobile')

        if (not phone or not str(phone).strip()) and \
           (not mobile or not str(mobile).strip()):
            missing.append(_("Teléfono o celular"))

        if missing:
            raise ValidationError(_(
                "No se puede guardar el contacto.\n\n"
                "Complete los siguientes campos obligatorios:\n\n• %s"
            ) % "\n• ".join(missing))


    @api.model_create_multi
    def create(self, vals_list):

        # =========================================================
        # COPIA DE USUARIO
        # =========================================================

        if self.env.context.get('from_user_copy'):

            original_partner_id = self.env.context.get(
                'original_partner_id'
            )

            if original_partner_id:

                original_partner = self.browse(
                    original_partner_id
                )

                for vals in vals_list:

                    # -------------------------------------------------
                    # NOMBRE
                    # -------------------------------------------------

                    original_name = (
                        original_partner.name or _("Contacto")
                    )

                    base_name = re.sub(
                        r'\s*-\s*COPIA(?:\s+\d+)?$',
                        '',
                        original_name,
                        flags=re.IGNORECASE
                    )

                    name = f"{base_name} - COPIA"

                    counter = 1

                    while self.search_count([
                        ('name', '=', name)
                    ]):
                        counter += 1
                        name = (
                            f"{base_name} - COPIA {counter}"
                        )

                    vals['name'] = name

                    # -------------------------------------------------
                    # VAT
                    # -------------------------------------------------

                    original_vat = original_partner.vat or ''

                    if original_vat:

                        base_vat = re.sub(
                            r'-COPIA(?:-\d+)?$',
                            '',
                            original_vat,
                            flags=re.IGNORECASE
                        )

                        vat = f"{base_vat}-COPIA"

                        counter = 1

                        while self.search_count([
                            ('vat', '=', vat)
                        ]):
                            counter += 1
                            vat = f"{base_vat}-COPIA-{counter}"

                        vals['vat'] = vat

                        # Tipo de identificación:
                        # 3 = Identificación del exterior
                        vals['l10n_latam_identification_type_id'] = 3
                        base_vat = re.sub(
                            r'-COPIA(?:-\d+)?$',
                            '',
                            original_vat,
                            flags=re.IGNORECASE
                        )

                        vat = f"{base_vat}-COPIA"

                        counter = 1

                        while self.search_count([
                            ('vat', '=', vat)
                        ]):
                            counter += 1
                            vat = (
                                f"{base_vat}-COPIA-{counter}"
                            )

                        vals['vat'] = vat

                    # -------------------------------------------------
                    # EMAIL
                    # -------------------------------------------------

                    original_email = (
                        original_partner.email or ''
                    )

                    if (
                        original_email
                        and '@' in original_email
                    ):

                        local_part, domain = (
                            original_email.split('@', 1)
                        )

                        local_part = re.sub(
                            r'\+\d+$',
                            '',
                            local_part
                        )

                        counter = 1

                        email = (
                            f"{local_part}+{counter}@{domain}"
                        )

                        while self.search_count([
                            ('email', '=ilike', email)
                        ]):
                            counter += 1
                            email = (
                                f"{local_part}+{counter}@{domain}"
                            )

                        vals['email'] = email

                    else:

                        counter = 1

                        email = (
                            f"copia{counter}@abc.com"
                        )

                        while self.search_count([
                            ('email', '=ilike', email)
                        ]):
                            counter += 1
                            email = (
                                f"copia{counter}@abc.com"
                            )

                        vals['email'] = email

        # =========================================================
        # VALIDACIÓN NORMAL
        # =========================================================

        if not self.env.context.get('from_user_copy'):

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


    def copy(self, default=None):
        """
        Duplica el contacto generando valores únicos para
        nombre, VAT y correo electrónico.
        """

        self.ensure_one()

        default = dict(default or {})

        # =========================================================
        # NOMBRE
        # =========================================================

        original_name = self.name or _("Contacto")

        base_name = re.sub(
            r'\s*-\s*COPIA(?:\s+\d+)?$',
            '',
            original_name,
            flags=re.IGNORECASE
        )

        name = f"{base_name} - COPIA"

        counter = 1

        while self.search_count([('name', '=', name)]):
            counter += 1
            name = f"{base_name} - COPIA {counter}"

        default['name'] = name

        # =========================================================
        # VAT
        # =========================================================

        original_vat = self.vat or ''

        if original_vat:

            base_vat = re.sub(
                r'-COPIA(?:-\d+)?$',
                '',
                original_vat,
                flags=re.IGNORECASE
            )

            vat = f"{base_vat}-COPIA"

            counter = 1

            while self.search_count([('vat', '=', vat)]):
                counter += 1
                vat = f"{base_vat}-COPIA-{counter}"

            default['vat'] = vat

        # =========================================================
        # EMAIL
        # =========================================================

        original_email = self.email or ''

        if original_email and '@' in original_email:

            local_part, domain = original_email.split('@', 1)

            # Quitar números anteriores:
            # gato+1 -> gato
            # gato+2 -> gato
            local_part = re.sub(
                r'\+\d+$',
                '',
                local_part
            )

            counter = 1

            email = f"{local_part}+{counter}@{domain}"

            while self.search_count([
                ('email', '=ilike', email)
            ]):
                counter += 1
                email = f"{local_part}+{counter}@{domain}"

            default['email'] = email

        else:
            # Si el original no tiene correo,
            # generamos uno para que pase la validación.

            counter = 1

            email = f"copia{counter}@abc.com"

            while self.search_count([
                ('email', '=ilike', email)
            ]):
                counter += 1
                email = f"copia{counter}@abc.com"

            default['email'] = email

        # =========================================================
        # OBTENER DATOS DE LA COPIA
        # =========================================================

        vals = self.copy_data(default)[0]

        # =========================================================
        # ASEGURAR LOS VALORES OBLIGATORIOS
        # =========================================================

        vals['name'] = default['name']
        vals['vat'] = default.get('vat')
        vals['email'] = default['email']

        # =========================================================
        # CREAR LA COPIA
        # =========================================================

        return self.with_context(
            duplicating_partner=True
        ).create(vals)    