import os
from PIL import Image

def png_to_ico(png_path, ico_path, sizes=None):
    """
    Convert a PNG image to ICO format with multiple resolutions
    
    Args:
        png_path (str): Path to the source PNG file
        ico_path (str): Path to save the output ICO file
        sizes (list): List of sizes to include in the ICO file (default is Windows standard sizes)
    """
    if sizes is None:
        # Standard Windows icon sizes
        sizes = [16, 24, 32, 48, 64, 128, 256]
    
    try:
        img = Image.open(png_path)
        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            # Paste the image on the background
            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            img = background
        
        # Resize to all required sizes
        img_list = []
        for size in sizes:
            resized_img = img.resize((size, size), Image.LANCZOS)
            img_list.append(resized_img)
        
        # Save as ICO
        img_list[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in img_list])
        return True
    except Exception as e:
        print(f"Error converting PNG to ICO: {e}")
        return False

if __name__ == "__main__":
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(base_dir, 'public', 'assets', 'twinrain-logo.png')
    ico_path = os.path.join(base_dir, 'public', 'assets', 'twinrain-logo.ico')
    
    # Ensure assets directory exists
    assets_dir = os.path.dirname(ico_path)
    os.makedirs(assets_dir, exist_ok=True)
    
    print(f"Converting {png_path} to {ico_path}...")
    if png_to_ico(png_path, ico_path):
        print(f"Successfully created icon at {ico_path}")
    else:
        print("Failed to create icon") 