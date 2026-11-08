from db_connection import get_dashboard_stats
import mechwarx_operations as ops
from datetime import datetime
from decimal import Decimal, InvalidOperation
import math
import random
import tkinter as tk
import customtkinter as ctk
import threading
import queue

# ---------- THEME ----------
BG = "#080B18"
PANEL = "#12182B"
PANEL_LIGHT = "#1B2340"
WHITE = "#F8FAFC"
MUTED = "#98A6C5"
BLUE = "#4F7CFF"
PURPLE = "#A855F7"
PINK = "#F02C9B"

ctk.set_appearance_mode("dark")



class NeonBackground(tk.Canvas):
    """Lightweight, gently animated aurora; one scheduled update at a time."""

    def __init__(self, master, **kwargs):
        super().__init__(master, bg=BG, highlightthickness=0, **kwargs)
        self.tick = 0.0
        self._job = None
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._job = self.after(180, self.animate)

    def _on_destroy(self, event):
        if event.widget is self and self._job is not None:
            try:
                self.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None

    @staticmethod
    def blend(a, b, amount):
        first = tuple(int(a[i:i + 2], 16) for i in (1, 3, 5))
        second = tuple(int(b[i:i + 2], 16) for i in (1, 3, 5))
        return "#{:02x}{:02x}{:02x}".format(*(
            int(x * (1 - amount) + y * amount)
            for x, y in zip(first, second)
        ))

    def animate(self):
        self._job = None
        if not self.winfo_exists():
            return
        if self.winfo_ismapped():
            self.delete("aurora")
            self.tick += 0.045
            w = max(self.winfo_width(), 1)
            h = max(self.winfo_height(), 1)
            bands = [
                ("#304C94", 0.22, 0.055, 0.0),
                ("#65318D", 0.47, 0.070, 1.8),
                ("#703465", 0.77, 0.055, 3.4),
            ]
            for color, base_y, amplitude, phase in bands:
                for layer in range(3, 0, -1):
                    points = []
                    for x in range(-40, w + 80, 70):
                        nx = x / w
                        wave = (
                            math.sin(nx * 5 + self.tick + phase) * amplitude
                            + math.sin(nx * 9 - self.tick * 0.6 + phase) * 0.012
                        )
                        points.extend((x, h * (base_y + wave) + layer * 7))
                    shade = self.blend(BG, color, 0.16 + (3 - layer) * 0.09)
                    self.create_line(
                        *points, fill=shade, width=layer * 8,
                        smooth=True, splinesteps=8,
                        capstyle=tk.ROUND, tags="aurora"
                    )
        # Schedule exactly ONE callback, outside every drawing loop.
        self._job = self.after(180, self.animate)


