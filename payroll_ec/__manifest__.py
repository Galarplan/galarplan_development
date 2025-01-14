
{
    'name': 'Cambios en Nomina',
    'version': '1.0',
    'category': 'Se realiza  cambios de nomina',
    'description': """

    """,
    'author': "GPS",
    'website': '',
    'depends': [
         'talent_human','fx','hr_employee_relative','conf_reports','payroll','hr_holidays_attendance'
    ],
    'data': [        

        "security/ir_module_category.xml",
        "security/res_groups.xml",

        "security/ir.model.access.csv",

        "sql/CROSSTAB.sql",

        "data/dynamic_function.xml",
        "data/hr_salary_rule_category.xml",
        "data/hr_salary_rule.xml",

        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",

        "mail/mail_template.xml",


        "security/ir_rule.xml",

        "wizard/hr_employee_movement_wizard.xml",
        "wizard/hr_payslip_employees.xml",
        "wizard/hr_employee_payslip_reports_wizard.xml",

        "reports/hr_payslip.xml",
        "reports/ir_actions_report_xml.xml",

        "views/hr_leave_type.xml",
        "views/hr_salary_rule_category.xml",
        "views/hr_salary_rule.xml",
        "views/hr_payroll_structure.xml",
        "views/hr_employee_movement_line.xml",
        "views/hr_employee_movement.xml",

        "views/hr_mail_message.xml",
        "views/hr_employee.xml",

        "views/hr_payslip_run.xml",
        "views/hr_payslip.xml",
        "views/hr_payslip_input.xml",

        "views/hr_contract_type.xml",

        "views/hr_payslip_move.xml",

        "views/res_company.xml",

        "views/hr_contract.xml",

        "views/th_family_burden.xml",
        "views/hr_employee_relative.xml",

        "views/hr_employee_payment.xml",

        "views/hr_payroll_structure_type.xml",

        "views/ir_ui_menu.xml",
    ],
    'installable': True,
}
