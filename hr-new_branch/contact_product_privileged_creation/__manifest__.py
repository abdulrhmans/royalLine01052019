# -*- coding: utf-8 -*-
{
    'name': "SW - Contacts & Products Privilege Groups",
    'summary': """
        This module creates two new groups, "Allow Create Products" and "Allow Create Contacts" """,
    'description': """
        The two groups this module installs anc creates. removes and overwrites the pre existing Access Rights for the Odoo source code. Instead it implements our groups into the Access RIghts system. Which means that if this is to be reversed then there are two possible solutions:
            1- Manual database changes and editing for the product.product and product.template to return it to the default.
            2- To update the Inventory APP, which causes various other problems.""",
    'author': "Smart Way Business Solutions",
    'website': "https://www.smartway-jo.com",
    'category': 'Extra Tools',
    'version': '11.0.1.0',
    'depends': ['base', 'contacts', 'product', 'purchase', 'sale'],
    'data': [
        'views/allow_create_product_view.xml',
        'security/groups_privileges.xml',
        'security/ir.model.access.csv',
        'views/allow_create_contact_view.xml']
}
