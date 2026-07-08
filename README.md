# RTCM3_Conv

## Move to this folder

```powershell
cd C:\Users\satok\Documents\researches\RTCM3_Conv\RTCM3_Conv
```

## Install convbin.exe from RTKLIB

```powershell
powershell -ExecutionPolicy Bypass -File .\install_convbin.ps1
```

## Replace existing convbin.exe

```powershell
powershell -ExecutionPolicy Bypass -File .\install_convbin.ps1 -Force
```

## Install convbin.exe from a specific RTKLIB tag

```powershell
powershell -ExecutionPolicy Bypass -File .\install_convbin.ps1 -Tag v2.4.3-b34
```

## Convert all RTCM3 files in this folder

```powershell
py -3 .\convert_rtcm3_to_rinex.py
```

or:

```powershell
.\convert_all.bat
```

## Convert a specific file

```powershell
py -3 .\convert_rtcm3_to_rinex.py --input .\raw\session_20260511_160000.rtcm3
```

## Choose output folder

```powershell
py -3 .\convert_rtcm3_to_rinex.py --input .\raw\session_20260511_160000.rtcm3 --output-dir .\rinex\session_20260511_160000
```

## Output at 1 second interval

```powershell
py -3 .\convert_rtcm3_to_rinex.py --input .\raw\session_20260511_160000.rtcm3 --interval 1
```

## Output at 30 second interval

```powershell
py -3 .\convert_rtcm3_to_rinex.py --input .\raw\session_20260511_160000.rtcm3 --interval 30
```

## Specify start and end UTC time

```powershell
py -3 .\convert_rtcm3_to_rinex.py --input .\raw\session_20260511_160000.rtcm3 --start "2026/05/11 16:00:00" --end "2026/05/11 17:00:00"
```

## Set RINEX header fields

```powershell
py -3 .\convert_rtcm3_to_rinex.py `
  --input .\raw\session_20260511_160000.rtcm3 `
  --marker TEST_STATION `
  --marker-type GEODETIC `
  --receiver "UNKNOWN" `
  --antenna "UNKNOWN NONE" `
  --antenna-delta 0 0 0 `
  --position -3939221.3856 3378071.9697 3696203.3834
```

## Show the convbin command without running it

```powershell
py -3 .\convert_rtcm3_to_rinex.py --input .\raw\session_20260511_160000.rtcm3 --dry-run
```

## Scan RTCM3 messages only

```powershell
py -3 .\convert_rtcm3_to_rinex.py --input .\raw\session_20260511_160000.rtcm3 --scan-only
```
