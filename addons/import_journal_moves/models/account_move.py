from odoo import _, api, fields, models


MOVIMIENTOS = [('entry','Entrada'),('in_invoice','Factura Proveedor'),('in_refund','Nota 1'),('out_invoice','Factura Cliente'),('out_refund','Nota 2')]
PAYMENT_STATE = [('paid','Pagado'),('not_paid','no pagado'),('revewrsed','reversado')]
MOVEID = [
        ('anticipo_clientes', 'ANTICIPO DE CLIENTES'),
        ('salario', 'Salario'),
        ('cruce_cuentas', 'Cruce de Cuentas'),
        ('banco_pichincha_cta_cte_2100203247', 'BANCO PICHINCHA CTA. CTE. # 2100203247'),
        ('cierre_ejercicio_fiscal', 'CIERRE EJERCICIO FISCAL'),
        ('efectivo', 'Efectivo'),
        ('liquidar_clientes_adjudicado', 'LIQUIDAR CLIENTES ADJUDICADO'),
        ('employee_liability', 'Employee Liability'),
        ('otros_movimientos', 'Otros Movimientos'),
        ('caja_general_principal', 'CAJA GENERAL PRINCIPAL'),
        ('rodrigo_galarza', 'RODRIGO GALARZA'),
        ('deposito_no_identificado', 'DEPOSITO NO IDENTIFICADO'),
        ('facturas_clientes', 'Facturas de Clientes'),
        ('retenciones_proveedores', 'Retenciones de Proveedores'),
        ('retenciones_iva_proveedor', 'Retenciones de IVA Proveedor'),
        ('fondo_clientes', 'FONDO DE CLIENTES'),
        ('notas_credito_clientes', 'Notas de Crédito de Clientes'),
        ('inventario', 'Inventario'),
        ('retenciones_fuente_clientes', 'Retenciones en la Fuente Clientes'),
        ('rafael_herrera', 'RAFAEL HERRERA'),
        ('amazonas_cta_cte_3501082022', 'AMAZONAS CTA. CTE. #3501082022'),
        ('facturas_proveedores', 'Facturas de Proveedores'),
        ('liquidacion_planes', 'LIQUIDACION DE PLANES'),
        ('cobros_tarjeta_credito', 'Cobros con Tarjeta de Crédito'),
        ('anticipo_mosinvest', 'ANTICIPO A MOSINVEST'),
        ('otros_activos_regularizar', 'OTROS ACTIVOS POR REGULARIZAR'),
        ('valoracion_inventario', 'Valoración del inventario'),
        ('tarjeta_credito', 'Tarjeta Credito'),
        ('cuentas_cobrar_stone_sa', 'CUENTAS POR COBRAR STONE S.A.'),
        ('cuentas_pagar_mosinvest', 'CUENTAS POR PAGAR MOSINVEST'),
        ('notas_debito_proveedores', 'Notas de Débito de Proveedores'),
        ('banco_pichincha_ahorro_2206934551', 'BANCO DEL PICHINCHA CTA AHORRO # 2206934551'),
        ('retenciones_iva_clientes', 'Retenciones de IVA Clientes'),
        ('diario_anticipos_proveedores', 'Diario de Anticipos de Proveedores'),
        ('deposito_por_aplicar', 'DEPOSITO POR APLICAR'),
        ('notas_credito_proveedores', 'Notas de Crédito de Proveedores'),
        ('no_deducible', 'NO DEDUCIBLE'),
        ('traspaso_mosinvest', 'TRASPASO A MOSINVEST'),
        ('cuentas_cobrar_mosinvest', 'CUENTAS POR COBRAR MOSINVEST'),
        ('gastos', 'Gastos'),
        ('planes_superior', 'PLANES SUPERIOR'),
        ('liquidar_clientes_adjudicado_otros', 'LIQUIDAR CLIENTES ADJUDICADO OTROS'),
        ('asiento_apertura', 'ASIENTO DE APERTURA'),
        ('banco_pichincha_ahorro_futuro_2206934719', 'BANCO DEL PICHINCHA AHORRO FUTURO # 2206934719'),
        ('liquidacion_compras', 'Liquidación de Compras'),
        ('datafast_mosinvest', 'DATAFAST MOSINVEST'),
        ('descuento_comisiones', 'DESCUENTO COMISIONES'),
        ('nota_venta_proveedores', 'Nota de Venta de Proveedores'),
        ('notas_debito_clientes', 'Notas de Débito de Clientes'),
        ('cuenta_cobrar_galarcorp_sa', 'CUENTA POR COBRAR GALARCORP S.A.'),
        ('activo_fijo', 'ACTIVO FIJO'),
        ('banco_pichincha_ahorro_futuro_2205255971', 'BANCO DEL PICHINCHA AHORRO FUTURO # 2205255971'),
        ('ventas_migradas', 'Ventas Migradas'),
        ('simon_motors', 'SIMON MOTORS'),
        ('ingresos_migrados', 'Ingresos Migrados'),
        ('anticipo_comisiones', 'Anticipo de Comisiones'),
        ('costos', 'COSTOS'),
        ('banco_amazonas_ahorro_4502368791', 'BANCO AMAZONAS CTA AHORRO # 4502368791'),
        ('adriana_arevalo', 'ADRIANA AREVALO'),
        ('devolucion_clientes', 'DEVOLUCION CLIENTES'),
        ('caja_portoviejo', 'CAJA PORTOVIEJO'),
        ('caja_chica_palmora', 'CAJA CHICA PALMORA'),
        ('notas_debito_interna_proveedores', 'Notas de Débito Interna de Proveedores'),
        ('caja_chica', 'CAJA CHICA'),
        ('recibos_perdidos', 'RECIBOS PERDIDOS'),
        ('cxp_prestamos_terceros', 'CxP Prestamos Terceros'),
        ('karol_vera', 'KAROL VERA'),
        ('ricardo_hurtado', 'RICARDO HURTADO'),
        ('pablo_torres', 'PABLO TORRES'),
        ('banco_pichincha_ahorro_2206535947', 'BANCO DEL PICHINCHA CTA AHORRO # 2206535947'),
        ('diario_anticipos_clientes', 'Diario de Anticipos de Clientes'),
        ('prestamo_mosinvest', 'PRESTAMO MOSINVEST'),
        ('banco_machala_ahorros', 'Banco Machala Ahorros'),
        ('anticipo_starmotors_sa', 'ANTICIPO A STARMOTORS S.A.'),
    ]

