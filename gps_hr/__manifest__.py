
{
    'name': 'Cambios en Nomina',
    'version': '1.0',
    'category': 'Se realiza  cambios de nomina',
    'description': """

    """,
    'author': "GPS",
    'website': '',
    'depends': [
         'talent_human','fx'
    ],
    'data': [        
        "security/ir.model.access.csv",

        "data/dynamic_function.xml",
        "data/hr_salary_rule_category.xml",
        "data/hr_salary_rule.xml",

        "security/ir_rule.xml",

        "wizard/hr_employee_movement_wizard.xml",
        "wizard/hr_payslip_employees.xml",

        "views/hr_salary_rule_category.xml",
        "views/hr_salary_rule.xml",
        "views/hr_payroll_structure.xml",
        "views/hr_employee_movement_line.xml",
        "views/hr_employee_movement.xml",

        "views/hr_employee.xml",

        "views/hr_payslip_run.xml",
        "views/hr_payslip.xml",

        "views/hr_contract_type.xml",

        "views/hr_payslip_move.xml",

        "views/ir_ui_menu.xml",
    ],
    'installable': True,
}
