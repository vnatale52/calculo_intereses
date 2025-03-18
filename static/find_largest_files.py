import os
import openpyxl
from openpyxl.styles import Font

def get_largest_files(drive, top_n):
    # Dictionary to store file paths and their sizes
    files_dict = {}

    # Traverse the directory structure
    for root, dirs, files in os.walk(f"{drive}:\\"):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Get file size
                file_size = os.path.getsize(file_path)
                files_dict[file_path] = file_size
            except FileNotFoundError:
                print(f"Error: File not found - {file_path}")
            except PermissionError:
                print(f"Error: Permission denied - {file_path}")
            except OSError as e:
                print(f"Error: {e} - {file_path}")

    # Sort files by size in descending order
    sorted_files = sorted(files_dict.items(), key=lambda x: x[1], reverse=True)

    # Select the top N files
    largest_files = sorted_files[:top_n]

    return largest_files

def save_to_excel(largest_files, drive_letter, top_n):
    # Create a new workbook and select the active worksheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Largest Files"

    # Add headers
    sheet["A1"] = "Rank"
    sheet["B1"] = "File Path"
    sheet["C1"] = "Size (MB)"
    
    # Format headers
    for cell in sheet["1:1"]:
        cell.font = Font(bold=True)

    # Add data rows
    for i, (file_path, file_size) in enumerate(largest_files, start=2):
        sheet[f"A{i}"] = i - 1
        sheet[f"B{i}"] = file_path
        sheet[f"C{i}"] = file_size / (1024 * 1024)

    # Auto-adjust column widths
    for column in sheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        sheet.column_dimensions[column_letter].width = adjusted_width

    # Save the workbook
    excel_file_name = f"largest_files_on_drive_{drive_letter}.xlsx"
    workbook.save(excel_file_name)
    print(f"\nExcel file '{excel_file_name}' created successfully.")

def main():
    # Get user input for drive letter and number of files
    drive_letter = input("Enter the drive letter (e.g., C, D, E): ").upper()
    top_n = int(input("Enter the number of largest files to find: "))

    # Validate the drive letter
    if not drive_letter.isalpha() or len(drive_letter) != 1:
        print("Invalid drive letter. Please enter a single letter (A-Z).")
        return

    # Get the largest files
    largest_files = get_largest_files(drive_letter, top_n)

    # Save the results to an Excel file
    if not largest_files:
        print("No files found or accessible on the specified drive.")
    else:
        save_to_excel(largest_files, drive_letter, top_n)

    # End of execution message
    print("\nExecution ended. Thank you for using the program!")

if __name__ == "__main__":
    main()