MOVEIDM=[
            ('coop_ahorro', 'Cooperativa de ahorro y Cred. JEP'),
            ('inventario', 'Inventario'),
            ('bco_guayaquil', 'Bco. Guayaquil #002851715-7'),
            ('cruce_accionistas', 'CRUCE ACCIONISTAS'),
            ('pichincha_ahorro', 'Pichincha ahorro 2209683931'),
            ('bco_capital_cte', 'Bco. Capital cte. #090600025-39'),
            ('cruce_anticipos_nopina', 'Cruce Anticipos Nopiña'),
            ('bco_amazonas_ahorros', 'Banco Amazonas Cta Ahorros#4502414050'),
            ('bco_pichincha', 'Bco. Pichincha #21002006-10'),
            ('bco_bolivariano', 'Banco Bolivariano'),
            ('cobros_tarjeta_credito', 'Cobros con Tarjeta de Crédito'),
            ('cruce_cuentas', 'Cruce de Cuentas'),
            ('efectivo', 'EFECTIVO'),
            ('retenciones_proveedores', 'Retenciones de Proveedores'),
            ('salario', 'Salario'),
            ('bco_amazonas_cta_cte', 'Banco Amazonas 35-0107338-4 Cta Cte'),
            ('retenciones_clientes', 'Retenciones en la Fuente Clientes'),
            ('bco_ruminahui_ahorros', 'Banco Rumiñahui Cta Ahorros #8633356900'),
            ('bco_austro', 'Banco del Austro 00-09-44518-8'),
            ('veh_usados', 'VEH USADOS'),
            ('bco_amazonas_trust', 'Banco Amazonas Trust #3501079463'),
            ('bco_comercial_manabi', 'Banco Comercial de Manabi Cta Cte #206243990'),
            ('provisiones', 'PROVISIONES'),
            ('anticipo_cliente', 'Anticipo de Cliente'),
            ('retenciones_iva_clientes', 'Retenciones IVA Clientes'),
            ('reversion_anticipos', 'REVERSION DE ANT.PROVEEDORES'),
            ('bco_machala', 'Banco de Machala 107099272-4'),
            ('anticipo_galarplan', 'ANTICIPO GALARPLAN'),
            ('cruce_galarplan', 'CRUCE GALARPLAN'),
            ('facturas_proveedores', 'Facturas de Proveedores'),
            ('otros_movimientos', 'Otros Movimientos'),
            ('bco_capital_ahorros', 'Banco Capital Cta. Ahorros # 0901002462'),
            ('bco_amazonas_ahorros2', 'Banco Amazonas 4502364656 Cta Ahorros'),
            ('tarjeta_credito', 'Tarjeta Credito'),
            ('saldo_inicial_2022', 'SALDO INICIAL 2022'),
            ('impositivo', 'Impositivo'),
            ('facturas_clientes', 'Facturas de Clientes'),
            ('a_pagar_accionista_rg', 'A PAGAR ACCIONISTA RG'),
            ('retencion_iva_proveedor', 'Retención IVA Proveedor'),
            ('anticipo_proveedores', 'Anticipo de Proveedores'),
            ('act_por_amortizar_gao', 'ACT. POR AMORTIZAR GAO'),
            ('notas_credito_clientes', 'Notas de Crédito de Clientes'),
            ('bco_amazonas_cta_cte2', 'Banco Amazonas 3501085790 Cta Cte'),
            ('cuentas_por_liquidar', 'Cuentas por Liquidar'),
            ('pago_sueldos', 'Pago de Sueldos'),
            ('cruce_dep_no_identificados', 'CRUCE DEP. NO IDENTIFICADOS'),
            ('bco_loja', 'Banco de Loja'),
            ('por_cobrar_galarcorp', 'POR COBRAR GALARCORP'),
            ('anticipo_comisiones', 'Anticipo de Comisiones'),
            ('notas_credito_proveedores', 'Notas de Crédito de Proveedores'),
            ('prestamos_empleados', 'Prestamos empleados'),
            ('liquidacion_compras', 'Liquidación de Compras'),
            ('cierre_ejercicio_fiscal', 'CIERRE EJERCICIO FISCAL'),
            ('por_pagar_simonmotors', 'POR PAGAR SIMONMOTORS'),
            ('galarplan_por_pagar', 'GALARPLAN POR PAGAR'),
            ('cheques_protestados', 'CHEQUES PROTESTADOS'),
            ('notas_debito_clientes', 'Notas de Débito de Clientes'),
            ('pago_tc_diners', 'PAGO CON TC DINERS'),
            ('por_cobrar_stone', 'POR COBRAR STONE'),
            ('caja_chica_babahoyo', 'Caja Chica Babahoyo'),
            ('cheques_diferidos', 'Cheques Diferidos'),
        ]
class AccountMove(models.Model):
    _inherit = 'account.move'

    id_old_database = fields.Integer(string='ID straconx')

    old_move_type = fields.Selection(MOVIMIENTOS,string='Movimiento straconx')

    old_payment_state = fields.Selection(PAYMENT_STATE,string='pago straconx')

    old_journal_id = fields.Selection(MOVEID,string='Diario Antiguo')

    old_journal_id_m = fields.Selection(MOVEIDM,string='Diario Antiguo Mosinvest')

    migrate_move = fields.Boolean(string='Migrado')

    partner_find = fields.Char(string='cliente fue migrado?')



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    id_old_move = fields.Integer(string='ID straconx')

    id_old_move_id = fields.Integer(string='ID move straconx')

    migrated_move_line = fields.Boolean(string='Migrado')

    old_journal_id = fields.Selection(MOVEID,string='Diario Antiguo')

    old_journal_id_m = fields.Selection(MOVEIDM,string='Diario Antiguo Mosinvest')

    old_payment_state = fields.Selection(PAYMENT_STATE,string='pago straconx')

    partner_find = fields.Char(string='cliente migrado')
