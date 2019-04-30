# -*- encoding: utf-8 -*-
{
    "name" : "SW - Contact Privileges By Tags",
    "summary": "Limit user access to contacts by adding contact tags",
    "version" : "11.0.1.0",
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    "category" : "Extra Tools",
    'license':  "Other proprietary",
    "depends" : ["base", "contacts", "account", "purchase", "sale"],
    "data" : [
              "view/res_users_view.xml",
              "security/partner_rule.xml",
            ],
    "images":  ['static/description/Image.png'],
    'uninstall_hook': "uninstall_hook",
    "price" : 75,
    "currency" :  "EUR",
    "installable": True,
    "application":False,
    "auto_install":False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: