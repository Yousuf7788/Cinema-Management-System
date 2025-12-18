import sys
from PyQt6.QtWidgets import QApplication, QDoubleSpinBox, QComboBox
from screening_tab import ScreeningTab
from unittest.mock import MagicMock

# Mock classes to avoid full GUI/DB dependency
class MockDB:
    def get_halls(self):
        return [
            {'hall_id': 1, 'hall_name': 'Hall A - IMAX', 'capacity': 250},
            {'hall_id': 2, 'hall_name': 'Hall B - Standard', 'capacity': 180},
            {'hall_id': 3, 'hall_name': 'Hall C - Premium', 'capacity': 120},
            {'hall_id': 4, 'hall_name': 'Hall D - 3D', 'capacity': 200},
            {'hall_id': 5, 'hall_name': 'Hall E - VIP', 'capacity': 80}
        ]
    def get_movies(self): return [{'movie_id': 1, 'title': 'Test Movie', 'duration_minutes': 120}]
    def get_screenings(self): return []

def test_pricing_logic():
    app = QApplication(sys.argv)
    db = MockDB()
    
    # We need to patch BaseTab to avoid needing real UI file or parent
    # But ScreeningTab inherits Ui_ScreeningTab which is generated.
    # To keep it simple, we'll instantiate ScreeningTab but rely on our mocks 
    # and maybe catch setup errors or mock the setupUi.
    
    # Let's try a safer approach: just test the logic method directly if we can isolate it,
    # or create a minimal subclass that mocks the UI elements.
    
    print("Initializing test...")
    try:
        # Create minimal UI elements structure
        tab = MagicMock()
        tab.db = db
        tab.hallCombo = QComboBox()
        tab.priceInput = QDoubleSpinBox()
        
        # Populate hall combo as load_dynamic_data would
        halls = db.get_halls()
        for hall in halls:
            tab.hallCombo.addItem(hall['hall_name'], hall['hall_id'])
            
        # Bind the logic method from ScreeningTab to our mock object
        # This is a bit hacky but avoids full UI init
        # Better: Instantiate real tab but mock setupUi
        
        real_tab = ScreeningTab.__new__(ScreeningTab)
        real_tab.db = db
        real_tab.hallCombo = tab.hallCombo
        real_tab.priceInput = tab.priceInput
        
        # Test 1: IMAX
        print("Testing IMAX...")
        idx = real_tab.hallCombo.findData(1)
        real_tab.hallCombo.setCurrentIndex(idx)
        ScreeningTab.set_auto_price(real_tab) # Call unbound method with our instance
        print(f"Price for IMAX: {real_tab.priceInput.value()} (Expected: 20.0)")
        if real_tab.priceInput.value() != 20.0:
            print("FAIL")
            return
            
        # Test 2: Standard
        print("Testing Standard...")
        idx = real_tab.hallCombo.findData(2)
        real_tab.hallCombo.setCurrentIndex(idx)
        ScreeningTab.set_auto_price(real_tab)
        print(f"Price for Standard: {real_tab.priceInput.value()} (Expected: 12.0)")
        if real_tab.priceInput.value() != 12.0:
            print("FAIL")
            return

        # Test 3: Premium
        print("Testing Premium...")
        idx = real_tab.hallCombo.findData(3)
        real_tab.hallCombo.setCurrentIndex(idx)
        ScreeningTab.set_auto_price(real_tab)
        print(f"Price for Premium: {real_tab.priceInput.value()} (Expected: 18.0)")
        if real_tab.priceInput.value() != 18.0:
            print("FAIL")
            return
            
        print("ALL TESTS PASSED")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pricing_logic()
