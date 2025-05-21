import unittest
import os
import sys

# Add the parent directory to the sys.path to allow importing 'main'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

# Import classes from main.py
from main import MainApp, HomeScreen, DynamicScreen

# It's good practice to ensure Kivy's app is not already running if tests are run multiple times
# or if there's an issue with teardown. However, direct manipulation of App.get_running_app()
# can be tricky. For now, we'll rely on each test setting up what it needs.

class TestAppFunctionality(unittest.TestCase):

    def setUp(self):
        # It's crucial that main.py's "if __name__ == '__main__':" block
        # prevents app.run() when main.py is imported.
        # We will create a new app instance for some tests, or test screens in isolation.
        # Note: Kivy's App is a singleton. Running multiple app instances in tests can be problematic.
        # For now, we'll try to manage it locally or test components without a full app run where possible.
        # If App.get_running_app() exists, we should try to stop it.
        if App.get_running_app():
            App.get_running_app().stop()
        
        # Create a new app instance for tests that need it.
        # This is a simplified setup. More complex scenarios might require GraphicUnitTest.
        self.app = MainApp() # Create an instance
        self.app.build() # Manually call build to set up the screen manager etc.
                         # This internally creates self.app.sm (the ScreenManager)

    def tearDown(self):
        # Clean up any Kivy app instance if created.
        if App.get_running_app():
            App.get_running_app().stop()
        # Reset screen_count for subsequent tests if it's modified directly on MainApp class or instance
        MainApp.screen_count = 0 # Assuming screen_count might be a class variable or reset it on instance
        self.app.screen_count = 0


    def test_app_initialization(self):
        self.assertIsNotNone(self.app.sm, "ScreenManager (sm) should be initialized.")
        self.assertIsInstance(self.app.sm, ScreenManager, "sm should be an instance of ScreenManager.")
        
        home_screen = self.app.sm.get_screen('home')
        self.assertIsNotNone(home_screen, "HomeScreen should be in the ScreenManager.")
        self.assertEqual(self.app.sm.current, 'home', "HomeScreen should be the current screen.")
        self.assertIsInstance(home_screen, HomeScreen, "Screen 'home' should be an instance of HomeScreen.")
        
        # Verify HomeScreen contains the "Create New Screen" button
        # HomeScreen structure: main_layout -> top_controls_layout -> Button
        create_new_screen_button_found = False
        if home_screen.children: # main_layout
            main_layout = home_screen.children[0]
            if main_layout.children: # scroll_view, top_controls_layout
                top_controls_layout = main_layout.children[1] # top_controls_layout is added first, so it's at index 1 if main_layout.children are ordered bottom-to-top
                for widget in top_controls_layout.children:
                    if isinstance(widget, Button) and widget.text == 'Create New Screen':
                        create_new_screen_button_found = True
                        break
        self.assertTrue(create_new_screen_button_found, "HomeScreen should contain 'Create New Screen' button.")
        self.assertEqual(self.app.screen_count, 0, "Initial screen_count should be 0.")

    def test_dynamic_screen_creation(self):
        home_screen = self.app.sm.get_screen('home')
        self.assertIsNotNone(home_screen, "HomeScreen instance should exist.")

        initial_screen_count_in_manager = len(self.app.sm.screens)
        
        # Simulate clicking "Create New Screen" button
        home_screen.add_new_screen(None) # Button instance not used in method

        self.assertEqual(self.app.screen_count, 1, "App's screen_count should increment.")
        self.assertEqual(len(self.app.sm.screens), initial_screen_count_in_manager + 1, "A new screen should be added to ScreenManager.")
        
        new_screen_name = f"DynamicScreen_{self.app.screen_count}"
        self.assertEqual(self.app.sm.current, new_screen_name, f"Current screen should be {new_screen_name}.")
        
        new_screen = self.app.sm.get_screen(new_screen_name)
        self.assertIsNotNone(new_screen, f"{new_screen_name} should exist in ScreenManager.")
        self.assertIsInstance(new_screen, DynamicScreen, f"{new_screen_name} should be an instance of DynamicScreen.")

        # Verify new screen's default elements
        # DynamicScreen structure: main_screen_layout -> [controls_layout, content_layout]
        # controls_layout children: Label (name), Edit Button, Back Button
        self.assertTrue(len(new_screen.children) > 0, "DynamicScreen should have a main_layout.")
        main_screen_layout = new_screen.children[0]
        
        self.assertTrue(len(main_screen_layout.children) == 2, "DynamicScreen's main_layout should have controls and content areas.")
        controls_layout = main_screen_layout.children[1] # controls_layout is added first to main_screen_layout
        content_layout = main_screen_layout.children[0] # content_layout is added second

        self.assertIsNotNone(new_screen.content_layout, "DynamicScreen should have a content_layout.")
        self.assertEqual(new_screen.content_layout, content_layout, "content_layout attribute should match the one in hierarchy.")

        edit_button_found = False
        back_button_found = False
        for widget in controls_layout.children:
            if isinstance(widget, Button):
                if widget.text == 'Edit Screen':
                    edit_button_found = True
                elif widget.text == 'Go back to Home Screen':
                    back_button_found = True
        
        self.assertTrue(edit_button_found, "DynamicScreen should contain 'Edit Screen' button.")
        self.assertTrue(back_button_found, "DynamicScreen should contain 'Go back to Home Screen' button.")

        # Check if button for this screen was added to HomeScreen's list
        home_screen_list_button_found = False
        for widget in home_screen.screen_list_layout.children:
            if isinstance(widget, Button) and widget.text == new_screen_name:
                home_screen_list_button_found = True
                break
        self.assertTrue(home_screen_list_button_found, f"Button for {new_screen_name} should be added to HomeScreen's list.")

    def test_screen_background_color_change(self):
        # Test DynamicScreen directly for background color change
        # No need for a full app instance for this specific test
        dynamic_screen = DynamicScreen(name='TestColorScreen')
        
        # Default color is white
        self.assertEqual(dynamic_screen.bg_color.rgba, [1, 1, 1, 1], "Default background color should be white.")

        dynamic_screen.set_screen_background_color("Red")
        self.assertEqual(dynamic_screen.bg_color.rgba, [1, 0, 0, 1], "Background color should change to Red.")

        dynamic_screen.set_screen_background_color("Blue")
        self.assertEqual(dynamic_screen.bg_color.rgba, [0, 0, 1, 1], "Background color should change to Blue.")
        
        # Test with a color not in the predefined map
        dynamic_screen.set_screen_background_color("Yellow") # Assuming Yellow is not in the map
        self.assertEqual(dynamic_screen.bg_color.rgba, [0, 0, 1, 1], "Background color should remain Blue if color_name is invalid.")

        # Test that the popup is dismissed if it were open (mocking this part)
        mock_popup = unittest.mock.Mock()
        dynamic_screen.edit_popup = mock_popup
        dynamic_screen.set_screen_background_color("Green")
        self.assertEqual(dynamic_screen.bg_color.rgba, [0, 1, 0, 1], "Background color should change to Green.")
        mock_popup.dismiss.assert_called_once()
        self.assertIsNone(dynamic_screen.edit_popup, "edit_popup reference should be reset after color change.")

    def test_add_widgets_to_screen(self):
        dynamic_screen = DynamicScreen(name='TestWidgetScreen')
        
        # Simulate that the popup has been opened and the text input is available
        # In the actual app, edit_screen_popup would create this TextInput.
        # For the test, we assign a mock or a real TextInput directly.
        dynamic_screen.widget_text_input = TextInput(text="Initial Text")

        # Test adding a Label
        dynamic_screen.add_widget_to_screen('label')
        self.assertEqual(len(dynamic_screen.content_layout.children), 1, "One widget should be added to content_layout.")
        added_widget_label = dynamic_screen.content_layout.children[0]
        self.assertIsInstance(added_widget_label, Label, "Added widget should be a Label.")
        self.assertEqual(added_widget_label.text, "Initial Text", "Label text should match input.")
        self.assertEqual(dynamic_screen.widget_text_input.text, "", "TextInput should be cleared after adding Label.")

        # Test adding a Button
        dynamic_screen.widget_text_input.text = "Click Me"
        dynamic_screen.add_widget_to_screen('button')
        self.assertEqual(len(dynamic_screen.content_layout.children), 2, "Two widgets should be in content_layout now.")
        # Children are added in reverse order of visual appearance (bottom-most is index 0)
        added_widget_button = dynamic_screen.content_layout.children[0] # Most recently added
        self.assertIsInstance(added_widget_button, Button, "Second added widget should be a Button.")
        self.assertEqual(added_widget_button.text, "Click Me", "Button text should match input.")
        self.assertEqual(dynamic_screen.widget_text_input.text, "", "TextInput should be cleared after adding Button.")
        
        # Test adding with empty text
        initial_children_count = len(dynamic_screen.content_layout.children)
        dynamic_screen.widget_text_input.text = "   " # Whitespace only
        dynamic_screen.add_widget_to_screen('label')
        self.assertEqual(len(dynamic_screen.content_layout.children), initial_children_count, "No widget should be added if text is only whitespace.")
        self.assertEqual(dynamic_screen.widget_text_input.text, "   ", "TextInput should not be cleared if no widget was added.")

    def test_homescreen_navigation_to_dynamic_screen(self):
        home_screen = self.app.sm.get_screen('home')
        self.assertIsNotNone(home_screen, "HomeScreen instance should exist.")

        # 1. Create a new dynamic screen (simulates user action)
        home_screen.add_new_screen(None) # This creates "DynamicScreen_1" and adds its button to home_screen.screen_list_layout
        test_screen_name = "DynamicScreen_1"
        
        # Verify the button for navigation exists in HomeScreen's list
        nav_button_found = False
        for widget in home_screen.screen_list_layout.children:
            if isinstance(widget, Button) and widget.text == test_screen_name:
                nav_button_found = True
                break
        self.assertTrue(nav_button_found, f"Navigation button for {test_screen_name} should be in HomeScreen's list.")

        # 2. Navigate back to home screen first to ensure navigation works from home
        # (add_new_screen already switches to the new screen)
        dynamic_screen = self.app.sm.get_screen(test_screen_name)
        dynamic_screen.go_back_home(None) # Navigate back to home
        self.assertEqual(self.app.sm.current, 'home', "Should navigate back to HomeScreen.")

        # 3. Simulate clicking the navigation button on HomeScreen
        home_screen.go_to_screen(test_screen_name)
        self.assertEqual(self.app.sm.current, test_screen_name, f"Should navigate to {test_screen_name} from HomeScreen.")


if __name__ == '__main__':
    unittest.main()
