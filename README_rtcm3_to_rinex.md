# RTCM3 to RINEX command examples

```powershell
cd C:\Users\satok\Documents\researches\RTCM3_Conv
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
