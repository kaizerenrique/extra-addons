/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { debounce } from "@web/core/utils/timing";
import { useService, useAutofocus } from "@web/core/utils/hooks";
import { useAsyncLockedMethod } from "@point_of_sale/app/utils/hooks";
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, onWillUnmount, useRef, useState } from "@odoo/owl";
import { PartnerListScreen } from "@point_of_sale/app/screens/partner_list/partner_list";


patch(PartnerListScreen.prototype, {
    setup() {
        super.setup();
    },

    get partners() {
        let res;
        if (this.state.query && this.state.query.trim() !== "") {
            if (this.state.query.length >= 4){
                const result = this.searchPartner();
            }
            res = this.pos.db.search_partner(this.state.query.trim());
        } else {
            res = this.pos.db.get_partners_sorted(1000);
        }
        res.sort(function (a, b) {
            return (a.name || "").localeCompare(b.name || "");
        });
        // the selected partner (if any) is displayed at the top of the list
        if (this.state.selectedPartner) {
            const indexOfSelectedPartner = res.findIndex(
                (partner) => partner.id === this.state.selectedPartner.id
            );
            if (indexOfSelectedPartner !== -1) {
                res.splice(indexOfSelectedPartner, 1);
            }
            res.unshift(this.state.selectedPartner);
        }
        return res;
    },

    async getNewPartners() {
        let domain = [];
        const limit = 30;
        if (this.state.query) {
            const search_fields = ["name", "parent_name", "phone_mobile_search", "email", "vat"];
            domain = [
                ...Array(search_fields.length - 1).fill('|'),
                ...search_fields.map(field => [field, "ilike", this.state.query + "%"])
            ];
        }
        // FIXME POSREF timeout
        const result = await this.orm.silent.call(
            "pos.session",
            "get_pos_ui_res_partner_by_params",
            [[odoo.pos_session_id], { domain, limit: limit, offset: this.state.currentOffset }]
        );
        return result;
    }
});
