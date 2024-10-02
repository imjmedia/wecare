{
    'name': 'Wecare Account Filter',
    'version': '17.0',
    'category': 'Accounting',
    'summary': 'Add fields to account invoice filter',
    'description': """
        This module adds Vendor (invoice_user_id), Fiscal Folio (l10n_mx_edi_cfdi_uuid),
        and Sales Team (team_id) fields to the account invoice filter.
    """,
    'depends': ['account', 'l10n_mx_edi'],
    'data': [
        'views/account_invoice_filter_view.xml',
    ],
    'installable': True,
    'application': False,
}
