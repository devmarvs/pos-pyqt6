
import socket
import usb.core, usb.util
from pos_app.settings_store import get_active_profile

class ZebraPrinter:
    def __init__(self):
        prof = get_active_profile()
        self.cfg = prof.get("zebra", {"mode":"network","host":"192.168.1.51","port":9100,"usb_vid":0,"usb_pid":0})

    def _send_network(self, zpl: str):
        with socket.create_connection((self.cfg.get("host","127.0.0.1"), int(self.cfg.get("port",9100))), timeout=3) as s:
            s.sendall(zpl.encode("utf-8"))

    def _send_usb(self, zpl: str):
        vid = int(self.cfg.get("usb_vid",0)); pid = int(self.cfg.get("usb_pid",0))
        dev = usb.core.find(idVendor=vid, idProduct=pid)
        if dev is None:
            raise RuntimeError("USB Zebra not found")
        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
        except Exception:
            pass
        dev.set_configuration()
        cfg = dev.get_active_configuration()
        intf = cfg[(0,0)]
        ep_out = None
        for ep in intf:
            if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                ep_out = ep; break
        if ep_out is None:
            raise RuntimeError("No OUT endpoint on Zebra device")
        ep_out.write(zpl.encode("utf-8"))

    def print_zpl(self, zpl: str):
        mode = self.cfg.get("mode","network")
        try:
            if mode == "usb":
                self._send_usb(zpl)
            else:
                self._send_network(zpl)
        except Exception as e:
            print("[ZPL fallback]", e)
            print(zpl)

    def print_barcode_label(self, barcode: str, title: str = "", copies: int = 1):
        zpl = f"""
^XA
^PW600
^FO50,40^A0N,30,30^FD{title:^30}^FS
^FO50,90^BY2
^BCN,120,Y,N,N
^FD{barcode}^FS
^XZ
""" * max(1, int(copies))
        self.print_zpl(zpl)
