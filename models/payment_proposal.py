# -*- coding: utf-8 -*-

from odoo import models, fields, api

class payment_proposal(models.Model):
    _name = 'payment.proposal'

    READONLY_STATES = {
        'submit': [('readonly', True)],
        'approve': [('readonly', True)],
        'paid': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    name = fields.Char('Name', readonly=True)
    date = fields.Date(required=True, states=READONLY_STATES, index=True, copy=False, default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', 'Responsible', states=READONLY_STATES, default=lambda self: self.env.user)
    approved_user_id = fields.Many2one('res.users', 'Approved User', states=READONLY_STATES)
    approved_date = fields.Date('Approved Date', states=READONLY_STATES)
    line_ids = fields.One2many('payment.proposal.line', 'proposal_id', 'Lines')
    state = fields.Selection([('draft', 'New'), ('submit', 'Submitted'),
    						('approve', 'Approved'),('paid', 'Paid'),('cancel', 'Cancel')], string='Status', required=True, readonly=True, copy=False, default='draft')
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
class PaymentProposalLine(models.Model):
    _name = 'payment.proposal.line'

    partner_id = fields.Many2one('res.partner', 'Partner')
    requested_amt = fields.Float('Requested Amount')
    sanctioned_amt = fields.Float('Sanctioned Amount')
    state = fields.Selection([('draft', 'New'),('approve', 'Approved'),('reject', 'Rejected')], string='Status', required=True, readonly=True, copy=False, default='draft')
    proposal_id = fields.Many2one('payment.proposal', 'Proposal')