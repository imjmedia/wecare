/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import {KsDashboardNinja} from "@ks_dashboard_ninja/js/ks_dashboard_ninja_new";
import { _t } from "@web/core/l10n/translation";
import {ks_carousel} from "@ks_dn_advance/js/carousel";

patch(KsDashboardNinja.prototype,{
        ks_dash_print(id){
            var self = this;
            var ks_dashboard_name = self.ks_dashboard_data.name
            setTimeout(function () {
            window.scrollTo(0, 0);
            html2canvas(document.querySelector('.ks_dashboard_item_content'), {useCORS: true, allowTaint: false}).then(function(canvas){
            window.jsPDF = window.jspdf.jsPDF;
            var pdf = new jsPDF("p", "mm", "a4");
            var ks_img = canvas.toDataURL("image/jpeg", 0.90);
            var ks_props= pdf.getImageProperties(ks_img);
            var KspageHeight = 300;
            var KspageWidth = pdf.internal.pageSize.getWidth();
            var ksheight = (ks_props.height * KspageWidth) / ks_props.width;
            var ksheightLeft = ksheight;
            var position = 0;

            pdf.addImage(ks_img,'JPEG', 0, 0, KspageWidth, ksheight, 'FAST');
            ksheightLeft -= KspageHeight;
            while (ksheightLeft >= 0) {
                position = ksheightLeft - ksheight;
                pdf.addPage();
                pdf.addImage(ks_img, 'JPEG', 0, position,  KspageWidth, ksheight, 'FAST');
                ksheightLeft -= KspageHeight;
            };
            pdf.save(ks_dashboard_name + '.pdf');
        })
        },500);
        },

        ks_send_mail(ev) {
            var self = this;
            var ks_dashboard_name = self.ks_dashboard_data.name
            setTimeout(function () {
            $('.fa-envelope').addClass('d-none')
            $('.fa-spinner').removeClass('d-none');


            window.scrollTo(0, 0);
            html2canvas(document.querySelector('.ks_dashboard_item_content'), {useCORS: true, allowTaint: false}).then(function(canvas){
            window.jsPDF = window.jspdf.jsPDF;
            var pdf = new jsPDF("p", "mm", "a4");
            var ks_img = canvas.toDataURL("image/jpeg", 0.90);
            var ks_props= pdf.getImageProperties(ks_img);
            var KspageHeight = 300;
            var KspageWidth = pdf.internal.pageSize.getWidth();
            var ksheight = (ks_props.height * KspageWidth) / ks_props.width;
            var ksheightLeft = ksheight;
            var position = 0;

            pdf.addImage(ks_img,'JPEG', 0, 0, KspageWidth, ksheight, 'FAST');
            ksheightLeft -= KspageHeight;
            while (ksheightLeft >= 0) {
                position = ksheightLeft - ksheight;
                pdf.addPage();
                pdf.addImage(ks_img, 'JPEG', 0, position,  KspageWidth, ksheight, 'FAST');
                ksheightLeft -= KspageHeight;
            };
//            pdf.save(ks_dashboard_name + '.pdf');
            const file = pdf.output()
            const base64String = btoa(file)

//            localStorage.setItem(ks_dashboard_name + '.pdf',file);

            $.when(base64String).then(function(){
                self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_dashboard_send_mail",{
                    model: 'ks_dashboard_ninja.board',
                    method: 'ks_dashboard_send_mail',
                    args: [
                        [parseInt(self.ks_dashboard_id)],base64String

                    ],

                    kwargs:{}
                }).then(function(res){
                    $('.fa-envelope').removeClass('d-none')
                    $('.fa-spinner').addClass('d-none');
                    if (res['ks_is_send']){
                        var msg = res['ks_massage']
                            self.notification.add(_t(msg),{
                                title:_t("Success"),
                                type: 'info',
                            });

                    }else{
                        var msg = res['ks_massage']
                        self.notification.add(_t(msg),{
                                title:_t("Fail"),
                                type: 'warning',
                            });

                    }
                });
             })
        })
        },500);

        },

        startTvDashboard(e){
            var self = this;
            this.dialogService.add(ks_carousel,{
                items : Object.values(self.ks_dashboard_data.ks_item_data),
                dashboard_data : self.ks_dashboard_data,
                ksdatefilter:'none',
                pre_defined_filter : {},
                custom_filter:{}
            },{
                   onClose: () => {},
                }
            );
        },





});

