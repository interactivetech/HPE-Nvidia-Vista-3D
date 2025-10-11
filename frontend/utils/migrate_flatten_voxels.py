#!/usr/bin/env python3
"""
Migration Script: Flatten Voxel Folder Structure

This script migrates existing voxel data from the old structure:
  output/patient/voxels/scan_name/original/*.nii.gz
  
To the new flat structure:
  output/patient/voxels/scan_name/*.nii.gz

Usage:
  python migrate_flatten_voxels.py [--dry-run] [--verbose]
  
Options:
  --dry-run   Show what would be done without making changes
  --verbose   Show detailed progress information
"""

import os
import shutil
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_output_folder():
    """Get the output folder from environment variables."""
    output_folder = os.getenv('OUTPUT_FOLDER')
    if not output_folder:
        raise ValueError("OUTPUT_FOLDER must be set in .env file")
    if not os.path.isabs(output_folder):
        raise ValueError("OUTPUT_FOLDER must be an absolute path")
    return Path(output_folder)


def migrate_voxel_folder(scan_voxels_path: Path, dry_run: bool = False, verbose: bool = False):
    """
    Migrate a single scan's voxel folder from the old to new structure.
    
    Args:
        scan_voxels_path: Path to the scan's voxel folder (e.g., output/patient/voxels/scan_name)
        dry_run: If True, only show what would be done
        verbose: If True, show detailed progress
    
    Returns:
        Tuple of (files_moved, folders_removed)
    """
    original_subfolder = scan_voxels_path / "original"
    
    if not original_subfolder.exists() or not original_subfolder.is_dir():
        return 0, 0
    
    files_moved = 0
    folders_removed = 0
    
    # Get all .nii.gz files in the original subfolder
    nii_files = list(original_subfolder.glob("*.nii.gz"))
    
    if not nii_files:
        if verbose:
            print(f"  No .nii.gz files found in {original_subfolder}")
        # Remove empty original folder
        if not dry_run:
            try:
                original_subfolder.rmdir()
                folders_removed = 1
                if verbose:
                    print(f"  Removed empty folder: {original_subfolder}")
            except Exception as e:
                print(f"  Warning: Could not remove empty folder {original_subfolder}: {e}")
        else:
            if verbose:
                print(f"  [DRY RUN] Would remove empty folder: {original_subfolder}")
            folders_removed = 1
        return files_moved, folders_removed
    
    # Move each file up one level
    for nii_file in nii_files:
        destination = scan_voxels_path / nii_file.name
        
        if destination.exists():
            if verbose:
                print(f"  Skipping {nii_file.name} - already exists at destination")
            continue
        
        if not dry_run:
            try:
                shutil.move(str(nii_file), str(destination))
                files_moved += 1
                if verbose:
                    print(f"  Moved: {nii_file.name}")
            except Exception as e:
                print(f"  Error moving {nii_file.name}: {e}")
        else:
            if verbose:
                print(f"  [DRY RUN] Would move: {nii_file.name}")
            files_moved += 1
    
    # Remove the now-empty original subfolder
    if not dry_run:
        try:
            # Check if folder is empty
            remaining_files = list(original_subfolder.iterdir())
            if not remaining_files:
                original_subfolder.rmdir()
                folders_removed = 1
                if verbose:
                    print(f"  Removed folder: {original_subfolder}")
            else:
                print(f"  Warning: Folder not empty after migration: {original_subfolder}")
                print(f"  Remaining files: {[f.name for f in remaining_files]}")
        except Exception as e:
            print(f"  Warning: Could not remove folder {original_subfolder}: {e}")
    else:
        if verbose:
            print(f"  [DRY RUN] Would remove folder: {original_subfolder}")
        folders_removed = 1
    
    return files_moved, folders_removed


def migrate_patient_voxels(patient_path: Path, dry_run: bool = False, verbose: bool = False):
    """
    Migrate all voxel folders for a single patient.
    
    Args:
        patient_path: Path to the patient folder (e.g., output/patient_id)
        dry_run: If True, only show what would be done
        verbose: If True, show detailed progress
    
    Returns:
        Tuple of (files_moved, folders_removed)
    """
    voxels_path = patient_path / "voxels"
    
    if not voxels_path.exists() or not voxels_path.is_dir():
        return 0, 0
    
    total_files_moved = 0
    total_folders_removed = 0
    
    # Iterate through all scan folders in the voxels directory
    for scan_folder in voxels_path.iterdir():
        if not scan_folder.is_dir():
            continue
        
        if verbose:
            print(f"\n  Processing scan: {scan_folder.name}")
        
        files_moved, folders_removed = migrate_voxel_folder(scan_folder, dry_run, verbose)
        total_files_moved += files_moved
        total_folders_removed += folders_removed
    
    return total_files_moved, total_folders_removed


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate voxel folders from old structure (with 'original' subfolder) to new flat structure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress information"
    )
    
    args = parser.parse_args()
    
    try:
        output_folder = get_output_folder()
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    if not output_folder.exists():
        print(f"Error: Output folder does not exist: {output_folder}")
        return 1
    
    print("=" * 70)
    print("Voxel Folder Structure Migration")
    print("=" * 70)
    print(f"Output folder: {output_folder}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Verbose: {args.verbose}")
    print("=" * 70)
    
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
    
    # Find all patient folders
    patient_folders = [f for f in output_folder.iterdir() if f.is_dir()]
    
    if not patient_folders:
        print("\nNo patient folders found in output directory.")
        return 0
    
    print(f"\nFound {len(patient_folders)} patient folder(s)")
    
    total_files_moved = 0
    total_folders_removed = 0
    patients_migrated = 0
    
    for patient_folder in patient_folders:
        if args.verbose or not args.dry_run:
            print(f"\nProcessing patient: {patient_folder.name}")
        
        files_moved, folders_removed = migrate_patient_voxels(
            patient_folder, 
            args.dry_run, 
            args.verbose
        )
        
        if files_moved > 0 or folders_removed > 0:
            patients_migrated += 1
            total_files_moved += files_moved
            total_folders_removed += folders_removed
            
            if not args.verbose:
                print(f"  {patient_folder.name}: {files_moved} files moved, {folders_removed} folders removed")
    
    # Summary
    print("\n" + "=" * 70)
    print("Migration Summary")
    print("=" * 70)
    print(f"Patients processed: {patients_migrated}")
    print(f"Files moved: {total_files_moved}")
    print(f"Folders removed: {total_folders_removed}")
    
    if args.dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made")
        print("Run without --dry-run to perform the migration")
    else:
        print("\n✅ Migration completed successfully")
    
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit(main())

