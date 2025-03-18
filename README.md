# Document Text Replacer

A desktop application that replaces keywords in Word documents with user-provided text.

## Setup Instructions

1. Install Python 3.8 or higher if not already installed
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Building the Executable

1. Run the build script:
   ```
   python build.py
   ```
2. The executable will be created in the `dist` folder as `DocReplacer.exe`

## Using the Application

1. Launch `DocReplacer.exe`
2. Fill in all the required fields in the form
3. Click "Process Documents" to replace keywords in all Word documents in the specified directory
4. The application will process all .docx files in the Extras folder and replace the keywords with your input

## Keywords

The application replaces the following keywords:
- *ADD C&N* - Client Name
- *ADD S&D* - Project Name
- *ADD P&R* - Procurement Reference No
- *ADD DD* - Bid Closing Date
- *ADD P&B* - P.O Box / Private Bag
- *ADD L* - Delivery Address
- *ADD T* - Town
- *ADD V&P* - Price Validity

## Notes

- All fields must be filled before processing
- The application will modify the original documents, so make sure to have backups
- The application processes all .docx files in the specified directory 