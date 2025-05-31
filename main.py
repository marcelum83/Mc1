import kivy
kivy.require('2.0.0') # Require Kivy version 2.0.0 or higher

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, Rectangle
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup # Added Popup import
from kivy.uix.spinner import Spinner # Added Spinner import
import json 
import os   
import uuid # Added uuid import

class DynamicScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.edit_popup = None 
        self.widget_text_input = None
        self.popup_widget_list_layout = None
        # For action configuration in popup
        self.action_type_spinner = None
        self.target_screen_spinner = None
        self.popup_message_input = None

        main_screen_layout = BoxLayout(orientation='vertical')

        controls_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='48dp')
        controls_layout.add_widget(Label(text=self.name)) 

        edit_button = Button(text='Edit Screen')
        edit_button.bind(on_press=self.edit_screen_popup)
        controls_layout.add_widget(edit_button)

        back_button = Button(text='Go back to Home Screen')
        back_button.bind(on_press=self.go_back_home)
        controls_layout.add_widget(back_button)
        
        main_screen_layout.add_widget(controls_layout)

        self.content_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        main_screen_layout.add_widget(self.content_layout)
        
        self.add_widget(main_screen_layout)

        with self.canvas.before:
            self.bg_color = Color(1, 1, 1, 1) # Default white
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect_size, pos=self._update_bg_rect_pos)

    def _update_bg_rect_size(self, instance, value):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.size = value

    def _update_bg_rect_pos(self, instance, value):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = value

    def add_widget_to_screen(self, widget_type, widget_text_override=None, widget_id_override=None, action_config_override=None, from_load=False, *args):
        app = App.get_running_app()
        widget_text = ""

        if from_load and widget_text_override is not None:
            widget_text = widget_text_override
        elif self.widget_text_input: # Interactive adding
            widget_text = self.widget_text_input.text
        
        if not widget_text.strip() and not from_load : # Allow loading empty text widgets if they were saved that way
            print("Widget text is empty, not adding.")
            return

        new_widget = None
        widget_id = widget_id_override if from_load else f"{widget_type}_{uuid.uuid4().hex[:6]}"
        action_config = None

        if widget_type == 'label':
            new_widget = Label(text=widget_text, size_hint_y=None, height='40dp')
        elif widget_type == 'button':
            new_widget = Button(text=widget_text, size_hint_y=None, height='48dp')
            if not from_load and self.action_type_spinner: # Interactive adding a button
                action_type = self.action_type_spinner.text
                if action_type == 'Navigate to Screen' and self.target_screen_spinner:
                    action_config = {'type': 'navigate', 'target': self.target_screen_spinner.text}
                elif action_type == 'Show Popup Message' and self.popup_message_input:
                    action_config = {'type': 'popup', 'message': self.popup_message_input.text}
            elif from_load and action_config_override: # Loading a button
                action_config = action_config_override
            
            if new_widget and action_config: # Store action_config on the button instance
                new_widget.action_config = action_config
                new_widget.bind(on_press=self.execute_button_action) # Bind action here
        
        if new_widget:
            new_widget.widget_id = widget_id # Assign widget_id
            self.content_layout.add_widget(new_widget)
        
        if self.widget_text_input and not from_load: # Clear input only for interactive mode
            self.widget_text_input.text = "" 
            # Potentially reset action config UI fields here too
            if self.action_type_spinner: self.action_type_spinner.text = 'None'
            if self.popup_message_input: self.popup_message_input.text = ''
            if self.target_screen_spinner: self.target_screen_spinner.values = [] ; self.target_screen_spinner.text = 'Target Screen'


        if not from_load and app and app.sm and hasattr(app, 'save_screens') and app.sm.has_screen('home'):
             app.save_screens()
             if self.edit_popup and self.popup_widget_list_layout:
                 self.refresh_popup_widget_list()

    def execute_button_action(self, button_instance):
        if not hasattr(button_instance, 'action_config') or not button_instance.action_config:
            return

        action_type = button_instance.action_config.get('type')
        app = App.get_running_app()

        if action_type == 'navigate':
            target_screen_name = button_instance.action_config.get('target')
            if target_screen_name and app.sm.has_screen(target_screen_name):
                app.sm.current = target_screen_name
            else:
                print(f"Error: Target screen '{target_screen_name}' not found for navigation.")
        elif action_type == 'popup':
            message = button_instance.action_config.get('message', 'No message.')
            popup = Popup(title='Popup Message',
                          content=Label(text=message),
                          size_hint=(0.8, 0.4))
            popup.open()

    def refresh_popup_widget_list(self):
        if not self.edit_popup or not self.popup_widget_list_layout:
            return

        self.popup_widget_list_layout.clear_widgets()
        if not self.content_layout.children:
            self.popup_widget_list_layout.add_widget(Label(text='No widgets on this screen.', size_hint_y=None, height='30dp'))
            return

        for widget in reversed(self.content_layout.children): # Display in visual order
            widget_info_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='30dp', spacing=5, padding=(0,0,5,0))

            widget_type = 'Unknown'
            if isinstance(widget, Label):
                widget_type = 'Label'
            elif isinstance(widget, Button):
                widget_type = 'Button'

            widget_text_display = getattr(widget, 'text', 'N/A')
            info_text = f"{widget_type}: {widget_text_display[:20]}" + ('...' if len(widget_text_display) > 20 else '')
            widget_info_layout.add_widget(Label(text=info_text, size_hint_x=0.8))

            delete_button = Button(text='Delete', size_hint_x=None, width='100dp')
            delete_button.widget_id_to_delete = getattr(widget, 'widget_id', None)
            delete_button.bind(on_press=self.confirm_delete_widget)
            widget_info_layout.add_widget(delete_button)

            self.popup_widget_list_layout.add_widget(widget_info_layout)

    def confirm_delete_widget(self, button_instance):
        widget_id_to_delete = getattr(button_instance, 'widget_id_to_delete', None)
        if not widget_id_to_delete:
            return

        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text='Are you sure you want to delete this widget?'))

        buttons_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height='48dp')

        confirm_btn = Button(text='Yes, Delete')
        # Note: binding is done after popup creation to pass popup instance

        cancel_btn = Button(text='No, Cancel')

        buttons_layout.add_widget(confirm_btn)
        buttons_layout.add_widget(cancel_btn)
        content.add_widget(buttons_layout)

        confirmation_popup = Popup(title='Confirm Deletion',
                                   content=content,
                                   size_hint=(0.6, 0.3),
                                   auto_dismiss=False)

        confirm_btn.bind(on_press=lambda x: self._execute_deletion(widget_id_to_delete, confirmation_popup))
        cancel_btn.bind(on_press=confirmation_popup.dismiss)

        confirmation_popup.open()

    def _execute_deletion(self, widget_id_to_delete, popup_instance):
        self.delete_widget(widget_id_to_delete)
        popup_instance.dismiss()

    def delete_widget(self, widget_id_to_delete):
        widget_to_remove = None
        for widget_in_layout in self.content_layout.children:
            if getattr(widget_in_layout, 'widget_id', None) == widget_id_to_delete:
                widget_to_remove = widget_in_layout
                break

        if widget_to_remove:
            self.content_layout.remove_widget(widget_to_remove)
            app = App.get_running_app()
            if app:
                app.save_screens()

            if self.edit_popup and self.popup_widget_list_layout:
                self.refresh_popup_widget_list()
        else:
            print(f"Widget with ID {widget_id_to_delete} not found for deletion.")

    def on_action_type_change(self, spinner_instance, selected_action_type):
        # Ensure these widgets exist in the popup's ids before accessing
        if not self.edit_popup or not hasattr(self.edit_popup, 'ids'):
            return

        target_spinner = self.edit_popup.ids.get('target_screen_spinner')
        message_input = self.edit_popup.ids.get('popup_message_input')

        if not target_spinner or not message_input:
            print("DEBUG: Action config UI elements not found in popup ids.")
            return
            
        app = App.get_running_app()
        
        if selected_action_type == 'Navigate to Screen':
            target_spinner.disabled = False
            target_spinner.opacity = 1
            if app and app.sm:
                 # Filter out the current screen from navigation targets for usability
                current_screen_name = self.name 
                target_spinner.values = [name for name in app.sm.screen_names if name != current_screen_name]
            else:
                target_spinner.values = []
            message_input.disabled = True
            message_input.opacity = 0
        elif selected_action_type == 'Show Popup Message':
            target_spinner.disabled = True
            target_spinner.opacity = 0
            message_input.disabled = False
            message_input.opacity = 1
        else: # 'None' or other
            target_spinner.disabled = True
            target_spinner.opacity = 0
            message_input.disabled = True
            message_input.opacity = 0


    def edit_screen_popup(self, instance):
        if self.edit_popup: 
            self.edit_popup.open()
            return

        popup_main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10) # Reduced spacing a bit
        self.edit_popup = ModalView(size_hint=(0.8, 0.8), auto_dismiss=True, ids={}) # Made popup larger, added ids
        self.edit_popup.add_widget(popup_main_layout)
        self.edit_popup.bind(on_dismiss=self.reset_edit_popup_flag)

        # Section 1: Background Color
        bg_color_section = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height="200dp") 
        bg_color_section.add_widget(Label(text='Edit Screen Background', size_hint_y=None, height=30))
        colors = ["Red", "Green", "Blue", "White", "Gray"]
        for color_name in colors:
            color_button = Button(text=color_name, size_hint_y=None, height=30)
            color_button.bind(on_press=lambda btn, name=color_name: self.set_screen_background_color(color_name=name))
            bg_color_section.add_widget(color_button)
        popup_main_layout.add_widget(bg_color_section)
        
        # Section 2: Add Widget
        add_widget_main_section = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height="280dp") # Increased height
        add_widget_main_section.add_widget(Label(text='Add Widget', size_hint_y=None, height=30))
        
        self.widget_text_input = TextInput(hint_text='Enter widget text (Label or Button)', multiline=False, size_hint_y=None, height=40)
        add_widget_main_section.add_widget(self.widget_text_input)

        # Action Configuration UI (initially mostly hidden, shown for buttons)
        action_config_layout = BoxLayout(orientation='vertical', spacing=3, size_hint_y=None)
        action_config_layout.add_widget(Label(text='Button Action (Optional)', size_hint_y=None, height=25))
        
        self.action_type_spinner = Spinner(text='None', values=('None', 'Navigate to Screen', 'Show Popup Message'), size_hint_y=None, height=40)
        self.action_type_spinner.bind(text=self.on_action_type_change)
        action_config_layout.add_widget(self.action_type_spinner)
        self.edit_popup.ids['action_type_spinner'] = self.action_type_spinner


        self.target_screen_spinner = Spinner(text='Target Screen', values=[], size_hint_y=None, height=40, disabled=True, opacity=0)
        action_config_layout.add_widget(self.target_screen_spinner)
        self.edit_popup.ids['target_screen_spinner'] = self.target_screen_spinner
        
        self.popup_message_input = TextInput(hint_text='Popup message', multiline=False, size_hint_y=None, height=40, disabled=True, opacity=0)
        action_config_layout.add_widget(self.popup_message_input)
        self.edit_popup.ids['popup_message_input'] = self.popup_message_input

        add_widget_main_section.add_widget(action_config_layout) # Add the action config section

        # Buttons to add widgets
        add_buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        add_label_button = Button(text='Add Label')
        add_label_button.bind(on_press=lambda x: self.add_widget_to_screen('label'))
        add_buttons_layout.add_widget(add_label_button)

        add_button_button = Button(text='Add Button (with action)')
        add_button_button.bind(on_press=lambda x: self.add_widget_to_screen('button'))
        add_buttons_layout.add_widget(add_button_button)
        add_widget_main_section.add_widget(add_buttons_layout)
        
        popup_main_layout.add_widget(add_widget_main_section)

        # Manage Widgets Section
        manage_widgets_section = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height="150dp")
        manage_widgets_section.add_widget(Label(text='Manage Widgets', size_hint_y=None, height='30dp'))

        widget_scroll_view = ScrollView(size_hint=(1, 1))

        self.popup_widget_list_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.popup_widget_list_layout.bind(minimum_height=self.popup_widget_list_layout.setter('height'))
        widget_scroll_view.add_widget(self.popup_widget_list_layout)

        manage_widgets_section.add_widget(widget_scroll_view)
        popup_main_layout.add_widget(manage_widgets_section)

        # Section 3: Close Popup Button
        close_button = Button(text='Close Popup', size_hint_y=None, height=40)
        close_button.bind(on_press=lambda x: self.edit_popup.dismiss() if self.edit_popup else None)
        popup_main_layout.add_widget(close_button)
        
        self.on_action_type_change(self.action_type_spinner, self.action_type_spinner.text) # Initial setup of visibility
        self.refresh_popup_widget_list()
        self.edit_popup.open()

    def reset_edit_popup_flag(self, instance):
        self.edit_popup = None
        self.widget_text_input = None 
        self.action_type_spinner = None
        self.target_screen_spinner = None
        self.popup_message_input = None
        self.popup_widget_list_layout = None


    def set_screen_background_color(self, color_name=None, rgba=None, from_load=False, *args):
        app = App.get_running_app()
        if rgba: 
            self.bg_color.rgba = list(rgba) 
        elif color_name: 
            colors = {
                "Red": (1, 0, 0, 1), "Green": (0, 1, 0, 1), "Blue": (0, 0, 1, 1),
                "White": (1, 1, 1, 1), "Gray": (0.5, 0.5, 0.5, 1)
            }
            if color_name in colors:
                self.bg_color.rgba = list(colors[color_name])
        
        if hasattr(self, 'edit_popup') and self.edit_popup and color_name: 
            self.edit_popup.dismiss() # Dismiss only if a color button in popup was pressed
        
        if not from_load and app and app.sm and hasattr(app, 'save_screens') and app.sm.has_screen('home'): 
             app.save_screens()

    def go_back_home(self, instance):
        self.manager.current = 'home'


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        main_layout = BoxLayout(orientation='vertical')

        top_controls_layout = BoxLayout(orientation='vertical', size_hint_y=None, height='96dp', spacing=5, padding=5)
        top_controls_layout.add_widget(Label(text='Home Screen', size_hint_y=None, height='40dp'))
        create_screen_button = Button(text='Create New Screen', size_hint_y=None, height='48dp')
        create_screen_button.bind(on_press=self.add_new_screen_interactive)
        top_controls_layout.add_widget(create_screen_button)
        main_layout.add_widget(top_controls_layout)

        scroll_view = ScrollView(size_hint=(1, 1)) 
        self.screen_list_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.screen_list_layout.bind(minimum_height=self.screen_list_layout.setter('height'))
        scroll_view.add_widget(self.screen_list_layout)
        main_layout.add_widget(scroll_view)
        
        self.add_widget(main_layout)

    def _create_screen_entry_widget(self, screen_name):
        screen_entry_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='48dp', spacing=10)
        screen_button = Button(text=screen_name, size_hint_x=0.8) # Navigation button
        screen_button.bind(on_press=lambda x, name=screen_name: self.go_to_screen(name))
        screen_entry_layout.add_widget(screen_button)
        delete_screen_button = Button(text='Delete', size_hint_x=0.2) # Delete button
        delete_screen_button.screen_name_to_delete = screen_name
        delete_screen_button.bind(on_press=self.confirm_delete_screen)
        screen_entry_layout.add_widget(delete_screen_button)
        return screen_entry_layout

    def confirm_delete_screen(self, button_instance):
        screen_name_to_delete = getattr(button_instance, 'screen_name_to_delete', None)
        if not screen_name_to_delete:
            return

        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        message = f"Are you sure you want to delete screen '{screen_name_to_delete}'?\n\nThis may affect buttons on other screens that navigate to it."
        content.add_widget(Label(text=message))

        buttons_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height='48dp')

        confirm_btn = Button(text='Yes, Delete Screen')

        cancel_btn = Button(text='No, Cancel')

        buttons_layout.add_widget(confirm_btn)
        buttons_layout.add_widget(cancel_btn)
        content.add_widget(buttons_layout)

        confirmation_popup = Popup(title='Confirm Screen Deletion',
                                   content=content,
                                   size_hint=(0.7, 0.4),
                                   auto_dismiss=False)

        confirm_btn.bind(on_press=lambda x: self._execute_screen_deletion(screen_name_to_delete, confirmation_popup))
        cancel_btn.bind(on_press=confirmation_popup.dismiss)

        confirmation_popup.open()

    def _execute_screen_deletion(self, screen_name_to_delete, popup_instance):
        self.delete_screen(screen_name_to_delete)
        popup_instance.dismiss()

    def delete_screen(self, screen_name_to_delete):
        app = App.get_running_app()
        if not app or not app.sm: return

        if app.sm.has_screen(screen_name_to_delete):
            screen_instance = app.sm.get_screen(screen_name_to_delete)
            app.sm.remove_widget(screen_instance)

        layout_to_remove = None
        for child_layout in self.screen_list_layout.children:
            if not isinstance(child_layout, BoxLayout): continue
            for widget_in_entry in child_layout.children:
                if isinstance(widget_in_entry, Button) and getattr(widget_in_entry, 'screen_name_to_delete', None) == screen_name_to_delete:
                    layout_to_remove = child_layout
                    break
            if layout_to_remove: break
        if layout_to_remove: self.screen_list_layout.remove_widget(layout_to_remove)

        for screen in app.sm.screens:
            if isinstance(screen, DynamicScreen):
                for widget in screen.content_layout.children:
                    if isinstance(widget, Button) and hasattr(widget, 'action_config'):
                        action_conf = widget.action_config
                        if action_conf and action_conf.get('type') == 'navigate' and action_conf.get('target') == screen_name_to_delete:
                            widget.action_config = {} # Clear or update action
        app.save_screens()

    def add_new_screen_interactive(self, instance):
        app = App.get_running_app()
        app.screen_count += 1
        new_screen_name = f"DynamicScreen_{app.screen_count}"
        
        self.create_and_add_screen(new_screen_name, from_load=False)
        app.sm.current = new_screen_name

    def create_and_add_screen(self, screen_name, background_color_rgba=None, widgets_data=None, from_load=True):
        app = App.get_running_app()
        screen_instance = None
        if not app.sm.has_screen(screen_name):
            screen_instance = DynamicScreen(name=screen_name)
            app.sm.add_widget(screen_instance)
            if background_color_rgba: screen_instance.set_screen_background_color(rgba=background_color_rgba, from_load=True)
            if widgets_data:
                for widget_data in widgets_data:
                    screen_instance.add_widget_to_screen(
                        widget_data['type'], widget_text_override=widget_data['text'],
                        widget_id_override=widget_data.get('widget_id'),
                        action_config_override=widget_data.get('action_config'), from_load=True)
        else:
            screen_instance = app.sm.get_screen(screen_name)

        ui_entry_exists = False
        for layout_entry in self.screen_list_layout.children:
            if not isinstance(layout_entry, BoxLayout): continue
            for child_widget in layout_entry.children:
                if isinstance(child_widget, Button) and child_widget.text == screen_name and child_widget.size_hint_x == 0.8: # Check nav button
                    ui_entry_exists = True; break
            if ui_entry_exists: break
        
        if not ui_entry_exists:
            screen_entry_widget = self._create_screen_entry_widget(screen_name)
            self.screen_list_layout.add_widget(screen_entry_widget)
        
        if not from_load and app and app.sm and hasattr(app, 'save_screens'): app.save_screens()
        return screen_instance

    def go_to_screen(self, screen_name, instance=None): 
        app = App.get_running_app()
        app.sm.current = screen_name


