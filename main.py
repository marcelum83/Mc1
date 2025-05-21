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
from kivy.uix.scrollview import ScrollView # Added ScrollView import
from kivy.uix.gridlayout import GridLayout # Added GridLayout import

class DynamicScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.edit_popup = None # To store the ModalView instance
        self.widget_text_input = None # To store the TextInput from the popup

        # Main layout for the screen
        main_screen_layout = BoxLayout(orientation='vertical')

        # Top bar for controls (Edit, Back)
        controls_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='48dp')
        controls_layout.add_widget(Label(text=self.name)) # Display screen name

        edit_button = Button(text='Edit Screen')
        edit_button.bind(on_press=self.edit_screen_popup)
        controls_layout.add_widget(edit_button)

        back_button = Button(text='Go back to Home Screen')
        back_button.bind(on_press=self.go_back_home)
        controls_layout.add_widget(back_button)
        
        main_screen_layout.add_widget(controls_layout)

        # Content layout for user-added widgets
        self.content_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        main_screen_layout.add_widget(self.content_layout)
        
        self.add_widget(main_screen_layout)

        # Background setup
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

    def add_widget_to_screen(self, widget_type, *args):
        if self.widget_text_input:
            widget_text = self.widget_text_input.text
            if not widget_text.strip(): # Do nothing if text is empty or whitespace
                return

            if widget_type == 'label':
                new_widget = Label(text=widget_text, size_hint_y=None, height='40dp')
            elif widget_type == 'button':
                new_widget = Button(text=widget_text, size_hint_y=None, height='48dp')
            else:
                return # Unknown widget type

            self.content_layout.add_widget(new_widget)
            self.widget_text_input.text = "" # Clear input field
            # Keep the popup open for adding more widgets

    def edit_screen_popup(self, instance):
        if self.edit_popup: # If popup already exists, don't create another
            self.edit_popup.open()
            return

        # Main layout for the popup
        popup_main_layout = BoxLayout(orientation='vertical', padding=10, spacing=20) # Increased spacing

        # Section for background color
        bg_color_section = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height="200dp") # Fixed height
        bg_color_section.add_widget(Label(text='Edit Screen Background', size_hint_y=None, height=30))
        colors = ["Red", "Green", "Blue", "White", "Gray"]
        for color_name in colors:
            color_button = Button(text=color_name, size_hint_y=None, height=30)
            color_button.bind(on_press=lambda btn, name=color_name: self.set_screen_background_color(name))
            bg_color_section.add_widget(color_button)
        popup_main_layout.add_widget(bg_color_section)

        # Separator or more spacing could be added here if needed
        
        # Section for adding widgets
        add_widget_section = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height="180dp") # Fixed height
        add_widget_section.add_widget(Label(text='Add Widget', size_hint_y=None, height=30))
        
        self.widget_text_input = TextInput(hint_text='Enter widget text here', multiline=False, size_hint_y=None, height=40)
        add_widget_section.add_widget(self.widget_text_input)

        add_label_button = Button(text='Add Label', size_hint_y=None, height=40)
        add_label_button.bind(on_press=lambda x: self.add_widget_to_screen('label'))
        add_widget_section.add_widget(add_label_button)

        add_button_button = Button(text='Add Button', size_hint_y=None, height=40)
        add_button_button.bind(on_press=lambda x: self.add_widget_to_screen('button'))
        add_widget_section.add_widget(add_button_button)
        popup_main_layout.add_widget(add_widget_section)

        # Close button for the entire popup
        close_button = Button(text='Close Popup', size_hint_y=None, height=40)
        close_button.bind(on_press=lambda x: self.edit_popup.dismiss() if self.edit_popup else None)
        popup_main_layout.add_widget(close_button)

        self.edit_popup = ModalView(size_hint=(0.7, 0.7), auto_dismiss=True) # Made popup a bit larger
        self.edit_popup.add_widget(popup_main_layout)
        self.edit_popup.bind(on_dismiss=self.reset_edit_popup_flag)
        self.edit_popup.open()

    def reset_edit_popup_flag(self, instance):
        self.edit_popup = None
        self.widget_text_input = None # Clear reference to text input

    def set_screen_background_color(self, color_name, *args):
        colors = {
            "Red": (1, 0, 0, 1),
            "Green": (0, 1, 0, 1),
            "Blue": (0, 0, 1, 1),
            "White": (1, 1, 1, 1),
            "Gray": (0.5, 0.5, 0.5, 1)
        }
        if color_name in colors:
            self.bg_color.rgba = colors[color_name]
        if hasattr(self, 'edit_popup') and self.edit_popup:
            self.edit_popup.dismiss()
            # self.edit_popup = None # Resetting is now handled by on_dismiss of ModalView

    def go_back_home(self, instance):
        # Access the screen manager and change screen
        self.manager.current = 'home'


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        # Main layout for HomeScreen
        main_layout = BoxLayout(orientation='vertical')

        # Top section for controls
        top_controls_layout = BoxLayout(orientation='vertical', size_hint_y=None, height='96dp', spacing=5, padding=5)
        top_controls_layout.add_widget(Label(text='Home Screen', size_hint_y=None, height='40dp'))
        create_screen_button = Button(text='Create New Screen', size_hint_y=None, height='48dp')
        create_screen_button.bind(on_press=self.add_new_screen)
        top_controls_layout.add_widget(create_screen_button)
        main_layout.add_widget(top_controls_layout)

        # ScrollView for the list of dynamic screens
        scroll_view = ScrollView(size_hint=(1, 1)) # Takes remaining space
        self.screen_list_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.screen_list_layout.bind(minimum_height=self.screen_list_layout.setter('height'))
        scroll_view.add_widget(self.screen_list_layout)
        main_layout.add_widget(scroll_view)
        
        self.add_widget(main_layout)

    def add_new_screen(self, instance):
        app = App.get_running_app()
        app.screen_count += 1
        new_screen_name = f"DynamicScreen_{app.screen_count}"
        new_screen = DynamicScreen(name=new_screen_name)
        self.manager.add_widget(new_screen)
        
        # Add button to HomeScreen for this new screen
        screen_button = Button(text=new_screen.name, size_hint_y=None, height='48dp')
        screen_button.bind(on_press=lambda x, name=new_screen_name: self.go_to_screen(name))
        self.screen_list_layout.add_widget(screen_button)
        
        # Switch to the new screen
        self.manager.current = new_screen_name

    def go_to_screen(self, screen_name, instance=None): # instance is passed by button press, but screen_name is what we need
        self.manager.current = screen_name

    # go_back_home was removed from HomeScreen as it's specific to DynamicScreen now

class MainApp(App):
    def __init__(self, **kwargs):
        super(MainApp, self).__init__(**kwargs)
        self.screen_count = 0

    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.current = 'home'
        return sm

if __name__ == '__main__':
    MainApp().run()