class MechWarX(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MechWar-X | Neo-Prime Command")
        self.geometry("1250x760")
        self.minsize(1050, 650)
        self.configure(fg_color=BG)

        self.active_page = "Dashboard"
        self._dashboard_queue = queue.Queue()
        self._operation_queue = queue.Queue()
        self.after(120, self._poll_operations)

        self.sidebar = ctk.CTkFrame(
            self,
            width=245,
            fg_color="#0D1224",
            corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.build_sidebar()

        self.main_area = ctk.CTkFrame(
            self,
            fg_color=BG,
            corner_radius=0
        )
        self.main_area.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.show_dashboard()

    def build_sidebar(self):
        ctk.CTkLabel(
            self.sidebar,
            text="◈ MECHWAR-X",
            font=("Arial", 25, "bold"),
            text_color=WHITE
        ).pack(pady=(38, 5), padx=18)

        ctk.CTkLabel(
            self.sidebar,
            text="NEO-PRIME COMMAND",
            font=("Arial", 10, "bold"),
            text_color=PURPLE
        ).pack(pady=(0, 45))

        self.nav_buttons = {}

        pages = [
            ("Dashboard", "◈"),
            ("Mech Registration", "▣"),
            ("Deployment Search", "⌕"),
            ("Book Deployment", "◇"),
            ("Maintenance Console", "⚙")
        ]

        for name, symbol in pages:
            button = ctk.CTkButton(
                self.sidebar,
                text=f"  {symbol}    {name}",
                anchor="w",
                height=48,
                corner_radius=12,
                fg_color="transparent",
                hover_color=PANEL_LIGHT,
                text_color=MUTED,
                font=("Arial", 13, "bold"),
                command=lambda page=name: self.show_page(page)
            )
            button.pack(fill="x", padx=15, pady=5)
            self.nav_buttons[name] = button

        ctk.CTkLabel(
            self.sidebar,
            text="●  MYSQL CONNECTED FEATURES",
            font=("Arial", 11, "bold"),
            text_color="#7DD3FC"
        ).pack(side="bottom", pady=30)

    def clear_main(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

    def update_navigation(self):
        for name, button in self.nav_buttons.items():
            selected = name == self.active_page
            button.configure(
                fg_color="#273466" if selected else "transparent",
                text_color=WHITE if selected else MUTED
            )

    def show_page(self, name):
        self.active_page = name
        self.update_navigation()

        if name == "Dashboard":
            self.show_dashboard()
        else:
            self.show_placeholder(name)

    def add_header(self, parent, eyebrow, title, subtitle):
        ctk.CTkLabel(
            parent,
            text=eyebrow,
            text_color=PURPLE,
            font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=(0, 9))

        ctk.CTkLabel(
            parent,
            text=title,
            text_color=WHITE,
            font=("Arial", 34, "bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            parent,
            text=subtitle,
            text_color=MUTED,
            font=("Arial", 13)
        ).pack(anchor="w", pady=(7, 24))

    def show_dashboard(self):
        self.clear_main()
        self.active_page = "Dashboard"
        self.update_navigation()

        background = NeonBackground(self.main_area)
        background.pack(fill="both", expand=True)

        # CTk panels sit above the animated canvas.
        overlay = ctk.CTkFrame(
            background,
            fg_color="#0D1022",
            corner_radius=18,
            border_width=1,
            border_color="#242047"
        )
       
        overlay.place(
            relx=0.5,
            rely=0.5,
            relwidth=0.88,
            relheight=0.86,
            anchor="center"
        )

        self.add_header(
            overlay,
            "FLEET OPERATIONS / OVERVIEW",
            "Command Center",
            "Your central hub for the Neo-Prime Gladiatorial League."
        )

        hero = ctk.CTkFrame(
            overlay,
            fg_color="#191635",
            corner_radius=20,
            border_width=1,
            border_color="#44336E"
        )
        hero.pack(fill="x", pady=(0, 22))

        ctk.CTkLabel(
            hero,
            text="WELCOME TO NEO-PRIME",
            font=("Arial", 25, "bold"),
            text_color="#D8B4FE"
        ).pack(anchor="w", padx=28, pady=(28, 10))

        ctk.CTkLabel(
            hero,
            text="Manage powerful machines. Coordinate deployments. Control the arena.",
            font=("Arial", 13),
            text_color="#C7C8E5"
        ).pack(anchor="w", padx=28, pady=(0, 28))

        stats = ctk.CTkFrame(
            overlay,
            fg_color="transparent"
        )
        stats.pack(fill="x", pady=(0, 22))
        # Never wait for MySQL on Tkinter's UI thread.
        dashboard_data = {"mechs": "--", "deployments": "--", "incidents": "--"}
        data_mode = "CONNECTING..."
        self._dashboard_value_labels = []
        self._dashboard_mode_labels = []
        self._dashboard_token = object()
        token = self._dashboard_token

        cards = [
            ("TOTAL MECHS", str(dashboard_data["mechs"]).zfill(2), BLUE),
            ("DEPLOYMENT RECORDS", str(dashboard_data["deployments"]).zfill(2), PURPLE),
            ("MAINTENANCE INCIDENTS", str(dashboard_data["incidents"]).zfill(2), PINK)
        ]       
        for index, (label, value, accent) in enumerate(cards):
            stats.grid_columnconfigure(index, weight=1)

            card = ctk.CTkFrame(
                stats,
                fg_color=PANEL,
                corner_radius=17,
                border_width=1,
                border_color="#2B3556"
            )
            card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=(0, 12) if index < 2 else 0
            )

            ctk.CTkLabel(
                card,
                text=label,
                font=("Arial", 10, "bold"),
                text_color=MUTED
            ).pack(anchor="w", padx=22, pady=(22, 6))

            value_label = ctk.CTkLabel(
                card, text=value, font=("Arial", 38, "bold"), text_color=accent
            )
            value_label.pack(anchor="w", padx=22)
            self._dashboard_value_labels.append(value_label)

            mode_label = ctk.CTkLabel(
                card, text=data_mode, font=("Arial", 9), text_color="#71809E"
            )
            mode_label.pack(anchor="w", padx=22, pady=(5, 20))
            self._dashboard_mode_labels.append(mode_label)

        threading.Thread(
            target=self._load_dashboard_stats,
            args=(token,),
            daemon=True,
        ).start()
        self.after(150, lambda: self._poll_dashboard_stats(token))

        activity = ctk.CTkFrame(
            overlay,
            fg_color=PANEL,
            corner_radius=18,
            border_width=1,
            border_color="#2B3556"
        )
        activity.pack(fill="both", expand=True)

        ctk.CTkLabel(
            activity,
            text="OPERATIONS OVERVIEW",
            font=("Arial", 16, "bold"),
            text_color=WHITE
        ).pack(anchor="w", padx=25, pady=(22, 7))

        ctk.CTkLabel(
            activity,
            text="Live fleet statistics are synchronized with your MySQL database.",
            font=("Arial", 12),
            text_color=MUTED
        ).pack(anchor="w", padx=25)

        ctk.CTkProgressBar(
            activity,
            progress_color=PURPLE,
            fg_color="#28304C",
            height=10
        ).pack(fill="x", padx=25, pady=(30, 10))

        # This is a design preview, not a database metric.
        progress = activity.winfo_children()[-1]
        progress.set(0.65)

        ctk.CTkLabel(
            activity,
            text="NEO-PRIME OPERATIONS  •  MYSQL DATA SOURCE",
            text_color="#8C9ABD",
            font=("Arial", 10)
        ).pack(anchor="w", padx=25)

    
    def _load_dashboard_stats(self, token):
        try:
            result = get_dashboard_stats()
            self._dashboard_queue.put((token, result, None))
        except Exception as exc:
            self._dashboard_queue.put((token, None, str(exc)))

    def _poll_dashboard_stats(self, token):
        if not self.winfo_exists() or self._dashboard_token is not token:
            return
        try:
            while True:
                result_token, data, error = self._dashboard_queue.get_nowait()
                if result_token is not token:
                    continue
                if error:
                    for label in self._dashboard_mode_labels:
                        label.configure(text="DATABASE OFFLINE")
                else:
                    for label, key in zip(
                        self._dashboard_value_labels,
                        ("mechs", "deployments", "incidents"),
                    ):
                        label.configure(text=str(data[key]).zfill(2))
                    for label in self._dashboard_mode_labels:
                        label.configure(text="LIVE DATABASE")
                return
        except queue.Empty:
            self.after(150, lambda: self._poll_dashboard_stats(token))

    def _run_operation(self, function, args, on_success, status_label):
        def worker():
            try:
                result = function(*args)
                self._operation_queue.put((on_success, status_label, result, None))
            except Exception as exc:
                self._operation_queue.put((on_success, status_label, None, str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def _poll_operations(self):
        try:
            while True:
                callback, label, result, error = self._operation_queue.get_nowait()
                if not label.winfo_exists():
                    continue
                if error:
                    label.configure(text=f'✕ MySQL: {error[:180]}', text_color='#FB7185')
                else:
                    callback(result)
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(120, self._poll_operations)

    def _refresh_maintenance(self):
        def finished(rows):
            self.demo_incidents = rows
            self.render_maintenance()
        self._run_operation(ops.list_incidents, (), finished, self.maintenance_status)

    def show_placeholder(self, name):
        self.clear_main()

        panel = ctk.CTkScrollableFrame(
            self.main_area,
            fg_color="transparent"
        )
        panel.pack(
            fill="both",
            expand=True,
            padx=40,
            pady=35
        )

        self.add_header(
            panel,
            "NEO-PRIME / OPERATIONS",
            name,
            "Fleet management and deployment operations."
        )

        if name == "Mech Registration":
            self.build_registration(panel)
        elif name == "Deployment Search":
            self.build_deployment_search(panel)
        elif name == "Book Deployment":
            self.build_booking(panel)
        elif name == "Maintenance Console":
            self.build_maintenance(panel)
        else:

            ctk.CTkLabel(
                panel,
                text="COMING NEXT",
                font=("Arial", 20, "bold"),
                text_color=PURPLE
            ).pack(pady=70)

    def build_registration(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color="#17152E",
            corner_radius=20,
            border_width=1,
            border_color="#514080"
        )
        card.pack(fill="x", pady=12)

        ctk.CTkLabel(
            card,
            text="REGISTER NEW MECH",
            font=("Arial", 22, "bold"),
            text_color="#D8B4FE"
        ).pack(anchor="w", padx=28, pady=(25, 8))

        ctk.CTkLabel(
            card,
            text="Enter the new machine's details to prepare its fleet record.",
            text_color=MUTED,
            font=("Arial", 12)
        ).pack(anchor="w", padx=28, pady=(0, 20))

        self.mech_fields = {}

        fields = [
            ("Chassis Serial Number", "e.g. NP-LS-1004"),
            ("Manufacturer", "e.g. Titan Dynamics"),
            ("Model", "e.g. Phantom X2"),
            ("Assembly Year", "e.g. 2026"),
            ("Armor Color", "e.g. Black"),
            ("Mech Type ID", "e.g. 1"),
            ("Garage ID", "e.g. 2"),
            ("Daily Deployment Rate", "e.g. 2500.00")
        ]

        for label, placeholder in fields:
            ctk.CTkLabel(
                card,
                text=label,
                text_color=WHITE,
                font=("Arial", 12, "bold")
            ).pack(anchor="w", padx=28, pady=(8, 5))

            entry = ctk.CTkEntry(
                card,
                placeholder_text=placeholder,
                height=44,
                fg_color="#101427",
                border_color="#3B4166",
                corner_radius=10
            )
            entry.pack(fill="x", padx=28, pady=(0, 10))
            self.mech_fields[label] = entry

        ctk.CTkButton(
            card,
            text="REGISTER MECH IN MYSQL",
            height=48,
            fg_color=PURPLE,
            hover_color="#9333EA",
            font=("Arial", 13, "bold"),
            command=self.validate_mech
        ).pack(fill="x", padx=28, pady=(20, 12))

        self.registration_status = ctk.CTkLabel(
            card,
            text="LIVE MYSQL • Registration saves a new mech and inventory record.",
            text_color=MUTED,
            font=("Arial", 11)
        )
        self.registration_status.pack(pady=(0, 25))

    def validate_mech(self):
        values = {key: entry.get().strip() for key, entry in self.mech_fields.items()}
        try:
            for name in ('Chassis Serial Number', 'Manufacturer', 'Model', 'Armor Color'):
                if not values[name]:
                    raise ValueError(f'{name} is required.')
            for name in ('Mech Type ID', 'Garage ID', 'Assembly Year'):
                if not values[name].isdigit() or int(values[name]) <= 0:
                    raise ValueError(f'Enter a valid {name}.')
            if int(values['Assembly Year']) > datetime.now().year:
                raise ValueError('Assembly Year cannot be in the future.')
            rate = Decimal(values['Daily Deployment Rate'])
            if not rate.is_finite() or rate <= 0 or rate.as_tuple().exponent < -2:
                raise ValueError('Daily rate must be positive with at most 2 decimals.')
            if len(values['Chassis Serial Number']) > 50:
                raise ValueError('Serial number is too long.')
        except (ValueError, InvalidOperation) as error:
            self.registration_status.configure(text=f'✕ {error}', text_color='#FB7185')
            return
        self.registration_status.configure(text='Saving mech to MySQL...', text_color=MUTED)
        self._run_operation(ops.register_mech, (values,), lambda mech_id:
            self.registration_status.configure(text=f'✓ Mech #{mech_id} registered in MySQL!', text_color='#4ADE80'),
            self.registration_status)


    def build_deployment_search(self, parent):
        self.demo_deployments = [
            (1, 1, 1, "2026-11-20 08:00", "Cancelled"),
            (2, 2, 1, "2026-11-20 08:00", "Match Booked"),
            (3, 3, 2, "2026-10-20 10:00", "Match Booked"),
            (4, 1, 3, "2026-11-25 08:00", "Match Booked"),
        ]

        card = ctk.CTkFrame(
            parent,
            fg_color="#17152E",
            corner_radius=20,
            border_width=1,
            border_color="#514080"
        )
        card.pack(fill="x", pady=12)

        ctk.CTkLabel(
            card,
            text="DEPLOYMENT INTELLIGENCE",
            font=("Arial", 22, "bold"),
            text_color="#D8B4FE"
        ).pack(anchor="w", padx=25, pady=(25, 6))

        ctk.CTkLabel(
            card,
            text="Search deployment records by client ID.",
            font=("Arial", 12),
            text_color=MUTED
        ).pack(anchor="w", padx=25, pady=(0, 18))

        search_row = ctk.CTkFrame(card, fg_color="transparent")
        search_row.pack(fill="x", padx=25, pady=(0, 22))

        self.client_search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Enter Client ID (e.g. 1)",
            height=45,
            fg_color="#101427",
            border_color="#3B4166",
            corner_radius=10
        )
        self.client_search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 12)
        )

        ctk.CTkButton(
            search_row,
            text="SEARCH",
            width=140,
            height=45,
            fg_color=PURPLE,
            hover_color="#9333EA",
            command=self.search_deployments
        ).pack(side="right")

        self.search_status = ctk.CTkLabel(
            parent,
            text="LIVE MYSQL • Enter a client ID to search records.",
            text_color=MUTED,
            font=("Arial", 11)
        )
        self.search_status.pack(anchor="w", pady=(8, 10))

        self.results_frame = ctk.CTkFrame(
            parent,
            fg_color=PANEL,
            corner_radius=16,
            border_width=1,
            border_color="#2B3556"
        )
        self.results_frame.pack(fill="x")

        self.render_deployments([])

    def search_deployments(self):
        client_id = self.client_search_entry.get().strip()
        if not client_id.isdigit() or int(client_id) <= 0:
            self.search_status.configure(text='✕ Enter a valid Client ID.', text_color='#FB7185')
            return
        self.search_status.configure(text='Searching MySQL...', text_color=MUTED)
        def finished(rows):
            self.render_deployments(rows)
            self.search_status.configure(text=f'✓ Found {len(rows)} deployment(s) for Client {client_id}.', text_color='#4ADE80')
        self._run_operation(ops.search_deployments, (int(client_id),), finished, self.search_status)

    def render_deployments(self, records):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        headers = [
            "MANIFEST", "CLIENT", "MECH", "SCHEDULED START", "STATUS"
        ]

        for col, heading in enumerate(headers):
            self.results_frame.grid_columnconfigure(col, weight=1)

            ctk.CTkLabel(
                self.results_frame,
                text=heading,
                text_color="#94A3B8",
                font=("Arial", 10, "bold")
            ).grid(
                row=0,
                column=col,
                padx=10,
                pady=18,
                sticky="w"
            )

        if not records:
            ctk.CTkLabel(
                self.results_frame,
                text="No deployments found for this client.",
                text_color=MUTED
            ).grid(
                row=1,
                column=0,
                columnspan=5,
                pady=25
            )
            return

        for index, record in enumerate(records, start=1):
            for col, value in enumerate(record):
                color = WHITE

                if col == 4:
                    color = (
                        "#FB7185" if value == "Cancelled"
                        else "#4ADE80"
                    )

                ctk.CTkLabel(
                    self.results_frame,
                    text=str(value),
                    text_color=color,
                    font=("Arial", 11)
                ).grid(
                    row=index,
                    column=col,
                    padx=10,
                    pady=13,
                    sticky="w"
                )


    def build_booking(self, parent):
        from datetime import datetime

        card = ctk.CTkFrame(
            parent,
            fg_color="#17152E",
            corner_radius=20,
            border_width=1,
            border_color="#514080"
        )
        card.pack(fill="x", pady=12)

        ctk.CTkLabel(
            card,
            text="DEPLOYMENT BOOKING",
            font=("Arial", 22, "bold"),
            text_color="#D8B4FE"
        ).pack(anchor="w", padx=28, pady=(25, 8))

        ctk.CTkLabel(
            card,
            text="Schedule a mech deployment with conflict validation.",
            text_color=MUTED
        ).pack(anchor="w", padx=28, pady=(0, 20))

        self.booking_fields = {}

        fields = [
            ("Client ID", "e.g. 1"),
            ("Mech ID", "e.g. 2"),
            ("Departure Garage ID", "e.g. 1"),
            ("Return Garage ID", "e.g. 2"),
            ("Scheduled Start", "YYYY-MM-DD HH:MM"),
            ("Scheduled Return", "YYYY-MM-DD HH:MM")
        ]

        for label, placeholder in fields:
            ctk.CTkLabel(
                card,
                text=label,
                text_color=WHITE,
                font=("Arial", 12, "bold")
            ).pack(anchor="w", padx=28, pady=(8, 5))

            entry = ctk.CTkEntry(
                card,
                placeholder_text=placeholder,
                height=44,
                fg_color="#101427",
                border_color="#3B4166",
                corner_radius=10
            )
            entry.pack(fill="x", padx=28, pady=(0, 10))
            self.booking_fields[label] = entry

        ctk.CTkButton(
            card,
            text="BOOK DEPLOYMENT IN MYSQL",
            height=48,
            fg_color=PURPLE,
            hover_color="#9333EA",
            font=("Arial", 13, "bold"),
            command=self.validate_booking
        ).pack(fill="x", padx=28, pady=(20, 12))

        self.booking_status = ctk.CTkLabel(
            card,
            text="LIVE MYSQL • Uses BookDeployment to validate and save.",
            text_color=MUTED,
            font=("Arial", 11)
        )
        self.booking_status.pack(pady=(0, 25))

        cancel_card = ctk.CTkFrame(parent, fg_color="#17152E", corner_radius=18,
                                   border_width=1, border_color="#514080")
        cancel_card.pack(fill="x", pady=(10, 20))
        ctk.CTkLabel(cancel_card, text="CANCEL AN UPCOMING DEPLOYMENT",
                     font=("Arial", 17, "bold"), text_color=WHITE).pack(
                         anchor="w", padx=25, pady=(22, 8))
        self.cancel_id_entry = ctk.CTkEntry(
            cancel_card, placeholder_text="Enter booked Manifest ID",
            height=42, fg_color="#101427", border_color="#3B4166")
        self.cancel_id_entry.pack(fill="x", padx=25, pady=(0, 10))
        ctk.CTkButton(cancel_card, text="CANCEL BOOKED DEPLOYMENT",
                      fg_color="#7C3AED", hover_color="#6D28D9", height=44,
                      command=self.cancel_booking).pack(fill="x", padx=25)
        self.cancel_status = ctk.CTkLabel(
            cancel_card, text="Cancels booked manifests using MySQL.",
            text_color=MUTED)
        self.cancel_status.pack(pady=(8, 20))

    def cancel_booking(self):
        manifest_id = self.cancel_id_entry.get().strip()
        if not manifest_id.isdigit() or int(manifest_id) <= 0:
            self.cancel_status.configure(text="✕ Enter a positive Manifest ID.",
                                         text_color="#FB7185")
            return
        self.cancel_status.configure(text="Cancelling in MySQL...", text_color=MUTED)
        self._run_operation(
            ops.cancel_deployment, (int(manifest_id),),
            lambda _: self.cancel_status.configure(
                text="✓ Deployment cancelled. Inventory status synchronized.",
                text_color="#4ADE80"), self.cancel_status)

    def validate_booking(self):
        values = {key: entry.get().strip() for key, entry in self.booking_fields.items()}
        try:
            for name in ('Client ID', 'Mech ID', 'Departure Garage ID', 'Return Garage ID'):
                if not values[name].isdigit() or int(values[name]) <= 0:
                    raise ValueError(f'Enter a valid {name}.')
            start = datetime.strptime(values['Scheduled Start'], '%Y-%m-%d %H:%M')
            end = datetime.strptime(values['Scheduled Return'], '%Y-%m-%d %H:%M')
            if end <= start or start <= datetime.now():
                raise ValueError('Choose a future start and a later return time.')
        except ValueError as error:
            self.booking_status.configure(text=f'✕ {error}', text_color='#FB7185')
            return
        self.booking_status.configure(text='Booking through MySQL stored procedure...', text_color=MUTED)
        self._run_operation(ops.book_deployment, (values,), lambda _:
            self.booking_status.configure(text='✓ Deployment booked in MySQL!', text_color='#4ADE80'),
            self.booking_status)


    def build_maintenance(self, parent):
        # Live rows are loaded asynchronously from MySQL.
        self.demo_incidents = []

        header = ctk.CTkFrame(
            parent,
            fg_color="#17152E",
            corner_radius=20,
            border_width=1,
            border_color="#514080"
        )
        header.pack(fill="x", pady=(10, 20))

        ctk.CTkLabel(
            header,
            text="MAINTENANCE CONTROL",
            font=("Arial", 23, "bold"),
            text_color="#D8B4FE"
        ).pack(anchor="w", padx=25, pady=(25, 8))

        ctk.CTkLabel(
            header,
            text="Monitor critical incidents and manage repair operations.",
            text_color=MUTED,
            font=("Arial", 12)
        ).pack(anchor="w", padx=25, pady=(0, 25))

        self.maintenance_summary = ctk.CTkLabel(
            parent,
            text="",
            text_color="#F472B6",
            font=("Arial", 14, "bold")
        )
        self.maintenance_summary.pack(anchor="w", pady=(0, 15))

        self.maintenance_table = ctk.CTkFrame(
            parent,
            fg_color=PANEL,
            corner_radius=16,
            border_width=1,
            border_color="#2B3556"
        )
        self.maintenance_table.pack(fill="x", pady=(0, 20))

        action_card = ctk.CTkFrame(
            parent,
            fg_color="#17152E",
            corner_radius=18,
            border_width=1,
            border_color="#514080"
        )
        action_card.pack(fill="x")

        ctk.CTkLabel(
            action_card,
            text="REPAIR MANAGEMENT",
            font=("Arial", 17, "bold"),
            text_color=WHITE
        ).pack(anchor="w", padx=25, pady=(22, 12))

        self.incident_entry = ctk.CTkEntry(
            action_card,
            placeholder_text="Enter Incident ID",
            height=44,
            fg_color="#101427",
            border_color="#3B4166"
        )
        self.incident_entry.pack(fill="x", padx=25, pady=(0, 12))

        ctk.CTkButton(
            action_card,
            text="MARK INCIDENT AS REPAIRED",
            height=46,
            fg_color=PURPLE,
            hover_color="#9333EA",
            command=self.mark_repaired
        ).pack(fill="x", padx=25, pady=(0, 12))

        self.maintenance_status = ctk.CTkLabel(
            action_card,
            text="LIVE MYSQL • Repair changes are saved.",
            text_color=MUTED,
            font=("Arial", 11)
        )
        self.maintenance_status.pack(pady=(0, 22))

        report_card = ctk.CTkFrame(parent, fg_color="#17152E",
                                  corner_radius=18, border_width=1,
                                  border_color="#514080")
        report_card.pack(fill="x", pady=(18, 16))
        ctk.CTkLabel(report_card, text="FILE A NEW DAMAGE INCIDENT",
                     font=("Arial", 18, "bold"), text_color="#D8B4FE").pack(
                         anchor="w", padx=25, pady=(22, 10))
        self.incident_fields = {}
        for name, placeholder in (
            ("Mech ID", "e.g. 3"),
            ("Reporting Client ID", "e.g. 1"),
            ("Technician ID", "e.g. 1"),
            ("Damage Description", "Describe the damage or maintenance request"),
            ("Engineering Notes", "Initial engineering / diagnostic notes"),
        ):
            ctk.CTkLabel(report_card, text=name, text_color=WHITE,
                         font=("Arial", 12, "bold")).pack(
                             anchor="w", padx=25, pady=(8, 4))
            entry = ctk.CTkEntry(report_card, placeholder_text=placeholder,
                                 height=43, fg_color="#101427",
                                 border_color="#3B4166")
            entry.pack(fill="x", padx=25, pady=(0, 8))
            self.incident_fields[name] = entry
        ctk.CTkLabel(report_card, text="Issue Type", text_color=WHITE).pack(
            anchor="w", padx=25, pady=(8, 4))
        self.incident_type = ctk.CTkOptionMenu(
            report_card, values=["Routine", "Critical"], fg_color="#273466",
            button_color=PURPLE)
        self.incident_type.pack(fill="x", padx=25, pady=(0, 10))
        ctk.CTkLabel(report_card, text="Severity", text_color=WHITE).pack(
            anchor="w", padx=25, pady=(8, 4))
        self.incident_severity = ctk.CTkOptionMenu(
            report_card, values=["Low", "Medium", "High", "Critical"],
            fg_color="#273466", button_color=PURPLE)
        self.incident_severity.pack(fill="x", padx=25, pady=(0, 12))
        ctk.CTkButton(report_card, text="FILE INCIDENT IN MYSQL",
                      fg_color=PURPLE, height=46, command=self.file_incident).pack(
                          fill="x", padx=25, pady=(10, 8))
        self.new_incident_status = ctk.CTkLabel(
            report_card, text="Critical failures automatically lock the mech.",
            text_color=MUTED)
        self.new_incident_status.pack(pady=(2, 22))

        self.render_maintenance()
        self._refresh_maintenance()

    def file_incident(self):
        values = {name: entry.get().strip()
                  for name, entry in self.incident_fields.items()}
        values["Issue Type"] = self.incident_type.get()
        values["Severity"] = self.incident_severity.get()
        for name in ("Mech ID", "Reporting Client ID", "Technician ID"):
            if not values[name].isdigit() or int(values[name]) <= 0:
                self.new_incident_status.configure(
                    text=f"✕ Enter a positive {name}.", text_color="#FB7185")
                return
        if not values["Damage Description"] or not values["Engineering Notes"]:
            self.new_incident_status.configure(
                text="✕ Damage description and engineering notes are required.",
                text_color="#FB7185")
            return
        if len(values["Damage Description"]) > 2000 or len(values["Engineering Notes"]) > 2000:
            self.new_incident_status.configure(
                text="✕ Use 2000 characters or fewer per description.",
                text_color="#FB7185")
            return
        self.new_incident_status.configure(text="Saving incident to MySQL...",
                                           text_color=MUTED)
        def finished(incident_id):
            self.new_incident_status.configure(
                text=f"✓ Incident #{incident_id} saved. Critical asset lock applied if needed.",
                text_color="#4ADE80")
            self._refresh_maintenance()
        self._run_operation(ops.create_incident, (values,), finished,
                            self.new_incident_status)

    def render_maintenance(self):
        for widget in self.maintenance_table.winfo_children():
            widget.destroy()

        unresolved = sum(
            1 for incident in self.demo_incidents
            if incident.get("issue_type", incident["severity"]) == "Critical"
            and incident["status"] != "Repaired"
        )

        self.maintenance_summary.configure(
            text=f"UNRESOLVED CRITICAL INCIDENTS: {unresolved}"
        )

        columns = [
            "INCIDENT ID", "MECH ID", "TYPE", "SEVERITY", "REPAIR STATUS"
        ]

        for col, label in enumerate(columns):
            self.maintenance_table.grid_columnconfigure(col, weight=1)

            ctk.CTkLabel(
                self.maintenance_table,
                text=label,
                text_color=MUTED,
                font=("Arial", 11, "bold")
            ).grid(
                row=0,
                column=col,
                padx=12,
                pady=17,
                sticky="w"
            )

        for row_index, incident in enumerate(
            self.demo_incidents, start=1
        ):
            values = [
                incident["id"],
                incident["mech"],
                incident.get("issue_type", incident["severity"]),
                incident["severity"],
                incident["status"]
            ]

            for col, value in enumerate(values):
                color = WHITE

                if col in (2, 3) and value == "Critical":
                    color = "#FB7185"

                if col == 4:
                    color = (
                        "#4ADE80" if value == "Repaired"
                        else "#FBBF24"
                    )

                ctk.CTkLabel(
                    self.maintenance_table,
                    text=str(value),
                    text_color=color,
                    font=("Arial", 12)
                ).grid(
                    row=row_index,
                    column=col,
                    padx=12,
                    pady=14,
                    sticky="w"
                )

    def mark_repaired(self):
        incident_id = self.incident_entry.get().strip()
        if not incident_id.isdigit() or int(incident_id) <= 0:
            self.maintenance_status.configure(text='✕ Enter a valid Incident ID.', text_color='#FB7185')
            return
        self.maintenance_status.configure(text='Updating MySQL...', text_color=MUTED)
        def finished(changed):
            self.maintenance_status.configure(
                text='✓ Repair saved in MySQL.' if changed else 'ℹ Incident not found or already repaired.',
                text_color='#4ADE80' if changed else '#FBBF24')
            self._refresh_maintenance()
        self._run_operation(ops.mark_incident_repaired, (int(incident_id),), finished, self.maintenance_status)

if __name__ == "__main__":
    app = MechWarX()
    app.mainloop()
