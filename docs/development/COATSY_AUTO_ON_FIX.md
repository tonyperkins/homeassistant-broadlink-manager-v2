# Fan Auto-On Fix for Coatsy

## Your Question

> "I'm not sure if this is the intended function, but for the fans I've tested setting up straight through smartIR, they turn on when I set a speed, and off when I click off. However, with this one setup with the Broadlink manager, I have to turn it on before I can set a speed, and when I click off, it shows on, and I have to actually turn it off."

**Answer**: This was **NOT** the intended behavior! You found another bug. 🎯

## The Problem

**SmartIR fans** (expected behavior):
- Click "Low" → Fan turns on at low speed ✅
- Click "Off" → Fan turns off ✅

**Broadlink Manager fans** (buggy behavior):
- Click "Low" → Fan runs at low speed but shows as "off" ❌
- Must manually click power button to show "on" ❌
- Click "Off" → Shows "on", must click power again ❌

## Root Cause

The `set_percentage` action (what happens when you click a speed button) was:
1. ✅ Sending the IR/RF command to the fan
2. ✅ Updating the speed helper
3. ❌ **NOT** updating the on/off state

So the fan was physically running, but Home Assistant thought it was still "off".

## The Fix

Added automatic state management to `set_percentage`:
- **When you set speed > 0%** → Automatically turns state to "on"
- **When you set speed = 0%** → Automatically turns state to "off"

Now it works exactly like SmartIR fans!

## What Changed

**Before**:
```
User clicks "Low" (33%)
  → Send speed_low command ✅
  → Update speed to "1" ✅
  → State stays "off" ❌
  → Fan UI shows "off" even though fan is running
```

**After**:
```
User clicks "Low" (33%)
  → Send speed_low command ✅
  → Update speed to "1" ✅
  → Update state to "on" ✅
  → Fan UI shows "on" correctly
```

## Release: v0.3.0-alpha.23

This fix is included in the new release along with your previous speed fix.

**GitHub Release**: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/releases/tag/v0.3.0-alpha.23

## How to Update

### Step 1: Update Add-on
Wait for Docker build (5-10 minutes), then update to v0.3.0-alpha.23

### Step 2: Regenerate Entities
1. Open Broadlink Manager
2. Settings → Generate Entities
3. Wait for success message

### Step 3: Reload Home Assistant
Developer Tools → YAML → Reload All (or restart)

### Step 4: Test the New Behavior

**Test 1: Turn on from off**
1. Make sure fan is off
2. Click "Low" button
3. **Expected**: Fan turns on AND shows "on" ✅
4. **No need to click power button!**

**Test 2: Change speed while on**
1. Fan is on at low speed
2. Click "High" button
3. **Expected**: Fan changes to high, stays "on" ✅

**Test 3: Turn off**
1. Fan is on at any speed
2. Click "Off" button
3. **Expected**: Fan turns off AND shows "off" ✅
4. **No need to click power button again!**

## Now Your Fan Works Like SmartIR!

After this update, your Broadlink Manager fan will behave **exactly** like SmartIR fans:
- ✅ Click speed → Turns on at that speed
- ✅ Click off → Turns off
- ✅ No manual power button needed
- ✅ State always matches reality

## Summary of All Three Fixes

You've helped us find and fix **three related bugs**:

### v0.3.0-alpha.21: Entity Generation
- **Problem**: Custom speed names (lowMedium, mediumHigh) not recognized
- **Fix**: Added named speed mapping to fan entity generator

### v0.3.0-alpha.22: Helper Generation  
- **Problem**: Helper only had "off" option, missing speed numbers
- **Fix**: Added named speed mapping to helper generator
- **Result**: You could set speeds without errors

### v0.3.0-alpha.23: Auto-On Behavior
- **Problem**: Setting speed didn't turn fan "on"
- **Fix**: Added automatic state management to set_percentage
- **Result**: Fan now works like SmartIR (this fix!)

## Thank You!

Your testing and feedback have been incredibly valuable. You've helped make Broadlink Manager better for everyone who uses RF fans! 🎉

## Questions?

If you have any issues after updating:
1. Make sure you regenerated entities
2. Make sure you reloaded Home Assistant
3. Check the detailed docs at `docs/development/FAN_AUTO_ON_FIX.md`
4. Let us know if anything still doesn't work right

Enjoy your properly working fan! 😊
