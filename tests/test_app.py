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
from kivy.uix.modalview import ModalView # Added ModalView import
from kivy.clock import Clock

# Import classes from main.py
from main import MainApp, HomeScreen, DynamicScreen

# can be tricky. For now, we'll rely on each test setting up what it needs.
from unittest.mock import patch, Mock # Added Mock

class TestAppFunctionality(unittest.TestCase):

    def setUp(self):
        # Stop any previous app instance
        if App.get_running_app():
            App.get_running_app().stop()
            # Clock.unschedule_all() # Might be needed if Clock events interfere

        # Create a new app instance for each test
        self.app = MainApp()
        
        # Determine save file path and ensure it's clean before each test
        self.save_file = self.app.save_file 
        if os.path.exists(self.save_file):
            os.remove(self.save_file)

        # Manually call build to set up the screen manager and other essentials.
        # build() in main.py now calls load_screens(), which is fine for most tests.
        # For tests that need a completely clean slate before loading, we ensure the file is gone.
        self.app.build() 
        
        # Ensure after build, if save file was deleted, screen_count is also reset
        # (load_screens might modify it based on the file, but file is gone)
        self.app.screen_count = 0 


    def tearDown(self):
        # Clean up the save file after each test
        if os.path.exists(self.save_file):
            os.remove(self.save_file)
        
        # Stop the Kivy app instance
        if App.get_running_app():
            App.get_running_app().stop()
            # Clock.unschedule_all()

        # Reset MainApp class variable if it exists and was modified by tests
        # This is a bit of a guess, ideally screen_count is instance-based or managed carefully
        if hasattr(MainApp, 'screen_count'): 
             MainApp.screen_count = 0


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

    # --- Test Case Group: Save/Load Functionality ---

    def test_save_single_screen_no_widgets(self):
        home_screen = self.app.sm.get_screen('home')
        
        # 1. Create one dynamic screen
        home_screen.add_new_screen_interactive(None) # Creates DynamicScreen_1
        screen_name = "DynamicScreen_1"
        created_screen = self.app.sm.get_screen(screen_name)
        original_bg_color = list(created_screen.bg_color.rgba) # Store original color

        # 2. Call self.app.save_screens()
        self.app.save_screens()

        # 3. Assert screens_data.json is created
        self.assertTrue(os.path.exists(self.save_file), f"{self.save_file} should be created.")

        # 4. Instantiate a new MainApp (or reset the current one) and call load_screens()
        # Stop the current app to allow a new one to be "fresh"
        if App.get_running_app():
            App.get_running_app().stop()
        
        new_app = MainApp()
        # new_app.save_file should be the same as self.save_file
        new_app.build() # This calls load_screens()

        # 5. Verify the screen is loaded correctly
        self.assertTrue(new_app.sm.has_screen(screen_name), f"{screen_name} should be loaded in the new app.")
        loaded_screen = new_app.sm.get_screen(screen_name)
        self.assertIsInstance(loaded_screen, DynamicScreen, "Loaded screen should be a DynamicScreen instance.")
        self.assertEqual(list(loaded_screen.bg_color.rgba), original_bg_color, "Loaded screen background color should match original.")
        self.assertEqual(len(loaded_screen.content_layout.children), 0, "Loaded screen should have no widgets.")
        
        # Clean up new_app instance
        if App.get_running_app(): # This should be new_app
            App.get_running_app().stop()

    def test_save_load_screen_with_widgets_and_ids(self):
        home_screen = self.app.sm.get_screen('home')
        
        # 1. Create a dynamic screen
        home_screen.add_new_screen_interactive(None) # Creates DynamicScreen_1
        screen_name = "DynamicScreen_1"
        created_screen = self.app.sm.get_screen(screen_name)

        # 2. Add a label and a button to it
        # To do this programmatically without UI, we need to set widget_text_input on created_screen
        # and then call add_widget_to_screen
        created_screen.widget_text_input = TextInput(text="Test Label 1")
        created_screen.add_widget_to_screen('label') # from_load=False by default
        
        created_screen.widget_text_input = TextInput(text="Test Button 1")
        # For this test, not adding action to button yet, just the widget itself
        created_screen.action_type_spinner = Spinner(text='None') # Mock spinner for non-action button
        created_screen.add_widget_to_screen('button')

        self.assertEqual(len(created_screen.content_layout.children), 2, "Screen should have 2 widgets.")
        
        # Retrieve widget_ids - widgets are added to content_layout in reverse visual order
        # Last added (button) is at index 0, first added (label) is at index 1
        button_widget_id = created_screen.content_layout.children[0].widget_id
        label_widget_id = created_screen.content_layout.children[1].widget_id
        self.assertIsNotNone(button_widget_id)
        self.assertIsNotNone(label_widget_id)

        # 3. Call self.app.save_screens()
        self.app.save_screens()
        self.assertTrue(os.path.exists(self.save_file))

        # 4. Load into a new/reset app
        if App.get_running_app(): App.get_running_app().stop()
        new_app = MainApp()
        new_app.build() # Calls load_screens

        # 5. Verify the screen and its widgets are reloaded
        self.assertTrue(new_app.sm.has_screen(screen_name), f"{screen_name} should be loaded.")
        loaded_screen = new_app.sm.get_screen(screen_name)
        self.assertEqual(len(loaded_screen.content_layout.children), 2, "Loaded screen should have 2 widgets.")

        # Widgets are loaded in the order they are in the JSON (visual order)
        # and added to content_layout (which means visually, first in JSON is top-most)
        # content_layout.children has them in reverse order of addition/visual.
        # So, if saved as [Label, Button], loaded as [Label, Button].
        # content_layout.children[1] is Label, content_layout.children[0] is Button.
        
        loaded_label = None
        loaded_button = None

        # Find by widget_id to be sure
        for widget in loaded_screen.content_layout.children:
            if widget.widget_id == label_widget_id:
                loaded_label = widget
            elif widget.widget_id == button_widget_id:
                loaded_button = widget
        
        self.assertIsNotNone(loaded_label, "Label should be reloaded.")
        self.assertIsInstance(loaded_label, Label)
        self.assertEqual(loaded_label.text, "Test Label 1")

        self.assertIsNotNone(loaded_button, "Button should be reloaded.")
        self.assertIsInstance(loaded_button, Button)
        self.assertEqual(loaded_button.text, "Test Button 1")
        
        if App.get_running_app(): App.get_running_app().stop()

    def test_load_empty_file_or_no_file(self):
        # Case 1: No save file exists (setUp already ensures this)
        if App.get_running_app(): App.get_running_app().stop()
        new_app_no_file = MainApp()
        new_app_no_file.build() # Calls load_screens
        
        # Verify app starts normally, with only HomeScreen
        self.assertEqual(len(new_app_no_file.sm.screens), 1, "Should only have HomeScreen if no save file.")
        self.assertTrue(new_app_no_file.sm.has_screen('home'), "HomeScreen should exist.")
        self.assertEqual(new_app_no_file.screen_count, 0, "Screen count should be 0 if no file.")
        if App.get_running_app(): App.get_running_app().stop()

        # Case 2: Empty save file exists
        with open(self.save_file, 'w') as f:
            f.write("") # Create an empty file
        
        if App.get_running_app(): App.get_running_app().stop()
        new_app_empty_file = MainApp()
        new_app_empty_file.build() # Calls load_screens

        self.assertEqual(len(new_app_empty_file.sm.screens), 1, "Should only have HomeScreen if save file is empty.")
        self.assertTrue(new_app_empty_file.sm.has_screen('home'), "HomeScreen should exist for empty file case.")
        self.assertEqual(new_app_empty_file.screen_count, 0, "Screen count should be 0 if save file is empty.")
        if App.get_running_app(): App.get_running_app().stop()

        # Case 3: Save file with empty JSON array
        with open(self.save_file, 'w') as f:
            json.dump([], f)
        
        if App.get_running_app(): App.get_running_app().stop()
        new_app_empty_json = MainApp()
        new_app_empty_json.build() # Calls load_screens

        self.assertEqual(len(new_app_empty_json.sm.screens), 1, "Should only have HomeScreen if save file has empty JSON array.")
        self.assertTrue(new_app_empty_json.sm.has_screen('home'), "HomeScreen should exist for empty JSON array.")
        self.assertEqual(new_app_empty_json.screen_count, 0, "Screen count should be 0 if save file has empty JSON array.")
        if App.get_running_app(): App.get_running_app().stop()

    def test_screen_count_after_load(self):
        home_screen = self.app.sm.get_screen('home')
        
        # 1. Save a few screens
        home_screen.add_new_screen_interactive(None) # DynamicScreen_1
        home_screen.add_new_screen_interactive(None) # DynamicScreen_2
        self.assertEqual(self.app.screen_count, 2, "App screen_count should be 2 after creating two screens.")
        self.app.save_screens()

        # 2. Load them into a new app
        if App.get_running_app(): App.get_running_app().stop()
        new_app = MainApp()
        new_app.build() # Calls load_screens

        # 3. Verify self.app.screen_count is correctly set
        self.assertEqual(new_app.screen_count, 2, "Loaded app's screen_count should be 2.")

        # 4. Create a new screen interactively and check its name
        loaded_home_screen = new_app.sm.get_screen('home')
        loaded_home_screen.add_new_screen_interactive(None) 
        
        # new_app.screen_count should now be 3
        self.assertEqual(new_app.screen_count, 3, "Screen_count should be 3 after adding one more screen post-load.")
        expected_new_screen_name = "DynamicScreen_3"
        self.assertTrue(new_app.sm.has_screen(expected_new_screen_name), f"{expected_new_screen_name} should be created.")
        
        if App.get_running_app(): App.get_running_app().stop()

    # --- Test Case Group: Button Action System ---

    def test_save_load_button_with_navigate_action(self):
        home_screen = self.app.sm.get_screen('home')

        # 1. Create two dynamic screens
        home_screen.add_new_screen_interactive(None) # DynamicScreen_1
        screen1_name = "DynamicScreen_1"
        screen1 = self.app.sm.get_screen(screen1_name)

        home_screen.add_new_screen_interactive(None) # DynamicScreen_2
        screen2_name = "DynamicScreen_2"
        # screen2 = self.app.sm.get_screen(screen2_name) # Not strictly needed for this part

        # 2. On "Screen1", add a button. Configure its action to navigate to "Screen2".
        # Simulate popup UI interaction for adding the button
        screen1.widget_text_input = TextInput(text="GoToScreen2")
        screen1.action_type_spinner = Spinner(text='Navigate to Screen')
        # Populate target_screen_spinner.values as on_action_type_change would
        screen1.target_screen_spinner = Spinner(text=screen2_name, values=[s_name for s_name in self.app.sm.screen_names if s_name != screen1_name])
        screen1.popup_message_input = TextInput(text="") # Not used for navigate

        screen1.add_widget_to_screen('button') # This will read from the mocked popup elements

        self.assertEqual(len(screen1.content_layout.children), 1, "Screen1 should have one button.")
        button_on_screen1 = screen1.content_layout.children[0]
        self.assertIsInstance(button_on_screen1, Button)
        
        # 3. Ensure the button's action_config is correctly populated.
        expected_action_config = {'type': 'navigate', 'target': screen2_name}
        self.assertTrue(hasattr(button_on_screen1, 'action_config'), "Button should have action_config attribute.")
        self.assertEqual(button_on_screen1.action_config, expected_action_config, "Button action_config is incorrect.")

        # 4. Call self.app.save_screens()
        self.app.save_screens()
        self.assertTrue(os.path.exists(self.save_file))

        # 5. Load into a new/reset app
        if App.get_running_app(): App.get_running_app().stop()
        new_app = MainApp()
        new_app.build() # Calls load_screens

        # 6. Retrieve the reloaded button from "Screen1". Verify its action_config.
        self.assertTrue(new_app.sm.has_screen(screen1_name), f"{screen1_name} should be loaded.")
        loaded_screen1 = new_app.sm.get_screen(screen1_name)
        self.assertEqual(len(loaded_screen1.content_layout.children), 1, "Loaded Screen1 should have one button.")
        
        loaded_button = loaded_screen1.content_layout.children[0] # Assuming only one widget
        self.assertIsInstance(loaded_button, Button)
        self.assertTrue(hasattr(loaded_button, 'action_config'), "Loaded button should have action_config.")
        self.assertEqual(loaded_button.action_config, expected_action_config, "Loaded button's action_config is incorrect.")

        if App.get_running_app(): App.get_running_app().stop()

    def test_save_load_button_with_popup_action(self):
        home_screen = self.app.sm.get_screen('home')

        # 1. Create "Screen1"
        home_screen.add_new_screen_interactive(None) # DynamicScreen_1
        screen1_name = "DynamicScreen_1"
        screen1 = self.app.sm.get_screen(screen1_name)

        # 2. Add a button with a "Show Popup Message" action
        popup_message_text = "Hello from test!"
        screen1.widget_text_input = TextInput(text="ShowPopup")
        screen1.action_type_spinner = Spinner(text='Show Popup Message')
        screen1.target_screen_spinner = Spinner(text='Target Screen', values=[]) # Not used for popup
        screen1.popup_message_input = TextInput(text=popup_message_text) 

        screen1.add_widget_to_screen('button')

        self.assertEqual(len(screen1.content_layout.children), 1, "Screen1 should have one button.")
        button_on_screen1 = screen1.content_layout.children[0]
        
        expected_action_config = {'type': 'popup', 'message': popup_message_text}
        self.assertTrue(hasattr(button_on_screen1, 'action_config'))
        self.assertEqual(button_on_screen1.action_config, expected_action_config)

        # 3. Save and load
        self.app.save_screens()
        self.assertTrue(os.path.exists(self.save_file))

        if App.get_running_app(): App.get_running_app().stop()
        new_app = MainApp()
        new_app.build()

        # 4. Verify action_config on loaded button
        self.assertTrue(new_app.sm.has_screen(screen1_name))
        loaded_screen1 = new_app.sm.get_screen(screen1_name)
        self.assertEqual(len(loaded_screen1.content_layout.children), 1)
        
        loaded_button = loaded_screen1.content_layout.children[0]
        self.assertTrue(hasattr(loaded_button, 'action_config'))
        self.assertEqual(loaded_button.action_config, expected_action_config)

        if App.get_running_app(): App.get_running_app().stop()

    def test_execute_navigate_action(self):
        # 1. Set up two screens in the app's screen manager
        home_screen = self.app.sm.get_screen('home')
        
        # Create "TargetScreen"
        home_screen.add_new_screen_interactive(None) # Creates DynamicScreen_1
        target_screen_name = "DynamicScreen_1"
        
        # Create "SourceScreen" where the button will be
        home_screen.add_new_screen_interactive(None) # Creates DynamicScreen_2
        source_screen_name = "DynamicScreen_2"
        source_screen = self.app.sm.get_screen(source_screen_name)

        # Ensure we are not on the target screen initially for a clear test
        self.app.sm.current = source_screen_name 
        self.assertNotEqual(self.app.sm.current, target_screen_name)

        # 2. Create a button instance and set its action_config
        # We add it to source_screen's content_layout to make it part of the screen
        # This also ensures its .manager attribute is set correctly when it's part of a screen.
        
        # Simulate popup UI interaction for adding the button
        source_screen.widget_text_input = TextInput(text="NavigateButton")
        source_screen.action_type_spinner = Spinner(text='Navigate to Screen')
        source_screen.target_screen_spinner = Spinner(text=target_screen_name, values=[target_screen_name, 'home']) # Simplified values
        source_screen.popup_message_input = TextInput(text="")

        source_screen.add_widget_to_screen('button') # Adds the button
        navigate_button = source_screen.content_layout.children[0] # Get the button

        # 3. Call source_screen.execute_button_action(button_instance)
        source_screen.execute_button_action(navigate_button)

        # 4. Assert that self.app.sm.current was set to target_screen_name
        self.assertEqual(self.app.sm.current, target_screen_name, "Should have navigated to TargetScreen.")

    @patch('kivy.uix.popup.Popup.open')
    def test_execute_popup_action(self, mock_popup_open):
        # 1. Get a DynamicScreen instance
        home_screen = self.app.sm.get_screen('home')
        home_screen.add_new_screen_interactive(None) # DynamicScreen_1
        screen1_name = "DynamicScreen_1"
        screen1 = self.app.sm.get_screen(screen1_name)

        # 2. Add a button to it
        # Simulate popup UI interaction for adding the button
        screen1.widget_text_input = TextInput(text="PopupButton")
        screen1.action_type_spinner = Spinner(text='Show Popup Message')
        screen1.target_screen_spinner = Spinner(text='Target Screen', values=[]) 
        screen1.popup_message_input = TextInput(text="Test Popup Message")

        screen1.add_widget_to_screen('button') # Adds the button
        popup_button = screen1.content_layout.children[0] # Get the button

        # 3. Call screen1.execute_button_action(button_instance)
        screen1.execute_button_action(popup_button)

        # 4. Assert that Popup.open() was called
        mock_popup_open.assert_called_once()

        # Optional: Verify popup content (more involved, may need to inspect args of mock_popup_open)
        # For instance, the Popup instance is the first arg to `open` (which is `self` for the method)
        # We'd need to capture the Popup instance passed to open.
        # This can be done by `mock_popup_open.call_args[0][0]` to get the Popup instance.
        # Then check its `title` and `content` widget (e.g., a Label).
        # However, the current implementation of `execute_button_action` creates a new Popup each time.
        # So, checking the call is a good start.
        
        # To check content, we can inspect the arguments Popup was called with if we also patch Popup.__init__
        # For now, assert_called_once is the primary check.


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

    # --- Test Case Group: Widget Deletion ---
    def test_widget_deletion_logic(self):
        home_screen = self.app.sm.get_screen('home')
        home_screen.add_new_screen_interactive(None) # DynamicScreen_1
        screen_name = "DynamicScreen_1"
        dynamic_screen = self.app.sm.get_screen(screen_name)

        # Add a Label
        dynamic_screen.widget_text_input = TextInput(text="LabelToDelete")
        dynamic_screen.add_widget_to_screen('label')
        # Add a Button
        dynamic_screen.widget_text_input = TextInput(text="ButtonToKeep")
        dynamic_screen.action_type_spinner = Spinner(text='None')
        dynamic_screen.add_widget_to_screen('button')

        self.assertEqual(len(dynamic_screen.content_layout.children), 2)
        # Widgets are in order [ButtonToKeep, LabelToDelete] in content_layout.children
        label_to_delete_widget_id = dynamic_screen.content_layout.children[1].widget_id
        button_to_keep_widget_id = dynamic_screen.content_layout.children[0].widget_id

        # Call delete_widget
        dynamic_screen.delete_widget(label_to_delete_widget_id)

        # Assert widget is removed from layout
        self.assertEqual(len(dynamic_screen.content_layout.children), 1)
        remaining_widget = dynamic_screen.content_layout.children[0]
        self.assertEqual(remaining_widget.widget_id, button_to_keep_widget_id)
        self.assertIsInstance(remaining_widget, Button)

        # Assert save_screens was effective
        # delete_widget calls app.save_screens()
        if App.get_running_app(): App.get_running_app().stop()
        new_app = MainApp()
        new_app.build() # This calls load_screens()

        self.assertTrue(new_app.sm.has_screen(screen_name))
        reloaded_screen = new_app.sm.get_screen(screen_name)
        self.assertEqual(len(reloaded_screen.content_layout.children), 1)
        reloaded_remaining_widget = reloaded_screen.content_layout.children[0]
        self.assertEqual(reloaded_remaining_widget.widget_id, button_to_keep_widget_id)
        self.assertIsInstance(reloaded_remaining_widget, Button)

        widget_ids_in_reloaded_screen = [w.widget_id for w in reloaded_screen.content_layout.children]
        self.assertNotIn(label_to_delete_widget_id, widget_ids_in_reloaded_screen)

        if App.get_running_app(): App.get_running_app().stop()

    @patch('kivy.uix.popup.Popup.open')
    @patch.object(DynamicScreen, 'delete_widget') # Mock the actual deletion for this test
    def test_widget_deletion_confirmation_popup_interaction(self, mock_delete_widget, mock_popup_open):
        home_screen = self.app.sm.get_screen('home')
        home_screen.add_new_screen_interactive(None)
        screen_name = "DynamicScreen_1"
        dynamic_screen = self.app.sm.get_screen(screen_name)

        dynamic_screen.widget_text_input = TextInput(text="TestWidget")
        dynamic_screen.add_widget_to_screen('label')
        widget_id_to_delete = dynamic_screen.content_layout.children[0].widget_id

        mock_button_instance = Mock()
        mock_button_instance.widget_id_to_delete = widget_id_to_delete

        # Call confirm_delete_widget
        dynamic_screen.confirm_delete_widget(mock_button_instance)
        mock_popup_open.assert_called_once() # Popup should open

        # Simulate "Yes" click by calling _execute_deletion
        # The lambda in confirm_delete_widget binds to _execute_deletion with (widget_id, popup_instance)
        # We need to capture the popup instance or pass a mock.
        # The actual popup instance is created within confirm_delete_widget.
        # For simplicity, we call _execute_deletion directly as the lambda would.
        mock_created_popup = Mock() # This mock represents the popup passed to _execute_deletion
        dynamic_screen._execute_deletion(widget_id_to_delete, mock_created_popup)

        mock_delete_widget.assert_called_once_with(widget_id_to_delete)
        mock_created_popup.dismiss.assert_called_once()

        # Simulate "No" click (simplified)
        mock_delete_widget.reset_mock()
        mock_popup_open.reset_mock()
        # Call confirm_delete_widget again
        dynamic_screen.confirm_delete_widget(mock_button_instance)
        mock_popup_open.assert_called_once()
        # If "No" is clicked, only popup.dismiss() is called. _execute_deletion is not.
        # So, delete_widget should not be called again.
        mock_delete_widget.assert_not_called()

    # --- Test Case Group: Screen Deletion ---
    def test_screen_deletion_logic(self):
        home_screen = self.app.sm.get_screen('home')

        # Add two screens
        home_screen.add_new_screen_interactive(None) # DynamicScreen_1
        screen_a_name = "DynamicScreen_1"
        screen_a = self.app.sm.get_screen(screen_a_name)

        home_screen.add_new_screen_interactive(None) # DynamicScreen_2
        screen_b_name = "DynamicScreen_2"
        # screen_b = self.app.sm.get_screen(screen_b_name)

        # On ScreenA, add a button that navigates to ScreenB
        screen_a.widget_text_input = TextInput(text="GoToB")
        screen_a.action_type_spinner = Spinner(text='Navigate to Screen')
        screen_a.target_screen_spinner = Spinner(text=screen_b_name, values=[s_name for s_name in self.app.sm.screen_names if s_name != screen_a_name])
        screen_a.popup_message_input = TextInput(text="")
        screen_a.add_widget_to_screen('button')
        nav_button_on_a = screen_a.content_layout.children[0]
        self.assertEqual(nav_button_on_a.action_config, {'type': 'navigate', 'target': screen_b_name})

        # Call delete_screen for ScreenB
        home_screen.delete_screen(screen_b_name)

        # Assert ScreenB is gone from ScreenManager
        self.assertFalse(self.app.sm.has_screen(screen_b_name))
        self.assertNotIn(screen_b_name, self.app.sm.screen_names)

        # Assert UI entry for ScreenB is removed from HomeScreen's list
        screen_b_entry_found = False
        for child_layout in home_screen.screen_list_layout.children:
            if isinstance(child_layout, BoxLayout): # Each entry is a BoxLayout
                for widget_in_entry in child_layout.children:
                    # Check the delete button's screen_name_to_delete or nav button's text
                    if isinstance(widget_in_entry, Button) and getattr(widget_in_entry, 'screen_name_to_delete', None) == screen_b_name:
                        screen_b_entry_found = True
                        break
            if screen_b_entry_found: break
        self.assertFalse(screen_b_entry_found, "UI entry for ScreenB should be removed from HomeScreen.")

        # Assert ScreenA's button action_config is cleared
        self.assertEqual(nav_button_on_a.action_config, {}, "Nav button's action_config should be cleared.")

        # Assert save_screens was effective
        # delete_screen calls app.save_screens()
        if App.get_running_app(): App.get_running_app().stop()
        new_app = MainApp()
        new_app.build()

        self.assertFalse(new_app.sm.has_screen(screen_b_name), "ScreenB should not exist in reloaded app.")
        self.assertTrue(new_app.sm.has_screen(screen_a_name))
        reloaded_screen_a = new_app.sm.get_screen(screen_a_name)
        self.assertEqual(len(reloaded_screen_a.content_layout.children), 1) # Assuming only nav button was there
        reloaded_nav_button = reloaded_screen_a.content_layout.children[0]
        self.assertEqual(reloaded_nav_button.action_config, {}, "Reloaded nav button's action_config should be cleared.")

        if App.get_running_app(): App.get_running_app().stop()

    @patch('kivy.uix.popup.Popup.open')
    @patch.object(HomeScreen, 'delete_screen') # Mock the actual deletion for this test
    def test_screen_deletion_confirmation_popup_interaction(self, mock_delete_screen, mock_popup_open):
        home_screen = self.app.sm.get_screen('home')
        home_screen.add_new_screen_interactive(None) # DynamicScreen_1
        screen_name_to_delete = "DynamicScreen_1"

        # Need a mock button instance that would be part of the screen list layout
        mock_button_instance = Mock()
        mock_button_instance.screen_name_to_delete = screen_name_to_delete

        # Call confirm_delete_screen
        home_screen.confirm_delete_screen(mock_button_instance)
        mock_popup_open.assert_called_once() # Popup should open

        # Simulate "Yes" click by calling _execute_screen_deletion
        mock_created_popup = Mock()
        home_screen._execute_screen_deletion(screen_name_to_delete, mock_created_popup)

        mock_delete_screen.assert_called_once_with(screen_name_to_delete)
        mock_created_popup.dismiss.assert_called_once()

        # Simulate "No" click (simplified)
        mock_delete_screen.reset_mock()
        mock_popup_open.reset_mock()
        home_screen.confirm_delete_screen(mock_button_instance)
        mock_popup_open.assert_called_once()
        mock_delete_screen.assert_not_called()

    @patch('kivy.uix.popup.Popup.open') # Mock general popup openings if they interfere
    @patch('main.App.get_running_app') # Mock get_running_app
    def test_edit_screen_popup_instantiation_and_open(self, mock_get_running_app, mock_popup_open_generic):
        # Setup a mock app instance that get_running_app will return
        mock_app_instance = Mock(spec=App)
        mock_app_instance.sm = self.app.sm
        mock_app_instance.save_screens = Mock()
        mock_get_running_app.return_value = mock_app_instance

        home_screen = self.app.sm.get_screen('home')
        home_screen.add_new_screen_interactive(None)
        dynamic_screen = self.app.sm.get_screen("DynamicScreen_1")
        self.assertIsNotNone(dynamic_screen)

        self.assertIsNone(dynamic_screen.edit_popup)

        mock_trigger_button = Mock()
        try:
            dynamic_screen.edit_screen_popup(mock_trigger_button)
        except Exception as e:
            self.fail(f"edit_screen_popup raised an exception: {e}")

        self.assertIsNotNone(dynamic_screen.edit_popup, "edit_popup was not created.")
        self.assertIsInstance(dynamic_screen.edit_popup, ModalView, "edit_popup is not a ModalView instance.")

        # Check if specific widgets that are set up in the popup exist
        self.assertIsNotNone(dynamic_screen.widget_text_input, "widget_text_input should be instantiated by edit_screen_popup.")
        self.assertIsNotNone(dynamic_screen.action_type_spinner, "action_type_spinner should be instantiated.")
        self.assertIsNotNone(dynamic_screen.target_screen_spinner, "target_screen_spinner should be instantiated.")
        self.assertIsNotNone(dynamic_screen.popup_message_input, "popup_message_input should be instantiated.")
        self.assertIsNotNone(dynamic_screen.popup_widget_list_layout, "popup_widget_list_layout should be instantiated.")


        if dynamic_screen.edit_popup:
            # Manually call dismiss to trigger the on_dismiss binding
            dynamic_screen.edit_popup.dismiss()
            # reset_edit_popup_flag should have been called, resetting instance variables
            self.assertIsNone(dynamic_screen.widget_text_input, "widget_text_input should be None after popup dismiss.")
            self.assertIsNone(dynamic_screen.action_type_spinner, "action_type_spinner should be None after popup dismiss.")
            self.assertIsNone(dynamic_screen.target_screen_spinner, "target_screen_spinner should be None after popup dismiss.")
            self.assertIsNone(dynamic_screen.popup_message_input, "popup_message_input should be None after popup dismiss.")
            self.assertIsNone(dynamic_screen.popup_widget_list_layout, "popup_widget_list_layout should be None after popup dismiss.")
            # edit_popup itself is set to None by reset_edit_popup_flag
            self.assertIsNone(dynamic_screen.edit_popup, "edit_popup should be None after its own dismissal.")


if __name__ == '__main__':
    unittest.main()
