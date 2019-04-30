# -*- coding: utf-8 -*-

from odoo import models, fields, api
import random,names,time
import odoo.service.db as DB

from odoo.http import request, route



class SaleOrder(models.Model):
	_inherit= 'sale.order'
	
	id_id = fields.Integer('ID')
	
class PurchaseOrder(models.Model):
	_inherit= 'purchase.order'
	
	id_id = fields.Integer('ID')

		
		
class RpcTest(models.TransientModel):
	_name = 'rpc.test'
	
	
	@api.model
	def create_so(self,id):
		cust_id = self.env['res.partner'].search([('customer','=',True)])[0]
		prod_ids = self.env['product.product'].search([])
		list_prod = []
		for i in prod_ids[:10]:
			list_prod.append((0,0,{'product_id': i.id,
							 'product_uom_qty':3}))
		so = self.env['sale.order'].create({
			'partner_id': cust_id.id,
			'order_line': list_prod,
			'id_id':id})
		return True
	@api.model
	def confirm_so(self,id):
		so = self.env['sale.order'].search([('id_id','=',id),('state','=','draft')],limit=1)
		if so :
			so.action_confirm()
		return True
	@api.model
	def deliver_so(self,id):
		so = self.env['sale.order'].search([('id_id','=',id),('picking_ids','!=',False),('state','=','sale')],limit=1)
		if so:
			so.picking_ids[0].move_lines.write({'quantity_done':3})
			so.picking_ids[0].button_validate()
		return True
	@api.model
	def invoice_so(self,id):
		so = self.env['sale.order'].search([('id_id','=',id),('picking_ids.state','=','done'),('invoice_ids','=',False)],limit=1)
		if so:
			qq = self.env['sale.advance.payment.inv'].create({}).with_context(active_ids=so.id).create_invoices()
			so.invoice_ids[0].action_invoice_open()
			self.env['account.payment'].create({'partner_type':'customer','partner_id':so.partner_id.id,'journal_id':1,'amount':so.invoice_ids[0].amount_total,'payment_method_id':1,'payment_type':'inbound','invoice_ids':[(4,so.invoice_ids[0].id)]}).action_validate_invoice_payment()
		return True
	@api.model
	def create_po(self,id):
		supp_id = self.env['res.partner'].search([('supplier','=',True)])[0]
		prod_ids = self.env['product.product'].search([])
		list_prod = []
		for i in prod_ids[:10]:
			list_prod.append((0,0,{'product_id': i.id,
							 'product_qty':3,
							 'name':'name',
							 'date_planned':'2018-07-31 09:25:45',
							 'product_uom':1,
							 'price_unit':100}))
		po = self.env['purchase.order'].create({'id_id':id,'date_planned':'2018-07-31 09:25:45','partner_id': supp_id.id,'order_line': list_prod,})
		return True
	@api.model
	def confirm_po(self,id):
		po = self.env['purchase.order'].search([('id_id','=',id),('state','=','draft')],limit=1)
		if po :
			po.button_confirm()
		return True
	@api.model
	def receive_po(self,id):
		po = self.env['purchase.order'].search([('id_id','=',id),('picking_ids','!=',False),('state','=','purchase')],limit=1)
		if po:
			po.picking_ids[0].move_lines.write({'quantity_done':3})
			po.picking_ids[0].button_validate()
	
		return True 
	@api.model
	def inoice_po(self,id):
		po = self.env['purchase.order'].search([('id_id','=',id),('invoice_ids','=',False),('picking_ids.state','=','done')],limit=1)
		if po:
			ai = self.env['account.invoice'].create({'purchase_id':po.id,'partner_id':po.partner_id.id,'type': 'in_invoice', 'type': 'in_invoice'})
			ai.purchase_order_change()
			ai.action_invoice_open()
			self.env['account.payment'].create({'partner_type':'supplier','partner_id':po.partner_id.id,'journal_id':1,'amount':po.invoice_ids[0].amount_total,'payment_method_id':1,'payment_type':'outbound','invoice_ids':[(4,po.invoice_ids[0].id)]}).action_validate_invoice_payment()
		return True		
	@api.model
	def create_contact(self,number):
		cust_model = self.env['res.partner']
		type_of_partner = [{'customer':True},{'supplier':True},{'supplier':True,'customer':True}]
		for i in range(number):
			value = {'name':str(names.get_full_name())}
			value.update(random.choice(type_of_partner))
			cust_model.create(value)   
		return True
	@api.model
	def create_catg(self,number):
		catg_model = self.env['product.category']
		catg_model.create({'name':names.get_full_name()})
		for i in range(number):
			catg_ids = catg_model.search([]).ids
			catg_model.create({'name':names.get_full_name(),'parent_id':random.choice(catg_ids)})
		return True
	@api.model	
	def create_wh(self,number):
		wh_model =  self.env['stock.warehouse']
		for i in range(number):
			a= str('%.20f'%(float(time.time())))[14:]
			wh_model.create({'name':names.get_full_name(),'code':a})
		return True
	@api.model
	def create_loc(self,number):
		loc_model =self.env['stock.location']
		loc_ids = loc_model.search([]).ids
		for i in range(number):
			loc_model.create({'name':names.get_full_name(),'location_id':random.choice(loc_ids)})
		return True
	@api.model
	def create_product(self,number):
		cust_model = self.env['res.partner']
		supplier_ids = cust_model.search([('supplier','=',True)]).ids
		prod_model = self.env['product.product']
		for i in range(number):
			prod_model.create({'name':str(names.get_full_name()),'type':'product','route_ids':[(4,5)] ,'seller_ids':[(0,0,{'name':random.choice(supplier_ids),'price':100})]})
		return True
	
		
		   
		   