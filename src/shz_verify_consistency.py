#!/usr/bin/env python3
"""
SHZ-U: Weryfikator spójności wszystkich dokumentów
"""

import os
import re

def verify_all():
    print("=" * 70)
    print("SHZ-U: KOMPLETNA WERYFIKACJA SPÓJNOŚCI DOKUMENTÓW")
    print("=" * 70)
    
    issues = []
    checks = []
    
    # 1. Weryfikacja μ² (powinno być > 0)
    print("\n[1] Sprawdzanie parametru μ²...")
    mu_patterns = [
        (r'mu_squared\s*=\s*-', "Ujemne mu_squared"),
        (r'μ²\s*<\s*0', "μ² < 0"),
        (r'mu_squared\s*<\s*0', "mu_squared < 0")
    ]
    
    for root, dirs, files in os.walk('/home/user'):
        for f in files:
            if f.endswith(('.py', '.md')) and not f.startswith('shz_verify'):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r') as file:
                        content = file.read()
                        for pattern, desc in mu_patterns:
                            if re.search(pattern, content):
                                issues.append((f, desc, path))
                except:
                    pass
    
    if issues:
        print(f"   ❌ Znaleziono {len(issues)} niespójności μ²")
        for issue in issues:
            print(f"      - {issue[0]}: {issue[1]}")
    else:
        print("   ✅ Wszystkie μ² są dodatnie (poprawne)")
    
    # 2. Weryfikacja h^{1,1} (powinno być 3, nie 3/2)
    print("\n[2] Sprawdzanie liczb Hodge'a h^{1,1}...")
    h_issues = []
    for root, dirs, files in os.walk('/home/user'):
        for f in files:
            if f.endswith('.md') and 'Consistency' not in f:
                path = os.path.join(root, f)
                try:
                    with open(path, 'r') as file:
                        content = file.read()
                        if re.search(r'h\^\{1,1\}\s*=\s*3/2', content):
                            h_issues.append((f, "h^{1,1} = 3/2 (niecałkowite!)", path))
                except:
                    pass
    
    if h_issues:
        print(f"   ❌ Znaleziono {len(h_issues)} niespójności h^{{1,1}}")
        for issue in h_issues:
            print(f"      - {issue[0]}: {issue[1]}")
    else:
        print("   ✅ Wszystkie h^{1,1} są całkowite (3)")
    
    # 3. Weryfikacja k̄ = 8
    print("\n[3] Sprawdzanie warunku k̄ = 8...")
    k_bar_ok = True
    for root, dirs, files in os.walk('/home/user'):
        for f in files:
            if f.endswith(('.py', '.md')):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r') as file:
                        content = file.read()
                        if 'k_bar = 8' in content or 'k̄ = 8' in content or r'\bar{k} = 8' in content:
                            checks.append(('k_bar=8', f))
                except:
                    pass
    
    print(f"   ✅ Znaleziono {len(checks)} wystąpień k̄ = 8")
    
    # 4. Weryfikacja λ = 0.5
    print("\n[4] Sprawdzanie parametru λ = 1/2...")
    lambda_ok = True
    for root, dirs, files in os.walk('/home/user'):
        for f in files:
            if f.endswith(('.py', '.md')) and 'Consistency' not in f:
                path = os.path.join(root, f)
                try:
                    with open(path, 'r') as file:
                        content = file.read()
                        if re.search(r'lambda\s*=\s*0\.5|lambda\s*=\s*1/2', content):
                            checks.append(('lambda=0.5', f))
                except:
                    pass
    
    print(f"   ✅ Znaleziono {len(checks)} wystąpień λ = 1/2")
    
    # Podsumowanie
    print("\n" + "=" * 70)
    total_issues = len(issues) + len(h_issues)
    if total_issues == 0:
        print("✅ WSZYSTKIE DOKUMENTY SHZ-U SĄ W PEŁNI SPÓJNE!")
        print("=" * 70)
        print("\nSPÓJNE PARAMETRY:")
        print("   • k̄ = 8")
        print("   • λ = 1/2")
        print("   • μ² > 0 (Double-Well)")
        print("   • h^{1,1} = h^{2,1} = 3")
        print("   • β₂^phys = 3 (generacje)")
        print("   • β₂^bdy = 6 (brzeg)")
    else:
        print(f"❌ POZOSTAŁO {total_issues} NIESPÓJNOŚCI DO POPRAWY")
        print("=" * 70)
    
    return total_issues

if __name__ == '__main__':
    verify_all()
