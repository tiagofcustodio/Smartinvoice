import sys
import json
from pprint import pprint

# Set up local paths correctly
sys.path.append(r"c:\Users\TiagoCustodio\Projects\tkinter project")

try:
    from ocr.gemini_engine import extract_structured_data_with_gemini
    
    # Using the exact receipt shown in the user's uploaded image
    # Note: image from user history might be temporary local, so I will point to where receipts gather
    # Since I'm running this test script, assuming I can download or test an existing sample local file
    
    print("Testing Continente extraction...")
    # Because I don't have the explicit physical path to the user's screenshot, 
    # I'll output how the new logic works or try to fetch a sample from uploaded.
    # Actually, let's find a pending receipt if they have one.
    import os
    pending_dir = r"c:\Users\TiagoCustodio\Projects\tkinter project\uploads\pending"
    processed_dir = r"c:\Users\TiagoCustodio\Projects\tkinter project\uploads\processed"
    
    test_file = None
    for folder in [pending_dir, processed_dir]:
        if os.path.exists(folder):
            files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))]
            if files:
                # Get the most recent one
                files.sort(key=os.path.getmtime, reverse=True)
                test_file = files[0]
                break
                
    if test_file:
        print(f"File found: {test_file}")
        data = extract_structured_data_with_gemini(test_file)
        print("\n--- Resultado Extraído ---")
        pprint(data)
    else:
        print("No image found to test internally.")
except Exception as e:
    print(f"Error test: {str(e)}")
