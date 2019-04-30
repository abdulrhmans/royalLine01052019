# -*- coding: utf-8 -*-
{
    'name': 'SW - Object Merger',
    'version': '11.0.1.0',
    'category': 'Extra Tools',
    'description': """
    This Module will give you the possibility to merge 2 or more objects:
    Example: You want to merge 2 partners, select the Partner to merge, then which one to keep.
    All SO, PO, Invoices, Pickings, products, etc. of selected partner will be add to the one to keep.""",
    'author': 'Smart Way Business Solutions',
    'website': 'https://www.smartway-jo.com',
    'depends': ['base'],
    'data': [
        "wizard/object_merger_view.xml",
        "res_config_view.xml",
    ],
    'installable': True,
    "active": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
