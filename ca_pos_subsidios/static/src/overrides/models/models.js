/** @odoo-module **/

import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
//import { Component } from "@odoo/owl";
import { Component, useState, useSubEnv, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(Order.prototype, {

    setup() {
        super.setup(...arguments);
    },

    async set_partner(partner) {
        var sin_productos =  this.is_empty();
        if (sin_productos && partner){
            return ;
        }

        /*SUPER PARA QUE NOS RETORNE EL USUARIO EN TIEMPO REAL */
        super.set_partner(partner);

        var partner_subsidio = false
        //var subsidio_product = this.pos.db.get_product_by_id(this.pos.config.producto_factura_id[0]);
        /*OBTENEMOS LAS LINEAS DE LA ORDEN*/
        var lines = this.get_orderlines();
        var subsidio_product = false;

        if(partner){
            var partner_pos = this.pos.db.get_partner_by_id(partner.id);
            if(partner_pos && partner_pos.subsidiaria_partner_id){
                partner_subsidio =  this.pos.db.get_partner_by_id(partner.subsidiaria_partner_id[0]); 

                if (!partner_subsidio){
                    await this.pos._loadPartners([partner.subsidiaria_partner_id[0]]);
                    partner_subsidio = this.pos.db.get_partner_by_id(partner.subsidiaria_partner_id[0]); 
                }

                subsidio_product = this.pos.db.get_product_by_id(partner_subsidio.producto_factura_id[0]);

                //product.product
                //partner = self.env['res.partner'].search([("id", "=", self.partner_id.id)] )
                /*var count_subsidios = await this.env.services.orm.call(
                "subsidios", 
                "get_count_subsidios_por_cliente_fecha", 
                [partner.id, order.date_order] );*/

                /*var prd_subsidio = await this.env.services.orm.call(
                "product.product", 
                "search", 
                ["id", "=", partner_subsidio.producto_factura_id[0]] );
                */

                //var subsidio_product = this.pos.db.get_product_by_id(partner_subsidio.producto_factura_id[0]);
                /*
                if prd_subsidio{
                    subsidio_product = this.pos.db.get_product_by_id(prd_subsidio.product_tmpl_id);
                }
                
                if (!subsidio_product){
                    //await this._getOrdersJson()
                    const ordersJson = await this.pos._getOrdersJson();
                    await this.pos._getMissingProducts(ordersJson);
                    //await this.pos._loadProductProduct([partner_subsidio.producto_factura_id[0]]);
                    subsidio_product = this.pos.db.get_product_by_id(partner_subsidio.producto_factura_id[0]);
                }*/
            }
        }
        
        /*AL MOMENTO DE SELECCIONAR LA ORDEN TENEMOS EN THIS EL OBJETO ORDEN*/
        var order = this
        /*OBTENEMOS EL PRODUCTO A AGREGAR*/
        if(partner_subsidio){
            /*OBTENEMOS EL DESCUENTO*/
            const discount = partner_subsidio.porcentaje_subsidio

            /*OBTENEMOS EL TOTAL DE LA ORDEN*/
            const total = order.get_total_with_tax()
    
            /*AÑADIMOS EL PRODUCTO EN LA ORDEN*/
            var count_subsidios = await this.env.services.orm.call(
                "subsidios", 
                "get_count_subsidios_por_cliente_fecha", 
                [partner.id, order.date_order] );
            var max_subsidios = await this.env.services.orm.call(
                "res.partner", 
                "get_max_subsidios", 
                [partner.id] );

            //id (.producto.id)        producto (.producto)        precio total (.price)
            //var lines_dic = Object.fromEntries(data.map(lines => [x.id, x.country]));
            var lines_dic = order.export_as_JSON().lines;

            var subtotal_sub = await this.env.services.orm.call(
                "pos.order", 
                "get_total_subsidio", 
                [partner_subsidio, lines_dic] );

            if (subsidio_product && subtotal_sub != 0 && partner_subsidio && partner_subsidio.subsidio_activo && count_subsidios < max_subsidios ) {
                for (var i = 0; i < lines.length; i++) {
                    if (lines[i].get_product() === subsidio_product && total > 0) {
                        lines[i].set_unit_price(-((subtotal_sub - lines[i].get_price_with_tax()) * (discount / 100)));
                        lines[i].set_lst_price(-((subtotal_sub - lines[i].get_price_with_tax()) * (discount / 100)));
                        return
                    }
                }
                return order.add_product(subsidio_product, {
                    is_tip: true,
                    quantity: 1,
                    price: -(subtotal_sub * (discount / 100)),
                    lst_price: -(subtotal_sub * (discount / 100)),
                    extras: { price_type: "manual" },
                });
            }
            else {
                if (order.get_total_with_tax() >= 0){
                    for (var i = 0; i < lines.length; i++) {
                        if (lines[i].get_product() === subsidio_product) {
                            order.removeOrderline(lines[i])
                        }
                    }
                }
            }
        }
        else {
            for (var i = 0; i < lines.length; i++) {
                if (lines[i].get_product() === subsidio_product) {
                    order.removeOrderline(lines[i])
                }
            }
        }
    },

});
