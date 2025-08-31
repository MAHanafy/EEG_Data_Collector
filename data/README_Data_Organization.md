# EEG Data Organization - Data_Collector Folder Structure

## Overview
The Data_Collector folder now contains two data directories with different organizational structures:

## Directory Structure

### 📁 `Data_Collector/data/` (Original Files)
- Contains original EEG data files with inconsistent naming patterns
- Files are preserved as-is for backup and reference
- **Do not modify these files** - they serve as the master backup

### 📁 `Data_Collector/data_renamed/` (Standardized Files) ⭐
- Contains standardized copies with consistent `Training_1`, `Training_2`, `Training_3` pattern
- **This is the folder used by the analysis pipeline**
- All subjects now follow the same naming convention
- Includes complete mapping documentation

## File Naming Convention

### Before (Inconsistent):
```
SUBJECT1: Training_1, Training_6, Training_7
SUBJECT3: Training_2, Training_3, Training_4  
SUBJECT4: Training_2, Training_3, Training_4
SUBJECT5: Training_3, Training_4, Training_5
SUBJECT6: Training_1, Training_2, Training_4
SUBJECT7: Training_1, Training_2, Training_3
```

### After (Consistent):
```
All Subjects: Training_1, Training_2, Training_3
SUBJECT1: Training_1, Training_2, Training_3
SUBJECT3: Training_1, Training_2, Training_3
SUBJECT4: Training_1, Training_2, Training_3
SUBJECT5: Training_1, Training_2, Training_3
SUBJECT6: Training_1, Training_2, Training_3
SUBJECT7: Training_1, Training_2, Training_3
```

## File Mapping Examples

### Detailed File Transformations:

#### 👤 SUBJECT1:
```
Original → Renamed
EXP3_SUBJECT1_Training_1_IMAGERY.npz → EXP3_SUBJECT1_Training_1_IMAGERY.npz (no change)
EXP3_SUBJECT1_Training_6_IMAGERY.npz → EXP3_SUBJECT1_Training_2_IMAGERY.npz
EXP3_SUBJECT1_Training_7_IMAGERY.npz → EXP3_SUBJECT1_Training_3_IMAGERY.npz
```

#### 👤 SUBJECT3:
```
Original → Renamed
EXP3_SUBJECT3_Training_2_IMAGERY.npz → EXP3_SUBJECT3_Training_1_IMAGERY.npz
EXP3_SUBJECT3_Training_3_IMAGERY.npz → EXP3_SUBJECT3_Training_2_IMAGERY.npz
EXP3_SUBJECT3_Training_4_IMAGERY.npz → EXP3_SUBJECT3_Training_3_IMAGERY.npz
```

#### 👤 SUBJECT4:
```
Original → Renamed
EXP3_SUBJECT4_Training_2_IMAGERY.npz → EXP3_SUBJECT4_Training_1_IMAGERY.npz
EXP3_SUBJECT4_Training_3_IMAGERY.npz → EXP3_SUBJECT4_Training_2_IMAGERY.npz
EXP3_SUBJECT4_Training_4_IMAGERY.npz → EXP3_SUBJECT4_Training_3_IMAGERY.npz
```

#### 👤 SUBJECT5:
```
Original → Renamed
EXP3_SUBJECT5_Training_3_IMAGERY.npz → EXP3_SUBJECT5_Training_1_IMAGERY.npz
EXP3_SUBJECT5_Training_4_IMAGERY.npz → EXP3_SUBJECT5_Training_2_IMAGERY.npz
EXP3_SUBJECT5_Training_5_IMAGERY.npz → EXP3_SUBJECT5_Training_3_IMAGERY.npz
```

#### 👤 SUBJECT6:
```
Original → Renamed
EXP3_SUBJECT6_Training_1_IMAGERY.npz → EXP3_SUBJECT6_Training_1_IMAGERY.npz (no change)
EXP3_SUBJECT6_Training_2_IMAGERY.npz → EXP3_SUBJECT6_Training_2_IMAGERY.npz (no change)
EXP3_SUBJECT6_Training_4_IMAGERY.npz → EXP3_SUBJECT6_Training_3_IMAGERY.npz
```

#### 👤 SUBJECT7:
```
Original → Renamed
EXP3_SUBJECT7_Training_1_IMAGERY.npz → EXP3_SUBJECT7_Training_1_IMAGERY.npz (no change)
EXP3_SUBJECT7_Training_2_IMAGERY.npz → EXP3_SUBJECT7_Training_2_IMAGERY.npz (no change)
EXP3_SUBJECT7_Training_3_IMAGERY.npz → EXP3_SUBJECT7_Training_3_IMAGERY.npz (no change)
```

## Files in data_renamed folder:

### All Subjects (18 files total):
```
EXP3_SUBJECT1_Training_1_IMAGERY.npz
EXP3_SUBJECT1_Training_2_IMAGERY.npz
EXP3_SUBJECT1_Training_3_IMAGERY.npz
EXP3_SUBJECT3_Training_1_IMAGERY.npz
EXP3_SUBJECT3_Training_2_IMAGERY.npz
EXP3_SUBJECT3_Training_3_IMAGERY.npz
EXP3_SUBJECT4_Training_1_IMAGERY.npz
EXP3_SUBJECT4_Training_2_IMAGERY.npz
EXP3_SUBJECT4_Training_3_IMAGERY.npz
EXP3_SUBJECT5_Training_1_IMAGERY.npz
EXP3_SUBJECT5_Training_2_IMAGERY.npz
EXP3_SUBJECT5_Training_3_IMAGERY.npz
EXP3_SUBJECT6_Training_1_IMAGERY.npz
EXP3_SUBJECT6_Training_2_IMAGERY.npz
EXP3_SUBJECT6_Training_3_IMAGERY.npz
EXP3_SUBJECT7_Training_1_IMAGERY.npz
EXP3_SUBJECT7_Training_2_IMAGERY.npz
EXP3_SUBJECT7_Training_3_IMAGERY.npz
```

## Documentation Files

### 📄 `file_renaming_mapping.txt`
- Complete documentation of all file mappings
- Shows which original file corresponds to each renamed file
- Includes timestamps and summary statistics
- Essential for traceability and reproducibility

## Pipeline Configuration

### Current Settings:
- **Data Source**: `Data_Collector/data_renamed/` 
- **Session Pattern**: All subjects use `Training_1`, `Training_2`, `Training_3`
- **Total Sessions per Subject**: 3
- **Total Subjects**: 6 (SUBJECT1, SUBJECT3, SUBJECT4, SUBJECT5, SUBJECT6, SUBJECT7)

### Code Changes:
1. ✅ **Pipeline updated** to use `data_renamed` folder
3. ✅ **Consistent naming** across all subjects
4. ✅ **Reproducibility maintained** with proper random seeds

## Benefits of New Structure:

1. **🎯 Consistency**: All subjects follow identical naming pattern
2. **📊 Fair Comparison**: Session 1 vs Session 1 across subjects is meaningful
3. **🔧 Simplified Code**: No complex mapping logic required
4. **📋 Clear Documentation**: Complete traceability of file origins
5. **🛡️ Safe Backup**: Original files preserved untouched
6. **🚀 Research Ready**: Clean data structure for analysis and publication

## Usage:
- The analysis pipeline automatically uses the `data_renamed` folder
- Results will now have consistent session labeling across all subjects
- Original data remains available in `data` folder if needed

---
**Generated**: August 14, 2025  
**Purpose**: Documentation for standardized EEG data organization
