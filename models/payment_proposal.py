# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime

class PaymentProposal(models.Model):
	_name = 'payment.proposal'

	READONLY_STATES = {
		'submit': [('readonly', True)],
		'approve': [('readonly', True)],
		'paid': [('readonly', True)],
		'cancel': [('readonly', True)],
	}

	name = fields.Char('Name', required=True, index=True, copy=False, default='New')
	date = fields.Date(required=True, states=READONLY_STATES, index=True, copy=False, default=fields.Date.context_today)
	user_id = fields.Many2one('res.users', 'Responsible', states=READONLY_STATES, default=lambda self: self.env.user)
	approved_user_id = fields.Many2one('res.users', 'Approved User', readonly=True)
	approved_date = fields.Date('Approved Date', readonly=True)
	# line_ids = fields.One2many('payment.proposal.line', 'proposal_id', 'Lines')
	payment_ids = fields.One2many('account.payment', 'proposal_id', 'Payment Lines')
	state = fields.Selection([('draft', 'New'), ('submit', 'Submitted'),
							('approve', 'Approved'),('paid', 'Paid'),('cancel', 'Cancel')], string='Status', required=True, readonly=True, copy=False, default='draft')
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
			proposal.write({'state':'submit'})

	def action_approve(self):
		for proposal in self:
			for line in proposal.payment_ids:
				if line.state not in ['approve','decline']:
					raise UserError(_("Every line should be Approved or Rejected."))

			proposal.write({'state':'approve','approved_user_id':self.env.user.id,'approved_date':datetime.datetime.now().date()})

	def action_cancel(self):
		for proposal in self:
			proposal.write({'state':'cancel'})
			


class PaymentProposalLine(models.Model):
	_name = 'payment.proposal.line'

# 	READONLY_STATES = {
# 		'approve': [('readonly', True)],
# 		'decline': [('readonly', True)],
# 	}

# 	partner_id = fields.Many2one('res.partner', 'Partner', required=True, states=READONLY_STATES)
# 	requested_amt = fields.Float('Requested Amount', required=True, states=READONLY_STATES)
# 	sanctioned_amt = fields.Float('Sanctioned Amount')
# 	state = fields.Selection([('draft', 'New'),('approve', 'Approved'),('decline', 'Declined')], string='Status', required=True, readonly=True, copy=False, default='draft')
# 	proposal_id = fields.Many2one('payment.proposal', 'Proposal')
# 	proposal_state = fields.Selection(related='proposal_id.state', string='Proposal Status', store=True)	

# 	def action_approve(self):
# 		for line in self:
# 			line.write({'state':'approve'})

# 	def action_decline(self):
# 		for line in self:
# 			line.write({'state':'decline'})