# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
	_inherit = "account.payment"


	requested_amt = fields.Float('Requested Amount')
	approved_amt = fields.Float('Approved Amount')
	generated_from_proposal = fields.Boolean('Is Generated from Proposal', defalt=False)
	proposal_id = fields.Many2one('payment.proposal', 'Proposal')
	proposal_state = fields.Selection(related='proposal_id.state', string='Proposal Status', store=True)	
	state = fields.Selection(selection_add=[('approve', 'Approved'),('decline', 'Declined')])

	@api.onchange('amount', 'currency_id')
	def _onchange_amount(self):
		res = super(AccountPayment, self)._onchange_amount()
		if self.generated_from_proposal == True:
			self.journal_id = False
		return res

	def action_approve(self):
		for line in self:
			if line.approved_amt <= 0.0:
				raise UserError(_("Approved Amount should be greater than Zero."))
			if line.approved_amt > line.requested_amt:
				raise UserError(_("Approved Amount should not be greater than the Requested Amount."))
			line.write({'state':'approve', 'amount':line.approved_amt})

	def action_decline(self):
		for line in self:
			line.write({'state':'decline'})
