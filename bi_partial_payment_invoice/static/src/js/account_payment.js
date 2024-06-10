odoo.define('bi_partial_payment_invoice.account_payment', function (require) {
"use strict";

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var field_utils = require('web.field_utils');
    var payment = require('account.payment');
    var QWeb = core.qweb;
    var _t = core._t;

    var ShowPaymentLineWidget = payment.ShowPaymentLineWidget;


    ShowPaymentLineWidget.include({

        init: function() {
            var self = this;
            this._super.apply(this, arguments);
        },

        start: function () {
            var self = this;
            return this._super();
        },

        _onOutstandingCreditAssign: function (event) {
                event.stopPropagation();
                event.preventDefault();
                var self = this;
                var id = $(event.target).data('id') || false;
                var value = JSON.parse(this.value);
                this._rpc({
                    model: 'ir.model.data',
                    method: 'xmlid_to_res_model_res_id',
                    args: ["bi_partial_payment_invoice.account_payment_wizard_form"],
                }).then(function (data) {
                    self.do_action({
                        name: _t('Payment Wizard'),
                        type: 'ir.actions.act_window',
                        view_mode: 'form',
                        res_model: 'account.payment.wizard',
                        context: {
                            payment_value : value,
                            line_id : id
                        },
                        views: [[data[1], 'form']],
                        target : 'new'
                    });
                });
            },

        _onRemoveMoveReconcile: function (event) {
            var self = this;
            var paymentId = parseInt($(event.target).attr('payment-id'));

            if (paymentId !== undefined && !isNaN(paymentId)){
                this._rpc({
                    model: 'account.move.line',
                    method: 'remove_move_reconcile',
                    args: [paymentId],
                    context: {'move_id': this.res_id,'from_js':true},
                }).then(function () {
                    self.trigger_up('reload');
                });
            }
        },
    });

});