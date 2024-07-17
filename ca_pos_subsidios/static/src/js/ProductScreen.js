/** @odoo-module **/
import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { Numpad } from "@point_of_sale/app/generic_components/numpad/numpad";
import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { useService } from "@web/core/utils/hooks";
import { _lt, _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

/*
    Prohibir modificaciones de la linea del producto-subsidio en pantalla de productos

    1. heredar el metodo updateSelectedOrderline
    2. En el nuevo validar primero si el producto es producto-subsidio
    3. si lo es, retornar de la funcion
    4. si no lo es llamar a super(),updateSelectedOrderline()

    Para verificar si es el producto-subsidio
    const order = this.pos.get_order();

    var partner_pos = this.pos.db.get_partner_by_id(partner.id);
    partner_subsidio =  this.pos.db.get_partner_by_id(partner_subsidio.subsidiaria_partner_id[0]);   
    var subsidio_product = this.pos.db.get_product_by_id(partner_subsidio.producto_factura_id[0]);

    ----
    Ver simplified_pos, pos_takeaway

*/

ProductScreen.components = {
 ...ProductScreen.components,
        Numpad,
        PaymentScreenPaymentLines,
        PaymentScreenStatus,
        ProductsWidget,
        Orderline,
        OrderWidget,
 };

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        //this.pos.get_order().set_to_invoice(true);
    },

    async updateSelectedOrderline({ buffer, key }) {
        const order = this.pos.get_order();
        const selectedLine = order.get_selected_orderline();
        const partner = this.currentOrder.get_partner();
        var partner_subsidio = false;
        var subsidio_product = false;
        var partner_pos = false;

        /*if(partner){
            partner_pos = this.pos.db.get_partner_by_id(partner.id);
        }
        if (partner_pos && partner_pos.subsidiaria_partner_id){
            partner_subsidio =  this.pos.db.get_partner_by_id(partner_pos.subsidiaria_partner_id[0]);
            if (partner_subsidio){}
                subsidio_product = this.pos.db.get_product_by_id(partner_subsidio.producto_factura_id[0]);

                if (subsidio_product && subsidio_product === selectedLine.product && !_isRefundOrder){
                    return ;
                }
            }*/

        super.updateSelectedOrderline({ buffer, key });
        },


});
