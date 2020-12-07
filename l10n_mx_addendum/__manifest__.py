{
    "name": "L10N MX Addendum",
    "version": "13.0.0.1.0",
    "author": "HomebrewSoft",
    "website": "https://homebrewsoft.dev",
    "license": "LGPL-3",
    "depends": [
        "account",
        "sale",
    ],
    "data": [
        # security
        "security/ir.model.access.csv",  # TODO
        # data
        "data/addendum_city_fresko.xml",
        "data/account_move_addendum.xml",
        "data/account_move_addendum_field.xml",
        # reports
        # views
        "views/account_move_addendum_field_value.xml",
        "views/account_move_addendum_field.xml",
        "views/account_move_addendum_wizard.xml",
        "views/account_move_addendum.xml",
        "views/account_move.xml",
        "views/res_partner.xml",
    ],
}
