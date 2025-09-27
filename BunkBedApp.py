import json
import csv
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

tenant_data = []

class RoomScreen(Screen):
    def __init__(self, room_name, bunk_positions, background_image, app_ref, **kwargs):
        super().__init__(name=room_name, **kwargs)
        self.app_ref = app_ref
        layout = FloatLayout()

        bg = Image(source=background_image, allow_stretch=True, keep_ratio=False)
        layout.add_widget(bg)

        for bed_num, coords in bunk_positions.items():
            for bunk_type, pos in coords.items():
                bunk_id = f"{room_name}-{bunk_type}-{bed_num}"
                btn = Button(
                    text=f'{bunk_type.capitalize()} Bunk {bed_num} (Available)',
                    color=(0, 0, 0, 1),
                    size_hint=(0.25, 0.085),
                    pos_hint={'x': pos[0], 'y': pos[1]},
                    background_normal='',
                    background_color=(0, 1, 0, 0.5),
                    font_size='16sp'
                )
                btn.bunk_id = bunk_id
                btn.room_name = room_name

                for entry in tenant_data:
                    if entry["bunk_id"] == bunk_id and entry["status"] == "Unavailable":
                        btn.text = btn.text.replace("Available", "Unavailable")
                        btn.background_color = (1, 0, 0, 0.5)

                btn.bind(on_press=self.handle_press)
                layout.add_widget(btn)

        self.add_widget(layout)

    def handle_press(self, instance):
        if "Available" in instance.text:
            self.show_popup(instance)
        else:
            instance.text = instance.text.replace("Unavailable", "Available")
            instance.background_color = (0, 1, 0, 0.5)
            for entry in tenant_data:
                if entry["bunk_id"] == instance.bunk_id:
                    entry["status"] = "Available"
                    self.app_ref.save_data()

    def show_popup(self, bunk_button):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        name_input = TextInput(hint_text="Name", multiline=False)
        date_input = TextInput(hint_text="Day of arrival (YYYY-MM-DD)", multiline=False)
        number_input = TextInput(hint_text="Contact Number", multiline=False)

        submit_btn = Button(text="Submit", size_hint_y=None, height=40)
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=40)

        content.add_widget(Label(text="Enter Tenant Info"))
        content.add_widget(name_input)
        content.add_widget(date_input)
        content.add_widget(number_input)
        content.add_widget(submit_btn)
        content.add_widget(cancel_btn)

        popup = Popup(title="Tenant Information",
                      content=content,
                      size_hint=(0.8, 0.6),
                      auto_dismiss=False)

        def submit_data(instance):
            name = name_input.text.strip()
            date = date_input.text.strip()
            number = number_input.text.strip()

            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                date_input.text = ""
                return

            if name and date and number:
                if any(e["bunk_id"] == bunk_button.bunk_id and e["status"] == "Unavailable" for e in tenant_data):
                    popup.dismiss()
                    return

                tenant_data.append({
                    "bunk_id": bunk_button.bunk_id,
                    "room": bunk_button.room_name,
                    "status": "Unavailable",
                    "name": name,
                    "date": date,
                    "number": number,
                    "payment": 0
                })

                self.app_ref.save_data()
                bunk_button.text = bunk_button.text.replace("Available", "Unavailable")
                bunk_button.background_color = (1, 0, 0, 0.5)
                popup.dismiss()

        submit_btn.bind(on_press=submit_data)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

class RosterScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(name="Tenants", **kwargs)
        self.app_ref = app_ref
        self.layout = BoxLayout(orientation='vertical')
        self.summary = Label(text="", size_hint_y=0.1)
        self.layout.add_widget(self.summary)
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=10)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(Label(text="Tenant Sheet", size_hint_y=0.1))
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

    def on_pre_enter(self):
        self.grid.clear_widgets()

        total = len(tenant_data)
        occupied = sum(1 for e in tenant_data if e["status"] == "Unavailable")
        available = total - occupied
        total_payment = sum(e["payment"] for e in tenant_data if e["status"] == "Unavailable")

        self.summary.text = f"Total Tenants: {occupied} | Available Bunks: {available} | Total Payment: ₱{total_payment:,.2f}"

        for index, entry in sorted(enumerate(tenant_data), key=lambda x: x[1]["name"]):
            if entry["status"] == "Unavailable":
                row = BoxLayout(size_hint_y=None, height=40, spacing=10)
                info = f'{entry["room"]} - {entry["bunk_id"].split("-")[1].capitalize()} Bunk {entry["bunk_id"].split("-")[2]} | {entry["name"]} | {entry["Date"]} | {entry["number"]} | Payment: ₱{entry["payment"]:,.2f}'
                row.add_widget(Label(text=info))

                pay_btn = Button(text="Add Payment", size_hint_x=0.2)
                pay_btn.bind(on_press=lambda btn, i=index: self.add_payment(i))
                row.add_widget(pay_btn)

                delete_btn = Button(text="Delete", size_hint_x=0.2)
                delete_btn.bind(on_press=lambda btn, i=index: self.delete_entry(i))
                row.add_widget(delete_btn)

                self.grid.add_widget(row)

    def delete_entry(self, index):
        def confirm_delete(instance):
            del tenant_data[index]
            self.app_ref.save_data()
            self.on_pre_enter()
            confirm_popup.dismiss()

        confirm_content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        confirm_content.add_widget(Label(text="Are you sure you want to delete this entry?"))
        yes_btn = Button(text="Yes", size_hint_y=None, height=40)
        no_btn = Button(text="No", size_hint_y=None, height=40)
        confirm_content.add_widget(yes_btn)
        confirm_content.add_widget(no_btn)

        confirm_popup = Popup(title="Confirm Delete", content=confirm_content, size_hint=(0.6, 0.4), auto_dismiss=False)
        yes_btn.bind(on_press=confirm_delete)
        no_btn.bind(on_press=confirm_popup.dismiss)
        confirm_popup.open()

    def add_payment(self, index):
        entry = tenant_data[index]
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        amount_input = TextInput(hint_text="Enter payment amount", multiline=False, input_filter='float')
        submit_btn = Button(text="Submit", size_hint_y=None, height=40)
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=40)

        content.add_widget(Label(text=f"Add payment for {entry['name']}"))
        content.add_widget(amount_input)
        content.add_widget(submit_btn)
        content.add_widget(cancel_btn)

        popup = Popup(title="Payment Entry", content=content, size_hint=(0.7, 0.5), auto_dismiss=False)

        def submit_payment(instance):
            try:
                amount = float(amount_input.text.strip())
                entry["payment"] += amount
                self.app_ref.save_data()
                popup.dismiss()
                self.on_pre_enter()
            except ValueError:
                amount_input.text = ""

        submit_btn.bind(on_press=submit_payment)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

class BunkBedApp(App):
    def build(self):
        self.load_data()
        root = BoxLayout(orientation='vertical')
        self.sm = ScreenManager()
        room_a_positions = {
            1: {'upper': (0.08, 0.72), 'lower': (0.08, 0.63)},
            2: {'upper': (0.08, 0.52), 'lower': (0.08, 0.43)},
            3: {'upper': (0.65, 0.77), 'lower': (0.65, 0.68)},
            4: {'upper': (0.39, 0.58), 'lower': (0.39, 0.49)},
            5: {'upper': (0.65, 0.58), 'lower': (0.65, 0.49)},
        }

        room_b_positions = {
            1: {'upper': (0.05, 0.48), 'lower': (0.05, 0.39)},
            2: {'upper': (0.6, 0.8), 'lower': (0.6, 0.71)},
            3: {'upper': (0.6, 0.57), 'lower': (0.6, 0.48)},
            4: {'upper': (0.6, 0.34), 'lower': (0.6, 0.25)},
            5: {'upper': (0.05, 0.18), 'lower': (0.05, 0.09)},
        }

        self.sm.add_widget(RoomScreen("RoomA", room_a_positions, "floorplan.png", self))
        self.sm.add_widget(RoomScreen("RoomB", room_b_positions, "floorplan2.png", self))
        self.sm.add_widget(RosterScreen(app_ref=self))

        nav_bar = BoxLayout(size_hint_y=0.1)
        btn_room_a = Button(text="Room A")
        btn_room_b = Button(text="Room B")
        btn_roster = Button(text="Tenants")

        btn_room_a.bind(on_press=self.switch_to_room_a)
        btn_room_b.bind(on_press=self.switch_to_room_b)
        btn_roster.bind(on_press=self.switch_to_roster)

        nav_bar.add_widget(btn_room_a)
        nav_bar.add_widget(btn_room_b)
        nav_bar.add_widget(btn_roster)

        root.add_widget(self.sm)
        root.add_widget(nav_bar)

        return root

    def switch_to_room_a(self, instance):
        self.sm.current = "RoomA"

    def switch_to_room_b(self, instance):
        self.sm.current = "RoomB"

    def switch_to_roster(self, instance):
        self.sm.current = "Tenants"

    def save_data(self):
        with open("tenant_data.json", "w") as f:
            json.dump(tenant_data, f)

    def load_data(self):
        try:
            with open("tenant_data.json", "r") as f:
                loaded = json.load(f)
                tenant_data.clear()
                tenant_data.extend(loaded)
        except FileNotFoundError:
            pass

    def export_to_csv(self):
        if tenant_data:
            with open("tenant_data.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=tenant_data[0].keys())
                writer.writeheader()
                writer.writerows(tenant_data)

if __name__ == '__main__':
    BunkBedApp().run()
