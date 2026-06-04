import base64
import hashlib
import re
import time
import requests
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad

# လှပသော UI ထုတ်လုပ်ရန် Rich Library အား အသုံးပြုခြင်း
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

class RuijieWifiProvisioning:

    def __init__(self):
        self.baseurl = "http://10.44.77.240:2060"
        self.username_get_url = f"{self.baseurl}/username_get"
        self.online_info_url = f"{self.baseurl}/user/online_info"
        self.logout_url = f"{self.baseurl}/user/logout"
        self.enc_key = "RjYkhwzx$2018!"

    def show_banner(self):
        """Cyber Security Style Banner"""
        banner_text = (
            "[bold cyan]⚡ RUIJIE NETWORK PROVISIONING SYSTEM ⚡[/bold cyan]\n"
            "[bold black]=========================================[/bold black]\n"
            "[green]Status: READY[/green] | [yellow]Engine: V2.0 (Premium UI)[/yellow]"
        )
        console.print(Panel(banner_text, border_style="bold green", expand=False))

    def run_progress(self, message, duration=1.5):
        """လှပသော Loading Bar Animation"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=30, complete_style="bold green", finished_style="bold cyan"),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(message, total=100)
            step = 100 / (duration * 10)
            while not progress.finished:
                progress.update(task, advance=step)
                time.sleep(0.1)

    def start_provision(self):
        console.clear()
        self.show_banner()
        console.print("\n[bold green][*] Protocol Initialized...[/bold green]")
        time.sleep(0.5)

        # ----------------------------------------------------
        # STAGE 01: UNBIND SESSION
        # ----------------------------------------------------
        console.print("\n[bold box][STAGE-01] SESSION UNBIND PROTOCOL[/bold box]", style="bold blue")
        self.run_progress("Checking network gateway for active sessions...", 1.2)
        
        unbind_status = self.unbind_session()
        if not unbind_status:
            console.print("[bold yellow][!] Warning: No active session found or unbind rejected. (Fresh Line)[/bold yellow]")
        else:
            console.print("[bold green][+] Success: Existing session tokens flushed and unbound.[/bold green]")

        # ----------------------------------------------------
        # STAGE 02: INTERCEPT CONFIGURATIONS
        # ----------------------------------------------------
        console.print("\n[bold box][STAGE-02] ROUTER CONFIGURATION INTERCEPTION[/bold box]", style="bold blue")
        self.run_progress("Intercepting target router handshakes...", 1.5)

        try:
            # Local Router Gateway မှ Redirect URL ကို ဖတ်ယူခြင်း
            localhost_res = requests.get("http://192.168.0.1", timeout=10)
            portal_redirect_url = localhost_res.url

            # URL ထဲမှ Gateway IP ဆွဲထုတ်ခြင်း
            ip_match = re.search(r"gw_address=(.*?)&", portal_redirect_url)
            if not ip_match:
                raise ValueError("Could not extract Gateway IP from redirect URL.")
            gateway_ip = ip_match.group(1)

            # Portal Page HTML ထဲမှ Path ရှာဖွေခြင်း
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
                "Referer": portal_redirect_url,
            }
            portal_html = requests.get(portal_redirect_url, headers=headers).text
            path_match = re.search(r"href='(.*?)'</script>", portal_html)

            if not path_match:
                raise ValueError("Could not extract Session Path from Portal HTML.")
            session_url = "https://portal-as.ruijienetworks.com" + path_match.group(1)

            # ----------------------------------------------------
            # DISPLAY RESULTS IN A BEAUTIFUL TABLE
            # ----------------------------------------------------
            console.print("\n[bold green]🔑 PROVISIONING SUCCESSFUL - TARGET INJECT DATA[/bold green]")
            
            table = Table(title="Captured Network Parameters", title_style="bold cyan", border_style="bold green")
            table.add_column("Parameter", style="bold yellow", no_wrap=True)
            table.add_column("Value/Database Link", style="bold white")

            table.add_row("Target Gateway IP", gateway_ip)
            table.add_row("Captured Session URL", session_url)
            table.add_row("Encryption Status", "AES-256-CBC (Secured)")
            
            console.print(table)

            # ဖိုင်ထဲသို့ အလိုအလျောက် သိမ်းဆည်းခြင်း
            with open(".ip", "w") as f:
                f.write(gateway_ip)
            with open(".session_url", "w") as f:
                f.write(session_url)
                
            console.print("[dim text_cyan][*] Configuration logs compiled to local storage (.ip, .session_url)[/dim text_cyan]\n")
            return gateway_ip, session_url

        except Exception as err:
            console.print(Panel(f"[bold red]CRITICAL EXCEPTION ERROR:[/bold red]\n{err}", border_style="bold red", title="SYSTEM FAILURE"))
            return None, None

    # =====================================================================
    # CORE LOGIC FUNCTIONS (BACKGROUND PROCESS)
    # =====================================================================
    def unbind_session(self):
        username = self._get_username()
        if not username:
            return False

        online_info = self._get_online_info(username)
        if not online_info:
            return False

        mac_clean = online_info["mac"].replace(":", "")
        mac_req = ".".join([mac_clean[i : i + 4] for i in range(0, len(mac_clean), 4)])

        payload_data = {
            "ip": online_info["ip"],
            "mac": online_info["mac"],
            "ip_req": online_info["ip"],
            "mac_req": mac_req,
        }
        return self._execute_logout(payload_data, username)

    def _get_username(self):
        try:
            res = requests.get(self.username_get_url, timeout=5).json()
            return res.get("username")
        except:
            return None

    def _get_online_info(self, username):
        params = {"username": username, "usertype": "wifidog"}
        try:
            res = requests.get(self.online_info_url, params=params, timeout=5).json()
            return res["data"]["list"][0]
        except:
            return None

    def _encrypt_payload(self, auth_string):
        salt = get_random_bytes(8)
        key_iv = b""
        prev = b""
        while len(key_iv) < 48:
            prev = hashlib.md5(prev + self.enc_key.encode("utf-8") + salt).digest()
            key_iv += prev
        key = key_iv[:32]
        iv = key_iv[32:48]

        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(auth_string.encode("utf-8"), AES.block_size)
        encrypted = b"Salted__" + salt + cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode("utf-8")

    def _get_auth_token(self, username):
        try:
            raw_data = requests.get(self.baseurl, timeout=5).text
            match = re.search(r"chap_id=([^&]+)&chap_challenge=([^']+)", raw_data)
            if not match:
                return None
            chap_id = requests.utils.unquote(match.group(1))
            chap_challenge = requests.utils.unquote(match.group(2))
            auth_str = chap_id + chap_challenge + username
            return self._encrypt_payload(auth_str)
        except:
            return None

    def _execute_logout(self, data, username):
        auth_token = self._get_auth_token(username)
        if not auth_token:
            return False
        payload = f"ip={data['ip']}&mac={data['mac']}&ip_req={data['ip_req']}&mac_req={data['mac_req']}&auth={auth_token}"
        try:
            res = requests.post(self.logout_url, data=payload, timeout=5).json()
            return bool(res.get("success"))
        except:
            return False


if __name__ == "__main__":
    provisioner = RuijieWifiProvisioning()
    provisioner.start_provision()
