import csv
from collections import defaultdict

# Test 8: Verify product selection correctness
print('🔍 TEST 8: Product Selection Verification')
print('='*60)

# Read input
with open('sample_products.csv', 'r', encoding='utf-8') as f:
    input_products = list(csv.DictReader(f))
    for p in input_products:
        p['price'] = float(p['price'])

# Read output
with open('deduplicated_products_v2.csv', 'r', encoding='utf-8') as f:
    output_products = list(csv.DictReader(f))
    for p in output_products:
        p['price'] = float(p['price'])

# Group input by SKU
sku_groups = defaultdict(list)
for p in input_products:
    sku_groups[p['sku']].append(p)

# Check a few examples
examples_to_check = ['SAM-S23-001', 'APP-IP15P-001', 'DELL-XPS13-001']

print('Sample verification:')
for sku in examples_to_check:
    if sku in sku_groups:
        input_group = sku_groups[sku]
        output_product = next((p for p in output_products if p['sku'] == sku), None)
        
        # Find the actual cheapest
        cheapest = min(input_group, key=lambda x: x['price'])
        
        print(f'\nSKU {sku}:')
        print(f'  Variants: {len(input_group)}')
        print(f'  Cheapest input: {cheapest["name"]} - ₪{cheapest["price"]:.0f}')
        if output_product:
            print(f'  Selected output: {output_product["name"]} - ₪{output_product["price"]:.0f}')
            if output_product['price'] == cheapest['price']:
                print('  ✓ CORRECT - Lowest price selected')
            else:
                print('  ✗ BUG - Wrong price!')
