# Unicode Fonts Usage Guide

## Overview
The bot uses Unicode mathematical alphanumeric symbols to provide styled text without relying on device-specific fonts.

## Available Styles

### 1. Bold
```python
uf.bold("Hello World")
# Output: 𝐇𝐞𝐥𝐥𝐨 𝐖𝐨𝐫𝐥𝐝
```

### 2. Italic
```python
uf.italic("Hello World")
# Output: 𝐻𝑒𝑙𝑙𝑜 𝑊𝑜𝑟𝑙𝑑
```

### 3. Bold Italic
```python
uf.bold_italic("Hello World")
# Output: 𝑯𝒆𝒍𝒍𝒐 𝑾𝒐𝒓𝒍𝒅
```

### 4. Monospace
```python
uf.monospace("Hello 123")
# Output: 𝙷𝚎𝚕𝚕𝚘 𝟷𝟸𝟹
```

### 5. Sans-serif
```python
uf.sans("Hello 123")
# Output: 𝖧𝖾𝗅𝗅𝗈 𝟣𝟤𝟥
```

### 6. Sans-serif Bold
```python
uf.sans_bold("Hello 123")
# Output: 𝗛𝗲𝗹𝗹𝗼 𝟭𝟮𝟯
```

### 7. Script/Cursive
```python
uf.script("Hello")
# Output: ℋℯ𝓁𝓁ℴ
```

### 8. Small Caps
```python
uf.small_caps("Hello")
# Output: ʜᴇʟʟᴏ
```

### 9. Double-Struck
```python
uf.double_struck("Hello 123")
# Output: ℍ𝕖𝕝𝕝𝕠 𝟙𝟚𝟛
```

### 10. Fraktur (Gothic)
```python
uf.fraktur("Hello")
# Output: ℌ𝔢𝔩𝔩𝔬
```

## Usage Guidelines

### DO ✅
- Use `bold()` for headers and emphasis
- Use `monospace()` for code, IDs, amounts
- Use `small_caps()` for special greetings
- Combine with emojis for better visual impact

### DON'T ❌
- Don't overuse - too many styles = messy
- Don't use for long paragraphs
- Don't use for critical information (some devices may not render)
- Don't expect all styles to work on all devices

## Best Practices

```python
# ✅ GOOD: Clear hierarchy
text = f"""
{uf.bold('TITLE')}
Regular text here
{uf.monospace('Code or ID: 12345')}
"""

# ❌ BAD: Too many styles
text = f"""
{uf.bold('TITLE')}
{uf.italic('Some text')}
{uf.script('More text')}
{uf.fraktur('Even more')}
"""
```

## Device Compatibility

| Style | iOS | Android | Desktop | Web |
|-------|-----|---------|---------|-----|
| Bold | ✅ | ✅ | ✅ | ✅ |
| Italic | ✅ | ✅ | ✅ | ✅ |
| Monospace | ✅ | ✅ | ✅ | ✅ |
| Sans | ✅ | ✅ | ✅ | ✅ |
| Small Caps | ✅ | ✅ | ✅ | ✅ |
| Script | ⚠️ | ⚠️ | ✅ | ✅ |
| Fraktur | ⚠️ | ⚠️ | ✅ | ✅ |
| Double-Struck | ⚠️ | ⚠️ | ✅ | ✅ |

✅ = Works on all versions
⚠️ = May not render on older versions

## Quick Reference

```python
from utils.unicode_fonts import UnicodeFonts as uf

# Apply style by name
uf.apply_style("text", "bold")

# Get all available styles
styles = uf.get_available_styles()
```