class MainApp(App):
    def __init__(self, **kwargs):
        super(MainApp, self).__init__(**kwargs)
        self.screen_count = 0
        self.save_file = 'screens_data.json' 
        self.sm = None 

    def build(self):
        self.sm = ScreenManager() 
        home_screen = HomeScreen(name='home') 
        self.sm.add_widget(home_screen)
        self.load_screens() 
        self.sm.current = 'home'
        return self.sm

    def save_screens(self):
        if not self.sm: 
            return

        all_screens_data = []
        for screen_name in self.sm.screen_names:
            if screen_name == 'home': 
                continue
            
            screen_instance = self.sm.get_screen(screen_name)
            if not isinstance(screen_instance, DynamicScreen):
                continue

            screen_data = {
                'name': screen_instance.name,
                'background_color_rgba': list(screen_instance.bg_color.rgba), 
                'widgets': []
            }
            
            for widget in reversed(screen_instance.content_layout.children): # Iterate reversed to save in visual order
                widget_data_item = {
                    'type': '',
                    'text': '',
                    'widget_id': getattr(widget, 'widget_id', None) # Save widget_id
                }
                if isinstance(widget, Label):
                    widget_data_item['type'] = 'label'
                    widget_data_item['text'] = widget.text
                elif isinstance(widget, Button): 
                    widget_data_item['type'] = 'button'
                    widget_data_item['text'] = widget.text
                    if hasattr(widget, 'action_config'): # Save action_config for buttons
                        widget_data_item['action_config'] = widget.action_config
                else:
                    continue 
                screen_data['widgets'].append(widget_data_item)
            
            all_screens_data.append(screen_data)

        try:
            with open(self.save_file, 'w') as f:
                json.dump(all_screens_data, f, indent=4)
        except IOError as e:
            print(f"Error saving screens: {e}")

    def load_screens(self):
        if not os.path.exists(self.save_file):
            return

        if not self.sm: 
            return

        try:
            with open(self.save_file, 'r') as f:
                all_screens_data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading screens: {e}")
            return

        home_screen = self.sm.get_screen('home')
        if not home_screen: 
            print("Error: HomeScreen not found during load_screens.")
            return

        max_screen_id = 0
        for screen_data in all_screens_data:
            screen_name = screen_data['name']
            try: 
                screen_id_str = screen_name.split('_')[-1]
                if screen_id_str.isdigit():
                    screen_id = int(screen_id_str)
                    if screen_id > max_screen_id: max_screen_id = screen_id
            except (ValueError, IndexError):
                 print(f"Warning: Could not parse ID from screen name '{screen_name}' during load.")

            home_screen.create_and_add_screen(
                screen_name, background_color_rgba=screen_data.get('background_color_rgba'),
                widgets_data=screen_data.get('widgets', []), from_load=True)
        
        self.screen_count = max_screen_id

if __name__ == '__main__':
    MainApp().run()
