
from pos_app.settings_store import get_active_profile

class EscPosPrinter:
    def __init__(self):
        prof = get_active_profile()
        esc = prof.get("escpos", {})
        self.mode = esc.get("mode","network")
        self.host = esc.get("host","192.168.1.50")
        self.port = int(esc.get("port",9100))
        self.usb_vid = int(esc.get("usb_vid",0))
        self.usb_pid = int(esc.get("usb_pid",0))
        self._impl = None
        try:
            if self.mode == "network":
                from escpos.printer import Network
                self._impl = Network(self.host, self.port)
            elif self.mode == "usb" and self.usb_vid and self.usb_pid:
                from escpos.printer import Usb
                self._impl = Usb(self.usb_vid, self.usb_pid)
        except Exception:
            self._impl = None

    def print_text(self, text: str):
        if self._impl is None:
            print("[ESC/POS fallback]", text)
            return
        try:
            self._impl.text(text + "\n")
            self._impl.cut()
        except Exception as e:
            print("[ESC/POS error]", e)
            print(text)

    def print_receipt(self, sale, session):
        # simple formatter
        lines = ["==== RECEIPT ===="]
        when = getattr(sale, "datetime", None)
        lines.append(f"Date: {when.strftime('%Y-%m-%d %H:%M:%S') if when else ''}")
        lines.append("Items:")
        for l in sale.lines:
            name = l.product.name if getattr(l, "product", None) else f"#{l.product_id}"
            lines.append(f"  {l.qty:.0f} x {name:<20} {l.unit_price:>7.2f}")
        lines += ["-----------------", f"Subtotal: {sale.subtotal:>9.2f}", f"Tax:      {sale.tax_total:>9.2f}", f"Total:    {sale.grand_total:>9.2f}", "================="]
        self.print_text("\n".join(lines))

    def test_page(self):
        self.print_text("POS App Test Page\n\n*** Printer OK ***")
