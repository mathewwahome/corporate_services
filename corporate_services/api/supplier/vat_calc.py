import frappe
from frappe.utils import flt
from frappe import _

def calc(doc, method):
    total_price = 0
    for item in doc.items:
        units = flt(item.units)
        item_price = flt(item.price) * units
        total_price += item_price
    
    doc.total_amount = total_price
    
    vat_rate = doc.vat_rate
    if doc.total_amount is None or vat_rate is None:
        frappe.throw(_("Total Amount or VAT Rate is missing."))
    
    if doc.vat_type == "Inclusive of VAT":
        vat = total_price - (total_price / (1 + (vat_rate / 100)))
        grand_total = total_price
        doc.vat_amount = vat
    elif doc.vat_type == "Exclusive of VAT":
        vat = total_price * vat_rate / 100
        grand_total = total_price + vat
        doc.vat_amount = vat
    else:
        frappe.throw(_("Invalid VAT type."))
        
    doc.grand_total = grand_total

