"""
Product Deduplication Script - v2 (Simplified & More Effective)

This version uses a dual strategy:
1. Primary: Group by exact SKU match and keep lowest price
2. Secondary: For products WITHOUT SKU, use fuzzy name matching

This is more appropriate for e-commerce where SKU is the source of truth.
"""

import csv
from collections import defaultdict
from typing import List, Dict, Tuple
import difflib


class ProductDeduplicatorV2:
    def __init__(self, name_similarity_threshold: float = 0.80):
        """
        Args:
            name_similarity_threshold: Fuzzy match threshold for names (0-1)
        """
        self.similarity_threshold = name_similarity_threshold
        self.products = []
        
    def load_csv(self, filename: str) -> None:
        """Load products from CSV file."""
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['price'] = float(row['price'])
                self.products.append(row)
        print(f"✓ Loaded {len(self.products)} products")
    
    def get_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two product names (0-1)."""
        norm1 = name1.lower().strip()
        norm2 = name2.lower().strip()
        return difflib.SequenceMatcher(None, norm1, norm2).ratio()
    
    def deduplicate_by_sku(self) -> List[Dict]:
        """
        Group by SKU and keep the lowest price for each unique SKU.
        Prioritizes English product names.
        Returns deduplicated products.
        """
        sku_groups = defaultdict(list)
        
        # Group all products by SKU
        for product in self.products:
            sku_groups[product['sku']].append(product)
        
        deduplicated = []
        
        # For each SKU group
        for sku, group in sku_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Separate English and non-English names
                english_products = [p for p in group if self.is_english_name(p['name'])]
                non_english_products = [p for p in group if not self.is_english_name(p['name'])]
                
                # Strategy: Prefer English names. If English exists, pick lowest English price.
                # If no English names exist, pick lowest price overall.
                if english_products:
                    # Use English product with lowest price
                    selected = min(english_products, key=lambda x: x['price'])
                else:
                    # No English names available, use lowest price available
                    selected = min(group, key=lambda x: x['price'])
                
                deduplicated.append(selected)
        
        return deduplicated
    
    def deduplicate_by_name(self) -> List[Dict]:
        """
        For products WITHOUT proper SKU, use fuzzy name matching.
        This is a fallback for incomplete data.
        """
        products_with_no_sku = [p for p in self.products if not p['sku'] or p['sku'].strip() == '']
        
        if not products_with_no_sku:
            return []
        
        grouped = []
        used = set()
        
        for i, product1 in enumerate(products_with_no_sku):
            if i in used:
                continue
            
            group = [product1]
            used.add(i)
            
            for j, product2 in enumerate(products_with_no_sku[i+1:], start=i+1):
                if j in used:
                    continue
                
                similarity = self.get_similarity(product1['name'], product2['name'])
                if similarity >= self.similarity_threshold:
                    group.append(product2)
                    used.add(j)
            
            # Keep lowest price in group
            lowest = min(group, key=lambda x: x['price'])
            grouped.append(lowest)
        
        return grouped
    
    def is_english_name(self, name: str) -> bool:
        """Check if name starts with English/ASCII characters (no Hebrew/non-Latin at start)."""
        # If first character is ASCII (Latin letters/numbers), treat as English name
        if not name.strip():
            return False
        first_char = name.strip()[0]
        # Check if first character is ASCII letter/digit
        return ord(first_char) < 128 and (first_char.isalpha() or first_char.isdigit())
    
    def deduplicate(self) -> List[Dict]:
        """Main deduplication method."""
        # Primary: deduplicate by SKU (most reliable)
        by_sku = self.deduplicate_by_sku()
        
        # Secondary: deduplicate by name (for products without SKU)
        by_name = self.deduplicate_by_name()
        
        # Combine results
        all_deduplicated = by_sku + by_name
        
        return all_deduplicated
    
    def prefer_english_names(self, products: List[Dict]) -> List[Dict]:
        """For products with same SKU, prefer English names over Hebrew."""
        sku_groups = defaultdict(list)
        
        for product in products:
            sku_groups[product['sku']].append(product)
        
        deduplicated = []
        
        for sku, group in sku_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Find product with English name, preferring lower price
                english_products = [p for p in group if self.is_english_name(p['name'])]
                if english_products:
                    # Use the one with lowest price among English names
                    best = min(english_products, key=lambda x: x['price'])
                else:
                    # No English names, just use lowest price
                    best = min(group, key=lambda x: x['price'])
                deduplicated.append(best)
        
        return deduplicated
    
    def save_csv(self, filename: str, products: List[Dict]) -> None:
        """Save deduplicated products to CSV."""
        if not products:
            print("✗ No products to save")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'model', 'price', 'sku'])
            writer.writeheader()
            writer.writerows(products)
        
        print(f"✓ Saved {len(products)} deduplicated products to {filename}")
    
    def print_report(self, original_count: int, deduplicated_products: List[Dict]) -> None:
        """Print deduplication statistics."""
        deduplicated_count = len(deduplicated_products)
        duplicates_removed = original_count - deduplicated_count
        
        print("\n" + "="*60)
        print("DEDUPLICATION REPORT - v2")
        print("="*60)
        print(f"Original products:       {original_count}")
        print(f"Deduplicated products:   {deduplicated_count}")
        print(f"Duplicates removed:      {duplicates_removed}")
        if original_count > 0:
            print(f"Reduction:               {(duplicates_removed/original_count*100):.1f}%")
        print("="*60 + "\n")
    
    def print_summary(self, deduplicated: List[Dict]) -> None:
        """Print sample of results."""
        print("📋 Deduplicated Products (sorted by price):\n")
        
        # Group by SKU for display
        sku_groups = defaultdict(list)
        for product in deduplicated:
            sku_groups[product['sku']].append(product)
        
        counter = 1
        for sku, products in sorted(sku_groups.items()):
            # Show as different variants if multiple names exist
            product = products[0]  # They all have the same SKU
            print(f"{counter}. {product['name']}")
            print(f"   Model: {product['model']} | Price: ₪{product['price']:.2f} | SKU: {product['sku']}")
            if len(products) > 1:
                print(f"   ℹ️  Merged {len(products)} variants (removed duplicates)")
            print()
            counter += 1
            if counter > 8:  # Show first 8 only
                remaining = len(deduplicated) - counter + 1
                if remaining > 0:
                    print(f"... and {remaining} more products")
                break


def main():
    """Main execution."""
    input_file = "sample_products.csv"
    output_file = "deduplicated_products_v2.csv"
    
    print("🔄 Starting product deduplication (v2 - SKU-focused)...\n")
    
    # Initialize deduplicator
    dedup = ProductDeduplicatorV2(name_similarity_threshold=0.80)
    
    # Load products
    dedup.load_csv(input_file)
    original_count = len(dedup.products)
    
    # Deduplicate
    print("🔍 Deduplicating by SKU (primary) and fuzzy name match (secondary)...")
    deduplicated = dedup.deduplicate()
    
    # Save results
    dedup.save_csv(output_file, deduplicated)
    
    # Print report
    dedup.print_report(original_count, deduplicated)
    
    # Show sample
    dedup.print_summary(deduplicated)


if __name__ == "__main__":
    main()
