from odoo.addons.l10n_ec.models.account_move import _DOCUMENTS_MAPPING


_DOCUMENTS_MAPPING.update({
    "01": _DOCUMENTS_MAPPING.get("01", []) + ['ec_dt_01N']
})