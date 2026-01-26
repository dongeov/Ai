import os
import subprocess
from pathlib import Path
# Định nghĩa thư mục input
INPUT_FOLDER = "input_documents"  # 🎯 Thư mục input của bạn
OUTPUT_FOLDER = "markdown_output"

def convert_to_markdown(input_path, output_dir):
    """Chuyển đổi file sang Markdown"""
    input_path = Path(INPUT_FOLDER)
    output_path = Path(OUTPUT_FOLDER)
    
    # Tạo thư mục output nếu chưa tồn tại
    output_path.mkdir(exist_ok=True)
    
    print(f"🔍 Đang quét thư mục: {INPUT_FOLDER}")
    supported_formats = {
        '.pdf': 'pandoc "{input}" -f pdf -t markdown -o "{output}"',
        '.docx': 'pandoc "{input}" -f docx -t markdown -o "{output}"',
        '.txt': 'cp "{input}" "{output}"'  # Giữ nguyên format cho TXT
    }
    
    converted_files = []
    
    for file_path in input_path.rglob("*"):
        ext = file_path.suffix.lower()
        
        if ext in supported_formats:
            output_file = output_path / f"{file_path.stem}.md"
            
            if ext == '.txt':
                # Đối với TXT, chỉ cần copy hoặc convert đơn giản
                cmd = supported_formats[ext].format(
                    input=str(file_path),
                    output=str(output_file)
                )
            else:
                cmd = supported_formats[ext].format(
                    input=str(file_path),
                    output=str(output_file)
                )
            
            try:
                subprocess.run(cmd, shell=True, check=True)
                converted_files.append(output_file.name)
                print(f"✅ Đã chuyển đổi: {file_path.name} → {output_file.name}")
            except Exception as e:
                print(f"❌ Lỗi với {file_path.name}: {e}")
    
    return converted_files

# Sử dụng
if __name__ == "__main__":
    input_folder = "documents"
    output_folder = "markdown_output"
    results = convert_to_markdown(input_folder, output_folder)
    print(f"\nTổng số file đã chuyển đổi: {len(results)}")
