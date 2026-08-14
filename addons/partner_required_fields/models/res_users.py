from odoo import api, models
import re


class ResUsers(models.Model):
    _inherit = 'res.users'

    # =========================================================
    # CREAR USUARIO
    # =========================================================

    @api.model_create_multi
    def create(self, vals_list):

        # =====================================================
        # IMPORTANTE
        # =====================================================
        # Si estamos COPIANDO un usuario, NO ejecutamos
        # la lógica de "CreaUser".
        #
        # La copia tiene su propio proceso mediante:
        # from_user_copy=True
        # =====================================================

        if not self.env.context.get('from_user_copy'):

            Partner = self.env['res.partner']

            for vals in vals_list:

                # -------------------------------------------------
                # NOMBRE
                # -------------------------------------------------

                user_name = vals.get('name') or 'Usuario'

                # Evitamos duplicar (CreaUser) si por algún motivo
                # el proceso ya lo hubiera colocado.

                if '(CreaUser)' not in user_name:
                    vals['name'] = (
                        f"{user_name} (CreaUser)"
                    )

                # -------------------------------------------------
                # DIRECCIÓN
                # -------------------------------------------------

                vals['street'] = 'Calle y Avenida'

                # -------------------------------------------------
                # TELÉFONO
                # -------------------------------------------------

                vals['phone'] = '5555555555'

                # -------------------------------------------------
                # VAT / IDENTIFICACIÓN
                # -------------------------------------------------

                original_vat = vals.get('vat') or ''

                if original_vat:

                    base_vat = re.sub(
                        r'-COPIA(?:-\d+)?$',
                        '',
                        original_vat,
                        flags=re.IGNORECASE
                    )

                    vat = f"{base_vat}-COPIA"

                else:

                    vat = '111111111'

                counter = 1

                while Partner.search_count([
                    ('vat', '=', vat)
                ]):

                    counter += 1

                    if original_vat:
                        vat = (
                            f"{base_vat}-COPIA-{counter}"
                        )
                    else:
                        vat = (
                            f"111111111{counter}"
                        )

                vals['vat'] = vat

                # -------------------------------------------------
                # TIPO DE IDENTIFICACIÓN
                # -------------------------------------------------

                vals[
                    'l10n_latam_identification_type_id'
                ] = 3

                # -------------------------------------------------
                # EMAIL
                # -------------------------------------------------

                original_email = vals.get('email') or ''

                # Si el usuario no trae email pero el login
                # es un correo, utilizamos el login como base.

                if (
                    not original_email
                    and '@' in (vals.get('login') or '')
                ):
                    original_email = vals.get('login')

                if (
                    original_email
                    and '@' in original_email
                ):

                    local_part, domain = (
                        original_email.split('@', 1)
                    )

                    # Quitamos un posible +1, +2, etc.
                    #
                    # gato+1@abc.com
                    # gato+2@abc.com
                    #
                    # se convierte en:
                    #
                    # gato@abc.com

                    local_part = re.sub(
                        r'\+\d+$',
                        '',
                        local_part
                    )

                    counter = 1

                    email = (
                        f"{local_part}+{counter}@{domain}"
                    )

                    while Partner.search_count([
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

                    while Partner.search_count([
                        ('email', '=ilike', email)
                    ]):

                        counter += 1

                        email = (
                            f"copia{counter}@abc.com"
                        )

                    vals['email'] = email

        # =========================================================
        # CREAR USUARIO
        # =========================================================

        return super().create(vals_list)

    # =========================================================
    # COPIAR USUARIO
    # =========================================================

    def copy(self, default=None):

        self.ensure_one()

        default = dict(default or {})

        # ---------------------------------------------------------
        # Pasamos información del usuario original
        # para que res.partner genere los valores de COPIA.
        #
        # IMPORTANTE:
        # from_user_copy evita que create() ejecute la lógica
        # de CreaUser.
        # ---------------------------------------------------------

        return super(
            ResUsers,
            self.with_context(
                from_user_copy=True,
                original_partner_id=self.partner_id.id,
            )
        ).copy(default=default)