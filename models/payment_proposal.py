# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime

class PaymentProposal(models.Model):
	_name = 'payment.proposal'

	READONLY_STATES = {
		'submitted': [('readonly', True)],
		'approved': [('readonly', True)],
		'paid': [('readonly', True)],
		'cancel': [('readonly', True)],
	}

	name = fields.Char('Name', required=True, index=True, copy=False, default='New')
	date = fields.Date(required=True, states=READONLY_STATES, index=True, copy=False, default=fields.Date.context_today)
	user_id = fields.Many2one('res.users', 'Responsible', states=READONLY_STATES, default=lambda self: self.env.user)
	approved_user_id = fields.Many2one('res.users', 'Approved User', readonly=True)
	approved_date = fields.Date('Approved Date', readonly=True)
	line_ids = fields.One2many('payment.proposal.line', 'proposal_id', 'Lines')
	# payment_ids = fields.One2many('account.payment', 'proposal_id', 'Payment Lines')
	state = fields.Selection([('draft', 'New'), ('submitted', 'Submitted'),
							('approved', 'Approved'),('paid', 'Paid'),('cancelled', 'Cancelled')], string='Status', required=True, readonly=True, copy=False, default='draft')
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)

	@api.model
	def create(self, vals):
		if vals.get('name', 'New') == 'New':
			seq_date = None
			if 'date' in vals:
				seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date']))
			vals['name'] = self.env['ir.sequence'].next_by_code('payment.proposal', sequence_date=seq_date) or '/'
		return super(PaymentProposal, self).create(vals)


	def action_submit(self):
		for proposal in self:
			proposal.write({'state':'submitted'})

	def action_approve(self):
		for proposal in self:
			for line in proposal.line_ids:
				if line.state not in ['approved','declined']:
					raise UserError(_("Every line should be Approved or Rejected."))

			proposal.write({'state':'approved','approved_user_id':self.env.user.id,'approved_date':datetime.datetime.now().date()})

	def action_cancel(self):
		for proposal in self:
			proposal.write({'state':'cancelled'})
			


class PaymentProposalLine(models.Model):
	_name = 'payment.proposal.line'

	READONLY_STATES = {
		'approved': [('readonly', True)],
		'declined': [('readonly', True)],
		'posted': [('readonly', True)],
		'reconciled': [('readonly', True)],
		'cancelled': [('readonly', True)],
	}

	partner_id = fields.Many2one('res.partner', 'Partner', required=True, states=READONLY_STATES)
	requested_amt = fields.Float('Requested Amount',required=True, states=READONLY_STATES)
	approved_amt = fields.Float('Approved Amount')
	state = fields.Selection([('draft', 'New'),('approved', 'Approved'),('declined', 'Declined'),
		('posted', 'Paid'),('reconciled', 'Reconciled'),('cancelled', 'Cancelled')],string='Status', required=True, readonly=True, copy=False, default='draft')
	proposal_id = fields.Many2one('payment.proposal', 'Proposal')
	journal_id = fields.Many2one('account.journal', required=True, string='Journal', domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]")

	proposal_state = fields.Selection(related='proposal_id.state', string='Proposal Status', store=True)	
	company_id = fields.Many2one(related='proposal_id.company_id', string='Company', store=True)
	transaction_reference = fields.Char('Transaction Reference', states=READONLY_STATES)		
	communication = fields.Char(string='Memo', states=READONLY_STATES)
	payment_id = fields.Many2one('account.payment', 'Payment')
	

	def action_approve(self):
		for line in self:
			if line.approved_amt <= 0.0:
				raise UserError(_("Approved Amount should be greater than Zero."))
			if line.approved_amt > line.requested_amt:
				raise UserError(_("Approved Amount should not be greater than the Requested Amount."))
			line.write({'state':'approved'})

	def action_decline(self):
		for line in self:
			line.write({'state':'declined'})

	
	def action_paid(self):
		for line in self:
			if not line.transaction_reference:
				raise UserError(_("Please enter Transaction Reference."))
			payment_methods = self.journal_id.outbound_payment_method_ids
			payment_method_id = payment_methods and payment_methods[0] or False
			values = {
				'payment_type':'outbound',
				'partner_type':'supplier',
				'partner_id':line.partner_id.id,
				'company_id':line.company_id.id,
				'amount':line.approved_amt,
				'communication':line.communication,
				'journal_id':line.journal_id.id,
				'payment_method_id':payment_method_id.id,
				'generated_from_proposal':True,
			}
			payment = self.env['account.payment'].create(values)
			line.write({'payment_id':payment.id})
			payment.post()





class AccountPayment(models.Model):
	_inherit = "account.payment"

	generated_from_proposal = fields.Boolean('Is Generated from Proposal', defalt=False)


	def write(self, vals):
		if self.generated_from_proposal == True:
			proposal = self.env['payment.proposal.line'].search([('payment_id','=',self.id)], limit=1)
			if vals.get('state') == 'posted':
				proposal.write({'state':'posted'})
			if vals.get('state') == 'reconciled':
				proposal.write({'state':'reconciled'})
			if vals.get('state') == 'cancelled':
				proposal.write({'state':'cancelled'})
			if vals.get('state') == 'draft':
				proposal.write({'state':'draft'})
		res = super(AccountPayment, self).write(vals)
		return res
