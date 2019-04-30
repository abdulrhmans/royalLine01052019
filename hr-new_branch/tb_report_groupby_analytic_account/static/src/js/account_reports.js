odoo.define('tb_report_groupby_analytic_account.account_report', function (require) {
    'use strict';

    var AccountReportWidget = require('account_reports.account_report');

    AccountReportWidget.include({

        render_searchview_buttons: function() {
            var self = this;
            this._super.apply(this, arguments);

            if (self.report_options.analytic) {
                self.$searchview_buttons.find('[data-filter="analytic_table_separate"]').prop("checked", self.report_options.analytic_table_separate);
            }

            this.$searchview_buttons.find('.js_account_reports_analytic_separate').on('click', function(){
                self.report_options.analytic_table_separate = self.$searchview_buttons.find('[data-filter="analytic_table_separate"]').is(':checked');
                return self.reload().then(function(){
                    self.$searchview_buttons.find('.account_analytic_filter').click();
                })
            });
        },
    });
});
